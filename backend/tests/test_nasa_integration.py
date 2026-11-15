"""Mocked tests for DONKI fetching, normalization, classification, and gameplay."""

import unittest
from unittest.mock import patch

import requests
from fastapi import HTTPException

from app.models.schemas import ExecuteActionRequest, StartMissionRequest
from app.main import app
from app.routes import nasa as nasa_routes
from app.services import nasa_service, simulation
from app.services.event_manager import (
    maybe_trigger_nasa_scenario,
    maybe_trigger_nasa_sep_scenario,
)
from app.services.store import mission_store
from app.services.nasa_data_processor import process_nasa_response


SEP_RECORD = {
    "eventTime": "2026-11-12T10:20Z",
    "instruments": [{"displayName": "ACE"}, {"displayName": "SOHO"}],
    "linkedEvents": [{"activityID": "2026-11-12T09:00:00-CME-001"}],
    "link": "https://kauai.ccmc.gsfc.nasa.gov/DONKI/view/SEP/123",
    "submissionTime": "2026-11-12T11:00Z",
    "versionId": 1,
}

FLARE_RECORD = {
    "flrID": "2026-11-11T12:00:00-FLR-001",
    "beginTime": "2026-11-11T12:00Z",
    "peakTime": "2026-11-11T12:10Z",
    "endTime": "2026-11-11T12:20Z",
    "classType": "M1.2",
    "sourceLocation": "N15E20",
    "activeRegionNum": 12345,
    "linkedEvents": None,
    "instruments": [{"displayName": "GOES-P: EXIS 1.0-8.0"}],
    "note": "NASA DONKI flare note",
    "link": "https://kauai.ccmc.gsfc.nasa.gov/DONKI/view/FLR/456",
    "submissionTime": "2026-11-11T13:00Z",
    "versionId": 1,
}


class MockResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            response = type("Response", (), {"status_code": self.status_code})()
            raise requests.HTTPError(response=response)

    def json(self):
        return self.payload


