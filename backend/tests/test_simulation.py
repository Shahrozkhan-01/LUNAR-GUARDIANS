"""
LUNAR GUARDIANS — Comprehensive Automated Backend Test Suite.

Covers all 14 required simulation & API test scenarios plus non-negativity
invariants and deterministic reproducibility.
"""

import unittest
from typing import Any, Coroutine, Dict, Tuple
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.schemas import (
    ExecuteActionRequest,
    PowerUpdateRequest,
    StartMissionRequest,
)
from app.routes import game as game_routes
from app.services.store import mission_store


def _run_sync_coro(coro: Coroutine[Any, Any, Any]) -> Any:
    """Execute a non-yielding async FastAPI route handler without opening OS sockets."""
    try:
        coro.send(None)
    except StopIteration as stop:
        return stop.value
    finally:
        coro.close()
    raise RuntimeError("Coroutine yielded unexpectedly")


def call_api(method: str, path: str, body: Dict[str, Any] | None = None) -> Tuple[int, Dict[str, Any]]:
    """Dispatch request through Pydantic schemas and FastAPI route handlers with HTTP status mapping."""
    parts = [p for p in path.strip("/").split("/") if p]
    try:
        # POST /api/game/start
        if method == "POST" and parts == ["api", "game", "start"]:
            req = StartMissionRequest(**(body or {}))
            res = _run_sync_coro(game_routes.start_mission(req))
            return 201, res.model_dump()

        # GET /api/game/{mission_id}
        if method == "GET" and len(parts) == 3 and parts[:2] == ["api", "game"]:
            res = _run_sync_coro(game_routes.get_mission_state(parts[2]))
            return 200, res.model_dump()

        # POST /api/game/{mission_id}/action
        if method == "POST" and len(parts) == 4 and parts[:2] == ["api", "game"] and parts[3] == "action":
            req = ExecuteActionRequest(**(body or {}))
            res = _run_sync_coro(game_routes.run_player_action(parts[2], req))
            return 200, res.model_dump()

        # POST /api/game/{mission_id}/advance
        if method == "POST" and len(parts) == 4 and parts[:2] == ["api", "game"] and parts[3] == "advance":
            res = _run_sync_coro(game_routes.advance_day(parts[2]))
            return 200, res.model_dump()

        # GET /api/game/{mission_id}/events
        if method == "GET" and len(parts) == 4 and parts[:2] == ["api", "game"] and parts[3] == "events":
            res = _run_sync_coro(game_routes.get_mission_events(parts[2]))
            return 200, res.model_dump()

        # POST /api/game/{mission_id}/power
        if method == "POST" and len(parts) == 4 and parts[:2] == ["api", "game"] and parts[3] == "power":
            req = PowerUpdateRequest(**(body or {}))
            res = _run_sync_coro(game_routes.set_power_allocation(parts[2], req))
            return 200, res.model_dump()

        return 404, {"detail": "Route not found"}
    except HTTPException as http_exc:
        return http_exc.status_code, {"detail": http_exc.detail}
    except ValidationError as val_err:
        return 422, {"detail": val_err.errors()}


