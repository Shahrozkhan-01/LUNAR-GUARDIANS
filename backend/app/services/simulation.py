"""
LUNAR GUARDIANS — Core Simulation Engine Orchestrator.

Coordinates mission creation, player actions, power allocation updates,
daily progression, crew condition updates, and win/loss evaluation.
"""

import random
import uuid
from typing import List, Tuple
from app import config
from app.models.schemas import (
    ActionResponse,
    ActivityLogEntry,
    AdvanceDayResponse,
    ExecuteActionRequest,
    GameState,
    MissionDecisionRecord,
    MissionEventRecord,
    PlayerActionDefinition,
    PowerAllocation,
    PowerUpdateRequest,
    ResourcesState,
    StartMissionRequest,
    SubsystemStatus,
)
from app.services.crew_manager import build_initial_crew_status, update_crew_condition
from app.services.event_manager import (
    activate_radiation_shelter,
    apply_unresolved_events,
    maybe_trigger_daily_event,
    maybe_trigger_nasa_scenario,
    resolve_event_decision,
    resolve_nasa_training_event_decision,
)
from app.services.nasa_training_service import build_nasa_training_events
from app.services.nasa_service import get_cached_nasa_events
from app.services.resource_manager import (
    clamp_resource,
    process_daily_resources,
    validate_power_allocation,
)
from app.services.store import mission_store


def _build_available_actions() -> List[PlayerActionDefinition]:
    return [
        PlayerActionDefinition(**defn)
        for defn in config.ACTION_DEFINITIONS.values()
    ]


def _append_log(
    state: GameState,
    message: str,
    category: str = "info",
    day: int | None = None,
) -> None:
    entry = ActivityLogEntry(
        id=f"log-{uuid.uuid4().hex[:8]}",
        day=day if day is not None else state.current_day,
        category=category,  # type: ignore[arg-type]
        message=message,
    )
    state.activity_log.insert(0, entry)
    del state.activity_log[30:]


def _trim_allocations_to_power(state: GameState) -> None:
    """Keep total power_allocation <= current battery power after immediate action costs."""
    if state.power_allocation.total() <= state.resources.power:
        return
    excess = round(state.power_allocation.total() - state.resources.power, 1)
    for sys_key in reversed(config.POWER_PRIORITY_ORDER):
        if excess <= 0:
            break
        cur = getattr(state.power_allocation, sys_key)
        cut = min(cur, excess)
        setattr(state.power_allocation, sys_key, round(cur - cut, 1))
        excess = round(excess - cut, 1)


def create_mission(req: StartMissionRequest) -> GameState:
    diff_cfg = config.DIFFICULTY_SETTINGS[req.difficulty]
    start_res = diff_cfg["starting_resources"]

    mission_id = f"lg-{uuid.uuid4().hex[:10]}"
    nasa_training_events, seen_nasa_event_ids = build_nasa_training_events(
        mission_id, day=1
    )
    seed = (
        req.seed
        if req.seed is not None
        else (101 if req.deterministic else random.randint(1, 99999))
    )

    resources = ResourcesState(
        oxygen=start_res["oxygen"],
        water=start_res["water"],
        power=start_res["power"],
        food=start_res["food"],
        shield=start_res["shield"],
    )

    power_allocation = PowerAllocation(**config.DEFAULT_POWER_ALLOCATION)
    subsystems = SubsystemStatus(
        oxygen_recycling_active=True,
        water_recovery_active=True,
        greenhouse_active=True,
        greenhouse_growth_days=0,
        radiation_shelter_active=False,
        shelter_boost_days_left=0,
        research_active=False,
        research_days_left=0,
        conservation_mode_days_left=0,
        solar_efficiency=config.INITIAL_SOLAR_EFFICIENCY,
    )

    crew_status = build_initial_crew_status(req.crew_size)

    state = GameState(
        mission_id=mission_id,
        mission_name=req.mission_name or "Lunar Outpost Alpha",
        destination=req.destination,
        difficulty=req.difficulty,
        crew_size=req.crew_size,
        duration=req.duration,
        current_day=1,
        mission_status="In Progress",
        outcome_explanation=None,
        science_points=diff_cfg["starting_science_points"],
        deterministic=req.deterministic,
        enable_random_events=req.enable_random_events,
        seed=seed,
        resources=resources,
        power_allocation=power_allocation,
        subsystems=subsystems,
        crew_status=crew_status,
        active_events=[],
        nasa_training_events=nasa_training_events,
        seen_nasa_event_ids=seen_nasa_event_ids,
        available_actions=_build_available_actions(),
        educational_tips=[
            "Welcome, Commander! Keep Oxygen, Water, and Food supplied while managing your Solar Power.",
            "Click any Action or adjust Power Allocation before advancing to the next lunar day!",
        ],
        activity_log=[],
    )

    _append_log(
        state,
        f"Mission initialized on {diff_cfg['label']} difficulty with {req.crew_size} astronauts for {req.duration} simulated days.",
        category="info",
        day=1,
    )
    return mission_store.save(state)


