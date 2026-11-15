import copy
import unittest
from unittest.mock import patch

from app.models.schemas import ExecuteActionRequest, StartMissionRequest
from app.services import nasa_training_service
from app.services.event_manager import maybe_trigger_nasa_scenario
from app.services.simulation import advance_mission_day, create_mission, execute_player_action
from app.services.store import mission_store


class TestNasaTrainingEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.training_events, cls.seen_event_keys = (
            nasa_training_service.build_nasa_training_events("training-fixture", 1)
        )

    def setUp(self):
        mission_store.clear()

    def _create_mission(self):
        with patch(
            "app.services.simulation.build_nasa_training_events",
            return_value=(
                copy.deepcopy(self.training_events),
                list(self.seen_event_keys),
            ),
        ):
            return create_mission(
                StartMissionRequest(
                    duration=5,
                    deterministic=True,
                    enable_random_events=False,
                )
            )

    def _resolve(self, state, category, choice_id):
        event = next(
            event for event in state.nasa_training_events if event.category == category
        )
        return execute_player_action(
            state.mission_id,
            ExecuteActionRequest(
                action_id="resolve_nasa_training_event",
                event_id=event.event_id,
                choice_id=choice_id,
            ),
        )

    def test_creates_three_optional_categories_with_clear_labels(self):
        state = self._create_mission()
        self.assertEqual(
            {event.category for event in state.nasa_training_events},
            {
                "south_polar_environment",
                "space_weather_preparedness",
                "earth_moon_communication",
            },
        )
        for event in state.nasa_training_events:
            self.assertEqual(event.label, "SIMULATED TRAINING EVENT")
            self.assertEqual(event.consequence_label, "SIMULATED GAME CONSEQUENCE")
            self.assertEqual(len(event.decisions), 3)
            self.assertEqual(len(event.scientific_limitations), 4 if event.category != "south_polar_environment" else 3)

    def test_context_uses_available_processed_records_and_original_dates(self):
        contexts = {
            event.category: event.data_context for event in self.training_events
        }
        self.assertTrue(contexts["south_polar_environment"])
        self.assertTrue(contexts["space_weather_preparedness"])
        self.assertTrue(contexts["earth_moon_communication"])
        labels = {
            point.data_label
            for points in contexts.values()
            for point in points
        }
        self.assertIn("REAL NASA DATA", labels)
        self.assertIn("COMPUTED EPHEMERIS", labels)
        self.assertIn("DERIVED VALUE", labels)
        self.assertTrue(
            any(
                point.dataset_id == "ace_epam"
                and point.date_or_coverage
                and "2020" in point.date_or_coverage
                and "not a lunar-surface" in (point.note or "")
                for point in contexts["space_weather_preparedness"]
            )
        )
        self.assertTrue(
            any(
                point.dataset_id == "stereo_impact"
                and point.date_or_coverage
                and "2012" in point.date_or_coverage
                for point in contexts["space_weather_preparedness"]
            )
        )
        two_way = next(
            point
            for point in contexts["earth_moon_communication"]
            if point.measurement == "Two-way vacuum light time"
        )
        self.assertEqual(two_way.data_label, "DERIVED VALUE")

    def test_missing_datasets_keep_training_events_playable_without_fake_data(self):
        with (
            patch.object(nasa_training_service, "_dataset_snapshot", return_value=None),
            patch.object(nasa_training_service, "_record_page", return_value=[]),
            patch.object(nasa_training_service, "get_cached_nasa_events", return_value=[]),
        ):
            events, seen = nasa_training_service.build_nasa_training_events(
                "offline-mission", 1
            )
        self.assertEqual(len(events), 3)
        self.assertEqual(seen, [])
        self.assertTrue(all(not event.data_context for event in events))
        self.assertTrue(
            all(event.data_availability == "unavailable" for event in events)
        )
        self.assertTrue(all(event.data_unavailable_note for event in events))

    def test_partial_dataset_failure_is_named_and_does_not_hide_available_context(self):
        stereo_point = self.training_events[1].data_context[-1]
        with (
            patch.object(nasa_training_service, "_diviner_context", return_value=[]),
            patch.object(nasa_training_service, "_lola_context", return_value=[]),
            patch.object(nasa_training_service, "_ace_context", return_value=[]),
            patch.object(
                nasa_training_service,
                "_stereo_context",
                return_value=[stereo_point],
            ),
            patch.object(nasa_training_service, "_horizons_context", return_value=[]),
            patch.object(nasa_training_service, "get_cached_nasa_events", return_value=[]),
        ):
            events, _ = nasa_training_service.build_nasa_training_events(
                "partial-mission", 1
            )
        space_weather = next(
            event for event in events if event.category == "space_weather_preparedness"
        )
        self.assertEqual(space_weather.data_availability, "partial")
        self.assertEqual(len(space_weather.data_context), 1)
        self.assertIn("ACE EPAM", space_weather.data_unavailable_note or "")
        self.assertIn("STEREO-A", space_weather.data_unavailable_note or "")

    def test_mission_progression_works_when_all_dataset_services_fail(self):
        with (
            patch.object(nasa_training_service, "_dataset_snapshot", return_value=None),
            patch.object(nasa_training_service, "_record_page", return_value=[]),
            patch.object(nasa_training_service, "get_cached_nasa_events", return_value=[]),
        ):
            state = create_mission(
                StartMissionRequest(
                    duration=5,
                    deterministic=True,
                    enable_random_events=False,
                )
            )
            advanced = advance_mission_day(state.mission_id)
        self.assertEqual(advanced.game_state.current_day, 2)
        self.assertEqual(advanced.game_state.mission_status, "In Progress")
        self.assertTrue(
            all(not event.data_context for event in advanced.game_state.nasa_training_events)
        )

    def test_all_nine_choices_resolve_and_report_simulated_changes(self):
        choices = (
            ("south_polar_environment", "environment_power_plan"),
            ("south_polar_environment", "environment_terrain_review"),
            ("south_polar_environment", "environment_keep_plan"),
            ("space_weather_preparedness", "space_weather_shelter"),
            ("space_weather_preparedness", "space_weather_pause_activity"),
            ("space_weather_preparedness", "space_weather_monitor"),
            ("earth_moon_communication", "communication_wait"),
            ("earth_moon_communication", "communication_autonomous"),
            ("earth_moon_communication", "communication_schedule"),
        )
        for category, choice_id in choices:
            with self.subTest(category=category, choice_id=choice_id):
                state = self._create_mission()
                result = self._resolve(state, category, choice_id)
                updated = result.game_state
                resolved = next(
                    event
                    for event in updated.nasa_training_events
                    if event.category == category
                )
                self.assertTrue(resolved.resolved)
                self.assertEqual(resolved.selected_choice_id, choice_id)
                self.assertIn("SIMULATED GAME CONSEQUENCE", result.feedback_message)
                self.assertEqual(updated.active_events, [])
                for resource_name in ("power", "water", "oxygen", "food", "shield"):
                    value = getattr(updated.resources, resource_name)
                    self.assertGreaterEqual(value, 0)
                    self.assertLessEqual(value, 100)

    def test_shelter_outcome_uses_existing_clamped_game_mechanics(self):
        state = self._create_mission()
        state.resources.power = 10
        state.resources.shield = 100
        state.crew_status.radiation_exposure = 0
        mission_store.save(state)
        result = self._resolve(
            state, "space_weather_preparedness", "space_weather_shelter"
        )
        updated = result.game_state
        self.assertEqual(updated.resources.power, 0)
        self.assertEqual(updated.resources.shield, 100)
        self.assertEqual(updated.crew_status.radiation_exposure, 0)
        self.assertTrue(updated.subsystems.radiation_shelter_active)

    def test_insufficient_resources_and_duplicate_resolution_are_rejected(self):
        state = self._create_mission()
        state.resources.power = 9
        mission_store.save(state)
        event = next(
            event
            for event in state.nasa_training_events
            if event.category == "space_weather_preparedness"
        )
        with self.assertRaisesRegex(ValueError, "requires 10 simulated units"):
            execute_player_action(
                state.mission_id,
                ExecuteActionRequest(
                    action_id="resolve_nasa_training_event",
                    event_id=event.event_id,
                    choice_id="space_weather_shelter",
                ),
            )
        self._resolve(
            state, "space_weather_preparedness", "space_weather_monitor"
        )
        with self.assertRaisesRegex(ValueError, "already resolved"):
            execute_player_action(
                state.mission_id,
                ExecuteActionRequest(
                    action_id="resolve_nasa_training_event",
                    event_id=event.event_id,
                    choice_id="space_weather_shelter",
                ),
            )

    def test_cached_donki_sep_is_context_and_not_retriggered(self):
        sep_event = {
            "event_type": "SEP",
            "event_id": "SEP-2025-01",
            "event_time": "2025-01-02T03:04:05Z",
            "deduplication_key": "sep:2025-01-02T03:04:05Z",
            "source_url": "https://example.nasa.gov/sep",
        }
        with patch.object(
            nasa_training_service,
            "get_cached_nasa_events",
            return_value=[sep_event],
        ):
            events, seen = nasa_training_service.build_nasa_training_events(
                "sep-mission", 1
            )
        self.assertEqual(seen, [sep_event["deduplication_key"]])
        space_weather = next(
            event for event in events if event.category == "space_weather_preparedness"
        )
        self.assertTrue(
            any(point.dataset_id == "donki_sep" for point in space_weather.data_context)
        )
        with patch(
            "app.services.simulation.build_nasa_training_events",
            return_value=(events, seen),
        ):
            state = create_mission(
                StartMissionRequest(duration=5, enable_random_events=False)
            )
        self.assertIsNone(maybe_trigger_nasa_scenario(state, [sep_event]))
        self.assertEqual(state.active_events, [])

    def test_day_progression_does_not_apply_or_gate_optional_training_events(self):
        state = self._create_mission()
        original_ids = [event.event_id for event in state.nasa_training_events]
        result = advance_mission_day(state.mission_id)
        self.assertEqual(result.game_state.current_day, 2)
        self.assertEqual(result.game_state.active_events, [])
        self.assertEqual(
            [event.event_id for event in result.game_state.nasa_training_events],
            original_ids,
        )
        self.assertTrue(
            all(not event.resolved for event in result.game_state.nasa_training_events)
        )

    def test_decisions_and_events_are_retained_for_the_final_debrief(self):
        state = self._create_mission()
        action = execute_player_action(
            state.mission_id,
            ExecuteActionRequest(action_id="activate_oxygen_recycling"),
        )
        self.assertEqual(len(action.game_state.mission_decisions), 1)
        self.assertEqual(
            action.game_state.mission_decisions[0].decision_type, "outpost_action"
        )

        state.enable_random_events = True
        mission_store.save(state)
        with patch(
            "app.services.simulation.get_cached_nasa_events", return_value=[]
        ):
            advanced = advance_mission_day(state.mission_id)
        event_state = advanced.game_state
        self.assertTrue(event_state.mission_events)
        self.assertEqual(event_state.mission_events[-1].title, "Solar Panel Dust Accumulation")
        event = event_state.active_events[0]
        resolved = execute_player_action(
            state.mission_id,
            ExecuteActionRequest(
                action_id="resolve_event",
                event_id=event.event_id,
                choice_id=event.decisions[0].choice_id,
            ),
        )
        history = resolved.game_state.mission_decisions
        self.assertEqual(history[-1].decision_type, "mission_event")
        self.assertEqual(history[-1].subject, event.name)
        self.assertEqual(history[-1].consequence_label, "SIMULATED GAME CONSEQUENCE")

        with patch(
            "app.services.simulation.build_nasa_training_events",
            return_value=([], []),
        ):
            new_mission = create_mission(
                StartMissionRequest(duration=5, enable_random_events=False)
            )
        self.assertEqual(new_mission.mission_decisions, [])
        self.assertEqual(new_mission.mission_events, [])


if __name__ == "__main__":
    unittest.main()