class TestLunarGuardiansSimulation(unittest.TestCase):
    def setUp(self) -> None:
        mission_store.clear()

    def _start_mission(self, **overrides: Any) -> Dict[str, Any]:
        payload = {
            "destination": "lunar-outpost",
            "difficulty": "commander",
            "crew_size": 4,
            "duration": 5,
            "deterministic": True,
            "enable_random_events": False,
        }
        payload.update(overrides)
        status_code, data = call_api("POST", "/api/game/start", payload)
        self.assertEqual(status_code, 201)
        return data

    def _assert_resources_bounded(self, resources: Dict[str, Any]) -> None:
        for key in ("oxygen", "water", "power", "food", "shield"):
            val = resources[key]
            self.assertGreaterEqual(val, 0.0, f"{key} became negative: {val}")
            self.assertLessEqual(val, 100.0, f"{key} exceeded 100: {val}")

    # 1. Mission Initialization
    def test_01_mission_initialization_and_get_endpoint(self) -> None:
        state = self._start_mission()
        self.assertTrue(state["mission_id"].startswith("lg-"))
        self.assertEqual(state["current_day"], 1)
        self.assertEqual(state["mission_status"], "In Progress")
        self.assertEqual(state["resources"]["unit_label"], "SIMULATED GAME UNITS")
        self.assertEqual(state["resources"]["oxygen"], 100.0)
        self.assertEqual(state["resources"]["water"], 100.0)
        self.assertEqual(state["resources"]["power"], 100.0)
        self.assertEqual(state["resources"]["food"], 100.0)
        self.assertEqual(state["resources"]["shield"], 50.0)

        code, fetched = call_api("GET", f"/api/game/{state['mission_id']}")
        self.assertEqual(code, 200)
        self.assertEqual(fetched["mission_id"], state["mission_id"])

        code_404, _ = call_api("GET", "/api/game/nonexistent-id")
        self.assertEqual(code_404, 404)

    # 2. Different Crew Sizes
    def test_02_different_crew_sizes_affect_consumption(self) -> None:
        m2 = self._start_mission(crew_size=2)
        m6 = self._start_mission(crew_size=6)

        _, adv2 = call_api("POST", f"/api/game/{m2['mission_id']}/advance")
        _, adv6 = call_api("POST", f"/api/game/{m6['mission_id']}/advance")

        r2 = adv2["game_state"]["resources"]
        r6 = adv6["game_state"]["resources"]

        self.assertEqual(len(adv2["game_state"]["crew_status"]["members"]), 2)
        self.assertEqual(len(adv6["game_state"]["crew_status"]["members"]), 6)
        self.assertGreater(r2["oxygen"], r6["oxygen"])
        self.assertGreater(r2["water"], r6["water"])
        self.assertGreater(r2["food"], r6["food"])

    # 3. Different Difficulty Settings
    def test_03_difficulty_settings(self) -> None:
        exp = self._start_mission(difficulty="explorer")
        cmd = self._start_mission(difficulty="commander")
        xpt = self._start_mission(difficulty="expert")

        self.assertEqual(exp["resources"]["shield"], 65.0)
        self.assertEqual(cmd["resources"]["shield"], 50.0)
        self.assertEqual(xpt["resources"]["shield"], 40.0)
        self.assertEqual(xpt["resources"]["oxygen"], 85.0)
        self.assertEqual(exp["science_points"], 10)

    # 4. Oxygen Consumption & Recycling
    def test_04_oxygen_consumption_and_recycling(self) -> None:
        powered = self._start_mission(crew_size=6)
        unpowered = self._start_mission(crew_size=6)

        call_api(
            "POST",
            f"/api/game/{unpowered['mission_id']}/power",
            {
                "life_support": 0.0,
                "radiation_shelter": 15.0,
                "greenhouse": 15.0,
                "communication": 10.0,
                "scientific_research": 10.0,
            },
        )

        _, res_powered = call_api("POST", f"/api/game/{powered['mission_id']}/advance")
        _, res_unpowered = call_api("POST", f"/api/game/{unpowered['mission_id']}/advance")

        self.assertGreater(
            res_powered["game_state"]["resources"]["oxygen"],
            res_unpowered["game_state"]["resources"]["oxygen"],
        )

    # 5. Water Consumption & Recovery
    def test_05_water_consumption_and_recovery_action(self) -> None:
        state = self._start_mission(difficulty="expert", crew_size=6)
        _, adv = call_api("POST", f"/api/game/{state['mission_id']}/advance")
        water_before = adv["game_state"]["resources"]["water"]

        code, act = call_api(
            "POST",
            f"/api/game/{state['mission_id']}/action",
            {"action_id": "activate_water_recovery"},
        )
        self.assertEqual(code, 200)
        self.assertGreater(act["game_state"]["resources"]["water"], water_before)

    # 6 & 9. Food Consumption & Greenhouse Harvest Cycle
    def test_06_food_consumption_and_greenhouse_production(self) -> None:
        state = self._start_mission(difficulty="expert", crew_size=2)
        mid = state["mission_id"]

        _, d2 = call_api("POST", f"/api/game/{mid}/advance")
        food_after_day1 = d2["game_state"]["resources"]["food"]
        self.assertLess(food_after_day1, 85.0)
        self.assertEqual(d2["game_state"]["subsystems"]["greenhouse_growth_days"], 1)

        _, d3 = call_api("POST", f"/api/game/{mid}/advance")
        food_after_harvest = d3["game_state"]["resources"]["food"]
        self.assertGreater(food_after_harvest, food_after_day1)
        self.assertEqual(d3["game_state"]["subsystems"]["greenhouse_growth_days"], 0)

    # 7. Solar Power Generation & Repair Solar Panels Action
    def test_07_power_generation_and_solar_repair(self) -> None:
        state = self._start_mission(difficulty="expert")
        mid = state["mission_id"]

        code, repaired = call_api(
            "POST",
            f"/api/game/{mid}/action",
            {"action_id": "repair_solar_panels"},
        )
        self.assertEqual(code, 200)
        self.assertGreater(repaired["game_state"]["subsystems"]["solar_efficiency"], 1.0)

    # 8. Power Allocation Validation
    def test_08_power_allocation_validation(self) -> None:
        state = self._start_mission(difficulty="expert")  # starts with 85 power
        mid = state["mission_id"]

        bad_code, bad_resp = call_api(
            "POST",
            f"/api/game/{mid}/power",
            {
                "life_support": 40.0,
                "radiation_shelter": 25.0,
                "greenhouse": 20.0,
                "communication": 10.0,
                "scientific_research": 10.0,
            },
        )
        self.assertEqual(bad_code, 400)
        self.assertIn("cannot exceed", bad_resp["detail"])

        ok_code, ok_resp = call_api(
            "POST",
            f"/api/game/{mid}/power",
            {
                "life_support": 35.0,
                "radiation_shelter": 15.0,
                "greenhouse": 15.0,
                "communication": 5.0,
                "scientific_research": 5.0,
            },
        )
        self.assertEqual(ok_code, 200)
        self.assertEqual(ok_resp["power_allocation"]["life_support"], 35.0)

    # 8b. Priority Load-Shedding When Power Is Scarce
    def test_09_priority_load_shedding_protects_life_support(self) -> None:
        from app.models.schemas import PowerAllocation
        from app.services.resource_manager import compute_effective_power_distribution

        alloc = PowerAllocation(
            life_support=30.0,
            radiation_shelter=15.0,
            greenhouse=15.0,
            communication=10.0,
            scientific_research=10.0,
        )
        effective, used, notes = compute_effective_power_distribution(
            available_power_pool=40.0,
            allocation=alloc,
            conservation_active=False,
        )
        self.assertEqual(effective["life_support"], 30.0)
        self.assertEqual(effective["radiation_shelter"], 10.0)
        self.assertEqual(effective["greenhouse"], 0.0)
        self.assertEqual(effective["communication"], 0.0)
        self.assertEqual(effective["scientific_research"], 0.0)
        self.assertEqual(used, 40.0)
        self.assertTrue(any("shut down" in n or "reduced power" in n for n in notes))

    # 10. Radiation Shelter Activation & Deterministic Event Resolution
    def test_10_radiation_shelter_and_simulated_events(self) -> None:
        state = self._start_mission(deterministic=True, enable_random_events=True)
        mid = state["mission_id"]

        code, shelter_res = call_api(
            "POST",
            f"/api/game/{mid}/action",
            {"action_id": "activate_radiation_shelter"},
        )
        self.assertEqual(code, 200)
        self.assertEqual(shelter_res["game_state"]["resources"]["shield"], 65.0)
        self.assertTrue(shelter_res["game_state"]["subsystems"]["radiation_shelter_active"])

        _, _ = call_api("POST", f"/api/game/{mid}/advance")
        ev_code, ev_list = call_api("GET", f"/api/game/{mid}/events")
        self.assertEqual(ev_code, 200)
        self.assertEqual(len(ev_list["active_events"]), 1)
        event = ev_list["active_events"][0]
        self.assertEqual(event["label"], "SIMULATED TRAINING EVENT")

        res_code, resolved = call_api(
            "POST",
            f"/api/game/{mid}/action",
            {
                "action_id": "resolve_event",
                "event_id": event["event_id"],
                "choice_id": event["decisions"][0]["choice_id"],
            },
        )
        self.assertEqual(res_code, 200)
        self.assertEqual(len(resolved["game_state"]["active_events"]), 0)

    # 11. Invalid Actions & Conservation Trade-Off
    def test_11_invalid_actions_and_conservation_tradeoff(self) -> None:
        state = self._start_mission()
        mid = state["mission_id"]

        bad_code, _ = call_api(
            "POST",
            f"/api/game/{mid}/action",
            {"action_id": "launch_warp_drive"},
        )
        self.assertEqual(bad_code, 400)

        cons_code, _ = call_api(
            "POST",
            f"/api/game/{mid}/action",
            {"action_id": "emergency_conservation_mode"},
        )
        self.assertEqual(cons_code, 200)

        res_code, _ = call_api(
            "POST",
            f"/api/game/{mid}/action",
            {"action_id": "start_scientific_research"},
        )
        self.assertEqual(res_code, 400)

    # 12 & 14. Mission Day Progression & Completion
    def test_12_and_14_mission_progression_and_completion(self) -> None:
        state = self._start_mission(duration=5, crew_size=2, difficulty="explorer")
        mid = state["mission_id"]

        for expected_next_day in (2, 3, 4, 5):
            code, resp = call_api("POST", f"/api/game/{mid}/advance")
            self.assertEqual(code, 200)
            self.assertEqual(resp["game_state"]["current_day"], expected_next_day)
            self.assertEqual(resp["game_state"]["mission_status"], "In Progress")
            self._assert_resources_bounded(resp["game_state"]["resources"])

        code_final, final_resp = call_api("POST", f"/api/game/{mid}/advance")
        self.assertEqual(code_final, 200)
        self.assertEqual(final_resp["game_state"]["mission_status"], "Mission Successful")
        self.assertIsNotNone(final_resp["game_state"]["outcome_explanation"])

        after_code, _ = call_api("POST", f"/api/game/{mid}/advance")
        self.assertEqual(after_code, 400)

    # 13. Mission Failure Conditions & Non-Negative Resource Clamping
    def test_13_mission_failure_and_non_negative_resources(self) -> None:
        state = self._start_mission(difficulty="expert", crew_size=6, duration=15)
        mid = state["mission_id"]

        call_api(
            "POST",
            f"/api/game/{mid}/power",
            {
                "life_support": 0.0,
                "radiation_shelter": 0.0,
                "greenhouse": 0.0,
                "communication": 0.0,
                "scientific_research": 0.0,
            },
        )

        final_state = state
        for _ in range(12):
            code, step = call_api("POST", f"/api/game/{mid}/advance")
            if code != 200:
                break
            final_state = step["game_state"]
            self._assert_resources_bounded(final_state["resources"])
            if final_state["mission_status"] == "Mission Failed":
                break

        self.assertEqual(final_state["mission_status"], "Mission Failed")
        self.assertIsNotNone(final_state["outcome_explanation"])
        self._assert_resources_bounded(final_state["resources"])

    # 15. Deterministic Reproducibility Check
    def test_15_reproducible_deterministic_simulation(self) -> None:
        def run_scripted_sequence() -> Dict[str, Any]:
            m = self._start_mission(
                difficulty="commander",
                crew_size=4,
                duration=5,
                deterministic=True,
                enable_random_events=False,
            )
            mid = m["mission_id"]
            call_api("POST", f"/api/game/{mid}/action", {"action_id": "start_scientific_research"})
            call_api("POST", f"/api/game/{mid}/advance")
            call_api("POST", f"/api/game/{mid}/action", {"action_id": "activate_radiation_shelter"})
            _, out = call_api("POST", f"/api/game/{mid}/advance")
            return out["game_state"]

        run_a = run_scripted_sequence()
        run_b = run_scripted_sequence()

        self.assertEqual(run_a["resources"], run_b["resources"])
        self.assertEqual(run_a["science_points"], run_b["science_points"])
        self.assertEqual(run_a["crew_status"]["general_health"], run_b["crew_status"]["general_health"])
        self.assertEqual(run_a["current_day"], run_b["current_day"])


if __name__ == "__main__":
    unittest.main()