def get_mission_or_error(mission_id: str) -> GameState:
    state = mission_store.get(mission_id)
    if state is None:
        raise KeyError(f"Mission '{mission_id}' not found.")
    return state


def update_power_allocation(
    mission_id: str, req: PowerUpdateRequest
) -> Tuple[GameState, List[str]]:
    state = get_mission_or_error(mission_id)
    if state.mission_status != "In Progress":
        raise ValueError(f"Cannot modify power allocation: {state.mission_status}.")

    is_valid, msg, edu_notes = validate_power_allocation(req, state.resources.power)
    if not is_valid:
        raise ValueError(msg)

    state.power_allocation = PowerAllocation(
        life_support=round(req.life_support, 1),
        radiation_shelter=round(req.radiation_shelter, 1),
        greenhouse=round(req.greenhouse, 1),
        communication=round(req.communication, 1),
        scientific_research=round(req.scientific_research, 1),
    )

    if edu_notes:
        state.educational_tips = edu_notes

    _append_log(
        state,
        f"Updated power grid allocation (Total: {state.power_allocation.total()}/{state.resources.power} units).",
        category="action",
    )
    saved = mission_store.save(state)
    return saved, edu_notes


def execute_player_action(
    mission_id: str, req: ExecuteActionRequest
) -> ActionResponse:
    state = get_mission_or_error(mission_id)
    if state.mission_status != "In Progress":
        raise ValueError(f"Cannot execute actions because mission is '{state.mission_status}'.")

    # Branch 1: Event Decision Resolution
    if req.action_id == "resolve_event":
        if not req.event_id or not req.choice_id:
            raise ValueError("Both event_id and choice_id are required to resolve an event.")
        feedback, edu = resolve_event_decision(state, req.event_id, req.choice_id)
        _trim_allocations_to_power(state)
        update_crew_condition(state.crew_status, state.resources)
        state.educational_tips = [edu]
        _append_log(state, feedback, category="event")
        saved = mission_store.save(state)
        return ActionResponse(
            action_name="Event Decision",
            feedback_message=feedback,
            educational_note=edu,
            game_state=saved,
        )

    if req.action_id == "resolve_nasa_training_event":
        if not req.event_id or not req.choice_id:
            raise ValueError(
                "Both event_id and choice_id are required to resolve a NASA training event."
            )
        feedback, edu = resolve_nasa_training_event_decision(
            state, req.event_id, req.choice_id
        )
        _trim_allocations_to_power(state)
        update_crew_condition(state.crew_status, state.resources)
        state.educational_tips = [edu]
        _append_log(state, feedback, category="event")
        saved = mission_store.save(state)
        return ActionResponse(
            action_name="NASA Training Event Decision",
            feedback_message=feedback,
            educational_note=edu,
            game_state=saved,
        )

    # Branch 2: Standard Outpost Player Actions (1–7)
    if req.action_id not in config.ACTION_DEFINITIONS:
        raise ValueError(f"Invalid player action '{req.action_id}'.")

    defn = config.ACTION_DEFINITIONS[req.action_id]
    cost = defn["cost"]
    res = state.resources
    sub = state.subsystems

    # Verify resource costs
    for res_key, req_amount in cost.items():
        if getattr(res, res_key) < req_amount:
            raise ValueError(
                f"Not enough {res_key.title()} to run '{defn['name']}' "
                f"(needs {req_amount} units, have {getattr(res, res_key)})."
            )

    # Deduct costs
    for res_key, req_amount in cost.items():
        if req_amount > 0:
            setattr(res, res_key, clamp_resource(getattr(res, res_key) - req_amount))

    action_id = req.action_id
    if action_id == "activate_oxygen_recycling":
        sub.oxygen_recycling_active = True
        res.oxygen = clamp_resource(res.oxygen + defn["immediate_oxygen_gain"])
        if state.power_allocation.life_support < config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING and res.power >= config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING:
            state.power_allocation.life_support = config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING
        feedback = "Oxygen Recycling activated! Cabin CO2 scrubbers cleaned the air (+4 Oxygen)."
        edu = "Recycling air lets astronauts breathe safely without waiting for new oxygen tanks from Earth!"

    elif action_id == "activate_water_recovery":
        sub.water_recovery_active = True
        res.water = clamp_resource(res.water + defn["immediate_water_gain"])
        feedback = "Water Recovery pumps activated! (+4 clean Water units recovered)."
        edu = "On a lunar base, water filtration turns moisture in the air back into clean drinking water!"

    elif action_id == "activate_greenhouse":
        sub.greenhouse_active = True
        if state.power_allocation.greenhouse < config.MIN_GREENHOUSE_POWER and res.power >= state.power_allocation.life_support + config.MIN_GREENHOUSE_POWER:
            state.power_allocation.greenhouse = config.MIN_GREENHOUSE_POWER
        feedback = "Greenhouse irrigated and grow-lights energized! Fresh food will be ready in 2 growth days."
        edu = "Your greenhouse needs electricity and water before it can produce food for your astronauts."

    elif action_id == "activate_radiation_shelter":
        feedback, edu = activate_radiation_shelter(state)

    elif action_id == "start_scientific_research":
        if sub.conservation_mode_days_left > 0:
            raise ValueError(
                "Scientific Research cannot start while Emergency Conservation Mode is active!"
            )
        sub.research_active = True
        sub.research_days_left = int(defn["duration_days"])
        state.science_points += int(defn["immediate_science_gain"])
        feedback = "Scientific Research started! Earned +15 Science Points studying lunar geology."
        edu = "Studying Moon rocks helps scientists learn how both the Moon and Earth formed billions of years ago!"

    elif action_id == "emergency_conservation_mode":
        sub.conservation_mode_days_left = int(defn["duration_days"])
        sub.research_active = False
        sub.research_days_left = 0
        res.power = clamp_resource(res.power + defn["immediate_power_saved"])
        feedback = "Emergency Conservation Mode engaged for 2 days! (+10 Power saved; Research suspended)."
        edu = "During power shortages, real mission controllers shut down non-essential experiments first to keep astronauts alive."

    elif action_id == "repair_solar_panels":
        prev_eff = sub.solar_efficiency
        sub.solar_efficiency = round(
            min(config.MAX_SOLAR_EFFICIENCY, sub.solar_efficiency + config.SOLAR_REPAIR_EFFICIENCY_GAIN),
            2,
        )
        pct_now = int(round(sub.solar_efficiency * 100))
        pct_prev = int(round(prev_eff * 100))
        feedback = f"Solar Panels serviced! Array efficiency improved from {pct_prev}% to {pct_now}%."
        edu = "Clean, well-tuned solar panels capture more sunlight every lunar day to charge your outpost batteries!"

    else:
        raise ValueError(f"Unhandled action '{action_id}'.")

    state.mission_decisions.append(
        MissionDecisionRecord(
            day=state.current_day,
            decision_type="outpost_action",
            subject=defn["name"],
            choice="Execute action",
            source_label="SIMULATED GAME ACTION",
            consequence=feedback,
            lesson=edu,
        )
    )
    _trim_allocations_to_power(state)
    update_crew_condition(state.crew_status, state.resources)
    state.educational_tips = [edu]
    _append_log(state, feedback, category="action")

    saved = mission_store.save(state)
    return ActionResponse(
        action_name=defn["name"],
        feedback_message=feedback,
        educational_note=edu,
        game_state=saved,
    )