class TestNASAIntegration(unittest.TestCase):
    def setUp(self):
        mission_store.clear()
        nasa_service.clear_nasa_cache()

    def tearDown(self):
        nasa_service.clear_nasa_cache()
        mission_store.clear()

    def _api_responses(self, sep_payload, flare_payload, sep_status=200, flare_status=200):
        def fake_get(url, **kwargs):
            self.assertIn("startDate", kwargs["params"])
            self.assertIn("endDate", kwargs["params"])
            self.assertEqual(kwargs["timeout"], nasa_service.NASA_REQUEST_TIMEOUT)
            self.assertIn(
                url,
                (*nasa_service.DONKI_ENDPOINTS.values(), *nasa_service.CCMC_FALLBACK_ENDPOINTS.values()),
            )
            if url in nasa_service.DONKI_ENDPOINTS.values():
                self.assertTrue(kwargs["params"].get("api_key"))
            else:
                self.assertNotIn("api_key", kwargs["params"])
            if url in (
                nasa_service.DONKI_ENDPOINTS["SEP"],
                nasa_service.CCMC_FALLBACK_ENDPOINTS["SEP"],
            ):
                return MockResponse(sep_payload, sep_status)
            return MockResponse(flare_payload, flare_status)

        return fake_get

    def test_successful_fetch_normalizes_sep_and_flare_and_caches(self):
        mocked_get = self._api_responses([SEP_RECORD], [FLARE_RECORD])
        with patch.object(nasa_service.requests, "get", side_effect=mocked_get) as request:
            result = nasa_service.get_nasa_snapshot(force_refresh=True)
            cached = nasa_service.get_nasa_snapshot()

        self.assertEqual(result["connection_status"], "active")
        self.assertEqual(result["event_count"], 2)
        self.assertEqual(result, cached)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(result["events"][0]["event_type"], "SEP")
        self.assertEqual(result["events"][0]["category"], "INSUFFICIENT DATA FOR RISK ASSESSMENT")
        self.assertEqual(result["events"][0]["linked_events"], SEP_RECORD["linkedEvents"])
        self.assertEqual(result["events"][1]["class_type"], "M1.2")
        self.assertEqual(result["events"][1]["category"], "INFORMATIONAL")
        self.assertNotIn("api_key", result)
        self.assertTrue(result["events"][0]["retrieved_at"])

    def test_empty_responses_are_successful_and_do_not_create_events(self):
        with patch.object(
            nasa_service.requests, "get", side_effect=self._api_responses([], [])
        ):
            result = nasa_service.get_nasa_snapshot(force_refresh=True)

        self.assertEqual(result["connection_status"], "active")
        self.assertEqual(result["event_count"], 0)
        self.assertEqual(result["events"], [])

    def test_unauthorized_request_and_rate_limit_are_reported(self):
        for status_code, expected in ((403, "rejected"), (429, "rate limit")):
            nasa_service.clear_nasa_cache()
            with patch.object(
                nasa_service.requests,
                "get",
                side_effect=self._api_responses([], [], status_code, status_code),
            ):
                snapshot = nasa_service.get_nasa_snapshot(force_refresh=True)
                self.assertEqual(snapshot["connection_status"], "unavailable")
                with self.assertRaises(nasa_service.NASAServiceError) as raised:
                    nasa_service.get_nasa_events()
            self.assertIn(expected, str(raised.exception))

    def test_connection_timeout_and_server_error_status(self):
        with patch.object(
            nasa_service.requests,
            "get",
            side_effect=requests.Timeout(),
        ):
            timeout_snapshot = nasa_service.get_nasa_snapshot(force_refresh=True)
        self.assertEqual(timeout_snapshot["connection_status"], "unavailable")
        self.assertIn("timed out", timeout_snapshot["endpoint_status"]["SEP"]["error"])

        nasa_service.clear_nasa_cache()
        with patch.object(
            nasa_service.requests,
            "get",
            side_effect=self._api_responses([SEP_RECORD], [], 200, 500),
        ):
            partial_snapshot = nasa_service.get_nasa_snapshot(force_refresh=True)
        self.assertEqual(partial_snapshot["connection_status"], "partial")
        self.assertEqual(partial_snapshot["event_count"], 1)
        self.assertIn("server", partial_snapshot["endpoint_status"]["FLR"]["error"])

    def test_malformed_payload_and_missing_optional_event_fields(self):
        with patch.object(
            nasa_service.requests,
            "get",
            side_effect=self._api_responses({"unexpected": "object"}, []),
        ):
            malformed = nasa_service.get_nasa_snapshot(force_refresh=True)
        self.assertEqual(malformed["connection_status"], "partial")
        self.assertIn("unexpected format", malformed["endpoint_status"]["SEP"]["error"])

        processed = process_nasa_response("SEP", [{"unexpectedField": "kept"}])
        event = processed[0]
        self.assertIsNone(event["event_id"])
        self.assertIsNone(event["event_time"])
        self.assertEqual(event["instruments"], [])
        self.assertEqual(event["linked_events"], [])
        self.assertEqual(event["original"], {"unexpectedField": "kept"})
        self.assertEqual(event["category"], "INSUFFICIENT DATA FOR RISK ASSESSMENT")

        invalid_time = process_nasa_response("FLR", [{"beginTime": 123}])[0]
        self.assertIsNone(invalid_time["event_time"])
        self.assertEqual(
            invalid_time["category"],
            "INSUFFICIENT DATA FOR RISK ASSESSMENT",
        )

    def test_sep_and_flare_processing_preserves_source_fields(self):
        sep_event = process_nasa_response("SEP", [SEP_RECORD])[0]
        flare_event = process_nasa_response("FLR", [FLARE_RECORD])[0]
        revised_sep_record = {**SEP_RECORD, "versionId": 2}
        revised_sep_event = process_nasa_response("SEP", [revised_sep_record])[0]
        self.assertEqual(sep_event["event_time"], SEP_RECORD["eventTime"])
        self.assertEqual(sep_event["source_url"], SEP_RECORD["link"])
        self.assertEqual(sep_event["original"], SEP_RECORD)
        self.assertEqual(flare_event["event_id"], FLARE_RECORD["flrID"])
        self.assertEqual(flare_event["event_time"], FLARE_RECORD["beginTime"])
        self.assertEqual(flare_event["peak_time"], FLARE_RECORD["peakTime"])
        self.assertEqual(flare_event["notes"], FLARE_RECORD["note"])
        self.assertEqual(flare_event["original"], FLARE_RECORD)
        self.assertEqual(
            sep_event["deduplication_key"],
            revised_sep_event["deduplication_key"],
        )

    def test_duplicate_sep_does_not_create_multiple_mission_scenarios(self):
        state = simulation.create_mission(
            StartMissionRequest(enable_random_events=False, duration=5)
        )
        event = process_nasa_response("SEP", [SEP_RECORD])[0]
        first = maybe_trigger_nasa_sep_scenario(state, [event])
        self.assertIsNotNone(first)
        self.assertEqual(first.label, "REAL NASA DATA")
        self.assertEqual(first.severity, "low")

        state.active_events = []
        second = maybe_trigger_nasa_sep_scenario(state, [event])
        self.assertIsNone(second)
        self.assertEqual(len(state.seen_nasa_event_ids), 1)

    def test_solar_flare_creates_monitoring_alert_without_radiation_claim(self):
        state = simulation.create_mission(
            StartMissionRequest(enable_random_events=False, duration=5)
        )
        flare = process_nasa_response("FLR", [FLARE_RECORD])[0]
        alert = maybe_trigger_nasa_scenario(state, [flare])

        self.assertIsNotNone(alert)
        self.assertEqual(alert.source_event_type, "FLR")
        self.assertEqual(alert.source_event_time, FLARE_RECORD["beginTime"])
        self.assertEqual(alert.name, "Solar Activity Monitoring Alert")
        self.assertIn("does not measure radiation", alert.educational_explanation)
        self.assertIn("does not call for a radiation emergency", alert.mission_situation)
        self.assertEqual(len(alert.decisions), 3)
        self.assertIsNone(maybe_trigger_nasa_scenario(state, [flare]))

    def test_all_nasa_decisions_change_simulated_game_state(self):
        choices = (
            ("SEP", "nasa_activate_shelter"),
            ("SEP", "nasa_pause_outdoor_monitor"),
            ("SEP", "nasa_continue_operations"),
            ("FLR", "nasa_monitor_solar_conditions"),
            ("FLR", "nasa_pause_outdoor_observations"),
            ("FLR", "nasa_continue_scheduled_research"),
        )
        fixtures = {"SEP": SEP_RECORD, "FLR": FLARE_RECORD}

        for event_type, choice_id in choices:
            with self.subTest(event_type=event_type, choice_id=choice_id):
                state = simulation.create_mission(
                    StartMissionRequest(enable_random_events=False, duration=5)
                )
                state.resources.power = 60.0
                state.resources.shield = 40.0
                state.crew_status.radiation_exposure = 20.0
                state.science_points = 10
                nasa_event = process_nasa_response(
                    event_type, [fixtures[event_type]]
                )[0]
                alert = maybe_trigger_nasa_scenario(state, [nasa_event])
                self.assertIsNotNone(alert)
                state.active_events = [alert]
                mission_store.save(state)
                before = {
                    "power": state.resources.power,
                    "shield": state.resources.shield,
                    "exposure": state.crew_status.radiation_exposure,
                    "science": state.science_points,
                }

                result = simulation.execute_player_action(
                    state.mission_id,
                    ExecuteActionRequest(
                        action_id="resolve_event",
                        event_id=alert.event_id,
                        choice_id=choice_id,
                    ),
                )
                updated = result.game_state
                after = {
                    "power": updated.resources.power,
                    "shield": updated.resources.shield,
                    "exposure": updated.crew_status.radiation_exposure,
                    "science": updated.science_points,
                }

                self.assertNotEqual(before, after)
                self.assertIn("SIMULATED GAME CONSEQUENCE", result.feedback_message)
                self.assertEqual(updated.active_events, [])
                if event_type == "FLR":
                    self.assertEqual(after["exposure"], before["exposure"])
                    self.assertEqual(after["shield"], before["shield"])

    def test_simulation_uses_cached_flares_and_sep_records_for_alerts(self):
        state = simulation.create_mission(
            StartMissionRequest(enable_random_events=False, duration=5)
        )
        flare = process_nasa_response("FLR", [FLARE_RECORD])[0]
        with patch.object(simulation, "get_cached_nasa_events", return_value=[flare]):
            advanced = simulation.advance_mission_day(state.mission_id)

        self.assertEqual(len(advanced.game_state.active_events), 1)
        alert = advanced.game_state.active_events[0]
        self.assertEqual(alert.source_event_type, "FLR")
        self.assertEqual(alert.source_event_id, FLARE_RECORD["flrID"])

    def test_shelter_decision_uses_simulation_mechanics_for_nasa_scenario(self):
        state = simulation.create_mission(
            StartMissionRequest(enable_random_events=False, duration=5)
        )
        state.crew_status.radiation_exposure = 20.0
        mission_store.save(state)
        event = process_nasa_response("SEP", [SEP_RECORD])[0]
        with patch.object(simulation, "get_cached_nasa_events", return_value=[event]):
            advanced = simulation.advance_mission_day(state.mission_id)

        game_state = advanced.game_state
        nasa_event = game_state.active_events[0]
        self.assertEqual(nasa_event.source_type, "NASA")
        power_before = game_state.resources.power
        shield_before = game_state.resources.shield
        exposure_before = game_state.crew_status.radiation_exposure

        decision = simulation.execute_player_action(
            game_state.mission_id,
            ExecuteActionRequest(
                action_id="resolve_event",
                event_id=nasa_event.event_id,
                choice_id="nasa_activate_shelter",
            ),
        )
        updated = decision.game_state
        self.assertEqual(updated.resources.power, power_before - 10)
        self.assertGreater(updated.resources.shield, shield_before)
        self.assertLess(updated.crew_status.radiation_exposure, exposure_before)
        self.assertTrue(updated.subsystems.radiation_shelter_active)
        self.assertIn("SIMULATED GAME CONSEQUENCE", decision.feedback_message)

    def test_simulation_remains_playable_when_nasa_unavailable(self):
        state = simulation.create_mission(
            StartMissionRequest(enable_random_events=False, duration=5)
        )
        with patch.object(simulation, "get_cached_nasa_events", return_value=[]):
            advanced = simulation.advance_mission_day(state.mission_id)

        self.assertEqual(advanced.game_state.current_day, 2)
        self.assertEqual(advanced.game_state.active_events, [])
        self.assertEqual(advanced.game_state.mission_status, "In Progress")

    def test_nasa_routes_are_registered_and_status_has_no_credentials(self):
        expected_paths = {
            "/api/nasa/status",
            "/api/nasa/events",
            "/api/nasa/solar-events",
            "/api/nasa/sep",
            "/api/nasa/flares",
            "/api/nasa/last-updated",
        }
        registered_paths = set(app.openapi()["paths"])
        self.assertTrue(expected_paths.issubset(registered_paths))

        with patch.object(
            nasa_routes.nasa_service,
            "check_nasa_connection",
            return_value={
                "connection_status": "active",
                "message": "NASA SPACE WEATHER CONNECTION ACTIVE",
                "last_updated": "2026-11-14T00:00:00+00:00",
                "retrieval_timestamp": "2026-11-14T00:00:00+00:00",
                "event_count": 0,
                "start_date": "2026-11-08",
                "end_date": "2026-11-14",
                "endpoint_status": {},
            },
        ):
            status = nasa_routes.nasa_status(refresh=False)
        self.assertEqual(status["message"], "NASA SPACE WEATHER CONNECTION ACTIVE")
        self.assertNotIn("api_key", status)

    def test_event_routes_return_mocked_normalized_records_and_last_updated(self):
        mocked_get = self._api_responses([SEP_RECORD], [FLARE_RECORD])
        with patch.object(nasa_service.requests, "get", side_effect=mocked_get) as request:
            all_events = nasa_routes.solar_events(refresh=False)
            sep_events = nasa_routes.sep_events(refresh=False)
            flare_events = nasa_routes.flare_events(refresh=False)
            last_updated = nasa_routes.nasa_last_updated()

        self.assertEqual(all_events["event_count"], 2)
        self.assertEqual(sep_events["events"][0]["event_type"], "SEP")
        self.assertEqual(flare_events["events"][0]["event_type"], "FLR")
        self.assertIsNotNone(last_updated["last_updated"])
        self.assertEqual(request.call_count, 2)

    def test_nasa_data_route_returns_a_clear_503_when_unavailable(self):
        with patch.object(
            nasa_routes.nasa_service,
            "get_solar_energetic_particles",
            side_effect=nasa_service.NASAServiceError(
                "NASA API rate limit reached. Try again later."
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                nasa_routes.sep_events(refresh=False)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("rate limit", raised.exception.detail["message"])


if __name__ == "__main__":
    unittest.main()