def _evaluate_mission_outcome(state: GameState, completed_final_day: bool) -> None:
    """Check survival failure conditions and mission completion outcomes."""
    res = state.resources
    crew = state.crew_status

    # Failure conditions: unsustainable life-support depletion or prolonged critical state
    both_vital_empty = res.oxygen <= 0.0 and res.water <= 0.0
    prolonged_critical = crew.critical_days_streak >= config.CONSECUTIVE_CRITICAL_DAYS_FOR_FAILURE
    oxygen_collapsed = res.oxygen <= 0.0 and crew.critical_days_streak >= 1
    water_collapsed = res.water <= 0.0 and crew.critical_days_streak >= 1
    extreme_radiation = crew.radiation_exposure >= config.MAX_RADIATION_FAILURE_LIMIT

    if both_vital_empty or prolonged_critical or oxygen_collapsed or water_collapsed or extreme_radiation:
        state.mission_status = "Mission Failed"
        if res.oxygen <= 0.0:
            reason = (
                "Breathable oxygen ran out! Remember to keep Life Support powered and "
                "Oxygen Recycling active so your astronauts always have air to breathe."
            )
        elif res.water <= 0.0:
            reason = (
                "Clean drinking water ran out! Next time, activate Water Recovery early "
                "to recycle water for your crew."
            )
        elif extreme_radiation:
            reason = (
                "Simulated radiation exposure reached unsafe limits! Remember to activate "
                "the Radiation Shelter when solar storms approach."
            )
        else:
            reason = (
                "Critical resource shortages lasted too long for safe lunar operations. "
                "Balance power, water, oxygen, and food carefully on your next try!"
            )
        state.outcome_explanation = reason
        _append_log(state, f"MISSION FAILED: {reason}", category="outcome")
        return

    if completed_final_day:
        low_reserves = min(res.oxygen, res.water, res.food) < 25.0
        if crew.general_health == "Healthy" and not low_reserves:
            state.mission_status = "Mission Successful"
            state.outcome_explanation = (
                f"Outstanding leadership, Commander! All {state.crew_size} astronauts completed "
                f"the {state.duration}-day lunar mission in healthy condition with {state.science_points} Science Points!"
            )
        else:
            state.mission_status = "Mission Completed with Difficulties"
            state.outcome_explanation = (
                f"Your crew survived all {state.duration} days on the Moon and earned {state.science_points} Science Points, "
                "though low reserves or warnings made the final days tough. Great resilience!"
            )
        _append_log(state, f"{state.mission_status.upper()}: {state.outcome_explanation}", category="outcome")


def advance_mission_day(mission_id: str) -> AdvanceDayResponse:
    """
    Advance the lunar simulation by 1 day:
    1. Validate mission state
    2. Apply unresolved event effects
    3. Calculate daily consumption & production
    4. Tick subsystem timers
    5. Trigger new simulated event (if applicable)
    6. Update crew condition
    7. Check mission objectives & increment day
    """
    state = get_mission_or_error(mission_id)
    if state.mission_status != "In Progress":
        raise ValueError(
            f"Mission cannot advance because current status is '{state.mission_status}'."
        )

    completed_day_number = state.current_day
    is_completing_final_day = completed_day_number >= state.duration

    day_notes: List[str] = []

    # 1. Process any unresolved events from the current day
    event_notes = apply_unresolved_events(state)
    day_notes.extend(event_notes)

    # 2. Calculate daily resource consumption, recycling, power & production
    res_notes, science_gained = process_daily_resources(state)
    day_notes.extend(res_notes)
    state.science_points += science_gained

    # 3. Decrement temporary subsystem timers
    sub = state.subsystems
    if sub.shelter_boost_days_left > 0:
        sub.shelter_boost_days_left -= 1
        if sub.shelter_boost_days_left == 0:
            sub.radiation_shelter_active = False
    if sub.research_days_left > 0:
        sub.research_days_left -= 1
        if sub.research_days_left == 0:
            sub.research_active = False
    if sub.conservation_mode_days_left > 0:
        sub.conservation_mode_days_left -= 1

    # 4. Update crew condition & educational health explanations
    crew_notes = update_crew_condition(state.crew_status, state.resources)

    # 5. Evaluate failure or completion
    _evaluate_mission_outcome(state, completed_final_day=is_completing_final_day)

    # 6. Increment mission day if still in progress, and trigger next day's event
    if state.mission_status == "In Progress":
        state.current_day = completed_day_number + 1
        new_event = maybe_trigger_nasa_scenario(state, get_cached_nasa_events())
        if new_event is None:
            new_event = maybe_trigger_daily_event(state, state.current_day)
        if new_event is not None:
            state.active_events.append(new_event)
            state.mission_events.append(
                MissionEventRecord(
                    day=new_event.day_triggered,
                    title=new_event.name,
                    source_label=new_event.label,
                    description=new_event.description,
                    event_type=new_event.source_event_type,
                    source_event_id=new_event.source_event_id,
                )
            )
            event_msg = (
                f"{new_event.label}: {new_event.name} — {new_event.description}"
            )
            day_notes.append(event_msg)
            _append_log(state, event_msg, category="event", day=state.current_day)

        summary = (
            f"Advanced to Day {state.current_day} of {state.duration}. "
            f"Earned +{science_gained} Science Points (Crew: {state.crew_status.general_health})."
        )
        _append_log(state, summary, category="info", day=state.current_day)
    else:
        summary = state.outcome_explanation or f"Mission ended: {state.mission_status}."

    # Combine unique educational notes for frontend display
    combined_tips: List[str] = []
    for tip in day_notes + crew_notes:
        if tip not in combined_tips:
            combined_tips.append(tip)
    state.educational_tips = combined_tips[:5]

    saved = mission_store.save(state)
    return AdvanceDayResponse(
        day_summary=summary,
        educational_notes=state.educational_tips,
        game_state=saved,
    )
