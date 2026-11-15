"""
LUNAR GUARDIANS — Simulated Event Manager.

Implements scripted SIMULATED TRAINING EVENTS with player decision options,
gameplay trade-offs, unresolved consequences, and deterministic scenario modes
for reproducible automated testing.
"""

import random
from typing import Dict, List, Optional, Tuple
from app import config
from app.models.schemas import (
    EventDecisionOption,
    GameState,
    MissionDecisionRecord,
    SimulatedEvent,
)
from app.services.resource_manager import clamp_resource
from app.services.nasa_event_classifier import (
    is_eligible_nasa_event,
    is_eligible_sep_for_scenario,
)


EVENT_TEMPLATES: Dict[str, Dict] = {
    "solar_storm_warning": {
        "name": "Solar Storm Warning",
        "severity": "high",
        "description": (
            "Outpost sensors detected a simulated wave of energetic solar particles "
            "approaching the Moon! Without shelter protection, crew radiation risk will rise."
        ),
        "decisions": [
            EventDecisionOption(
                choice_id="energize_storm_shelter",
                label="Energize Radiation Shelter",
                cost_text="Costs 10 Power (pauses Research)",
                consequence_text="+16 Shield Protection and blocks storm radiation exposure.",
            ),
            EventDecisionOption(
                choice_id="stay_on_normal_ops",
                label="Keep Standard Operations",
                cost_text="0 Power",
                consequence_text="-12 Shield Protection and +18 simulated radiation exposure.",
            ),
        ],
    },
    "solar_panel_dust": {
        "name": "Solar Panel Dust Accumulation",
        "severity": "medium",
        "description": (
            "Clingy lunar dust (regolith) has settled across the solar arrays, blocking "
            "sunlight and reducing electricity generation."
        ),
        "decisions": [
            EventDecisionOption(
                choice_id="dispatch_dust_sweep",
                label="Send Astronaut Dust-Sweep Team",
                cost_text="Costs 6 Power & 3 Oxygen",
                consequence_text="Restores solar panel efficiency to 105% and earns +8 Science Points.",
            ),
            EventDecisionOption(
                choice_id="postpone_sweep",
                label="Wait Until Later",
                cost_text="0 Resources now",
                consequence_text="Solar panel efficiency drops by 20% until repaired.",
            ),
        ],
    },
    "greenhouse_equipment_failure": {
        "name": "Greenhouse Equipment Failure",
        "severity": "medium",
        "description": (
            "A nutrient misting nozzle clogged inside the Lunar Greenhouse! Young crops "
            "need quick maintenance to stay healthy."
        ),
        "decisions": [
            EventDecisionOption(
                choice_id="fix_greenhouse_nozzle",
                label="Repair Misting Nozzle",
                cost_text="Costs 7 Power & 3 Water",
                consequence_text="Saves the crop batch and grants +8 Food.",
            ),
            EventDecisionOption(
                choice_id="shut_down_affected_tray",
                label="Shut Down Affected Crop Tray",
                cost_text="0 Power",
                consequence_text="-10 Food and resets current greenhouse growth progress.",
            ),
        ],
    },
    "water_recovery_fault": {
        "name": "Water Recovery System Fault",
        "severity": "high",
        "description": (
            "A pressure seal in the water filtration unit is leaking! Clean drinking water "
            "reserves will drop unless repaired."
        ),
        "decisions": [
            EventDecisionOption(
                choice_id="replace_water_seal",
                label="Install Spare Filter Seal",
                cost_text="Costs 8 Power",
                consequence_text="Keeps Water Recovery online and recovers +8 Water.",
            ),
            EventDecisionOption(
                choice_id="accept_water_rationing",
                label="Switch to Strict Water Rationing",
                cost_text="0 Power",
                consequence_text="-12 Water and turns Water Recovery off until reactivated.",
            ),
        ],
    },
    "communication_interruption": {
        "name": "Communication Interruption",
        "severity": "low",
        "description": (
            "Extreme lunar temperature shifts nudged the main dish slightly out of "
            "alignment with Mission Control on Earth."
        ),
        "decisions": [
            EventDecisionOption(
                choice_id="realign_dish",
                label="Realign Dish Motors",
                cost_text="Costs 6 Power",
                consequence_text="Restores clear Earth link and earns +10 Science Points.",
            ),
            EventDecisionOption(
                choice_id="use_low_gain_backup",
                label="Use Low-Gain Backup Radio",
                cost_text="0 Power",
                consequence_text="Saves electricity, but loses 5 Science Points.",
            ),
        ],
    },
}

# Deterministic day -> event key mapping for reproducible scenario testing
DETERMINISTIC_EVENT_SCHEDULE: Dict[int, str] = {
    2: "solar_panel_dust",
    4: "solar_storm_warning",
    6: "water_recovery_fault",
    8: "greenhouse_equipment_failure",
    11: "communication_interruption",
}

ORDERED_EVENT_KEYS = list(EVENT_TEMPLATES.keys())


def build_simulated_event(template_key: str, day: int) -> SimulatedEvent:
    tpl = EVENT_TEMPLATES[template_key]
    return SimulatedEvent(
        event_id=f"{template_key}_day_{day}",
        label="SIMULATED TRAINING EVENT",
        name=tpl["name"],
        description=tpl["description"],
        severity=tpl["severity"],
        day_triggered=day,
        resolved=False,
        decisions=tpl["decisions"],
    )


def build_nasa_event_scenario(event: Dict, day: int) -> SimulatedEvent:
    """Create a monitoring/awareness decision from a real timed DONKI record."""
    event_type = event["event_type"]
    is_sep = event_type == "SEP"
    event_explanation = (
        "Solar Energetic Particles are fast particles from the Sun. They can be "
        "important for astronaut safety, but this NASA record does not measure "
        "radiation at the Moon or tell us the crew's dose."
        if is_sep
        else "A solar flare is a bright burst of X-rays from the Sun. Its flare "
        "class is not an astronaut radiation dose, and this record does not "
        "measure radiation at the Moon."
    )
    mission_situation = (
        "Mission Control asks the crew to review its shelter plan and choose how "
        "to respond to the NASA particle-event report."
        if is_sep
        else "Mission Control asks the crew to review the solar-weather update "
        "and plan its science schedule. The flare record alone does not call for "
        "a radiation emergency."
    )
    decisions = (
        [
            EventDecisionOption(
                choice_id="nasa_activate_shelter",
                label="Move crew into the Radiation Shelter",
                cost_text="Uses 10 SIMULATED Power units",
                consequence_text=(
                    "Applies the game's existing shelter and shield mechanics; "
                    "it is not a measured dose or NASA risk estimate."
                ),
            ),
            EventDecisionOption(
                choice_id="nasa_pause_outdoor_monitor",
                label="Pause outdoor work and monitor updates",
                cost_text="Uses 3 SIMULATED Power units",
                consequence_text=(
                    "The game spends power on monitoring and awards practice "
                    "points; no radiation protection is measured."
                ),
            ),
            EventDecisionOption(
                choice_id="nasa_continue_operations",
                label="Continue normal operations",
                cost_text="No power used",
                consequence_text=(
                    "Game-only shield and exposure indicators change. They are "
                    "not actual crew exposure or NASA measurements."
                ),
            ),
        ]
        if is_sep
        else [
            EventDecisionOption(
                choice_id="nasa_monitor_solar_conditions",
                label="Review NASA updates and monitor conditions",
                cost_text="Uses 2 SIMULATED Power units",
                consequence_text=(
                    "Spends game power and earns practice science points; no "
                    "dose or safety level is calculated."
                ),
            ),
            EventDecisionOption(
                choice_id="nasa_pause_outdoor_observations",
                label="Pause outdoor observations for now",
                cost_text="Loses 2 SIMULATED Science points",
                consequence_text=(
                    "The game trades a little research progress for a cautious "
                    "schedule; no radiation effect is assumed."
                ),
            ),
            EventDecisionOption(
                choice_id="nasa_continue_scheduled_research",
                label="Continue scheduled research",
                cost_text="Uses 3 SIMULATED Power units",
                consequence_text=(
                    "Earns more game science points while using power. This "
                    "flare record alone does not imply a radiation hazard."
                ),
            ),
        ]
    )
    return SimulatedEvent(
        event_id=f"nasa_{event_type.lower()}_{event['deduplication_key'][:24]}",
        label="REAL NASA DATA",
        source_type="NASA",
        source_event_type=event_type,
        source_event_id=(
            str(event["event_id"]) if event.get("event_id") is not None else None
        ),
        source_event_time=event.get("event_time"),
        source_url=event.get("source_url"),
        event_category=event.get("category"),
        educational_explanation=event_explanation,
        mission_situation=mission_situation,
        consequence_label="SIMULATED GAME CONSEQUENCE",
        name=(
            "Solar Energetic Particle Alert"
            if is_sep
            else "Solar Activity Monitoring Alert"
        ),
        description=(
            "Use this NASA observation to practice reviewing space-weather "
            "information. The game consequences below are simplified learning "
            "activities, not real safety advice."
        ),
        severity="low",
        day_triggered=day,
        decisions=decisions,
    )


def build_nasa_sep_scenario(event: Dict, day: int) -> SimulatedEvent:
    """Compatibility wrapper for callers building a SEP-only scenario."""
    if event.get("event_type") != "SEP":
        raise ValueError("A SEP event is required for a SEP scenario.")
    return build_nasa_event_scenario(event, day)


def maybe_trigger_nasa_scenario(
    state: GameState, nasa_events: List[Dict]
) -> Optional[SimulatedEvent]:
    """Select one new timed SEP or flare event without replaying it in a mission."""
    if any(not event.resolved for event in state.active_events):
        return None

    ordered_events = sorted(
        nasa_events,
        key=lambda event: event.get("event_time") or "",
        reverse=True,
    )
    for event in ordered_events:
        if not is_eligible_nasa_event(event):
            continue
        event_key = event["deduplication_key"]
        if event_key in state.seen_nasa_event_ids:
            continue
        state.seen_nasa_event_ids.append(event_key)
        return build_nasa_event_scenario(event, state.current_day)
    return None


def maybe_trigger_nasa_sep_scenario(
    state: GameState, sep_events: List[Dict]
) -> Optional[SimulatedEvent]:
    """Compatibility wrapper for SEP-only scenario selection."""
    return maybe_trigger_nasa_scenario(
        state,
        [event for event in sep_events if event.get("event_type") == "SEP"],
    )


def activate_radiation_shelter(
    state: GameState, charge_power: bool = False
) -> Tuple[str, str]:
    """Apply the existing shelter action mechanics to an event decision."""
    resources = state.resources
    subsystem = state.subsystems
    shelter_action = config.ACTION_DEFINITIONS["activate_radiation_shelter"]
    power_cost = shelter_action["cost"]["power"]
    if charge_power:
        if resources.power < power_cost:
            raise ValueError(
                f"Not enough battery power (requires {power_cost} Power) to energize the shelter!"
            )
        resources.power = clamp_resource(resources.power - power_cost)

    subsystem.radiation_shelter_active = True
    subsystem.shelter_boost_days_left = int(shelter_action["duration_days"])
    resources.shield = clamp_resource(
        resources.shield + shelter_action["immediate_shield_gain"]
    )
    state.crew_status.radiation_exposure = clamp_resource(
        state.crew_status.radiation_exposure - 8.0
    )

    paused_note = ""
    if resources.power < 45.0 and (
        subsystem.research_active or state.power_allocation.scientific_research > 0
    ):
        subsystem.research_active = False
        freed = state.power_allocation.scientific_research
        state.power_allocation.scientific_research = 0.0
        state.power_allocation.radiation_shelter = min(
            resources.power,
            max(
                state.power_allocation.radiation_shelter,
                config.MIN_SHELTER_POWER + 3.0,
            ),
        )
        if freed > 0:
            paused_note = " Scientific Research was paused so the shelter has enough electricity."
    elif (
        state.power_allocation.radiation_shelter < config.MIN_SHELTER_POWER
        and resources.power
        >= state.power_allocation.life_support + config.MIN_SHELTER_POWER
    ):
        state.power_allocation.radiation_shelter = config.MIN_SHELTER_POWER

    return (
        f"Radiation Shelter activated! Shield Protection boosted by +15 for 3 days.{paused_note}",
        "Radiation shelters use power, but they help protect astronauts during dangerous solar events.",
    )


def maybe_trigger_daily_event(state: GameState, target_day: int) -> Optional[SimulatedEvent]:
    """
    Trigger a scripted SIMULATED TRAINING EVENT according to deterministic schedule
    or seeded probability. Returns None if random events are disabled and not scheduled.
    """
    if not state.enable_random_events:
        return None

    # Avoid stacking more than 1 unresolved event at once so 7–12 year olds aren't overwhelmed
    unresolved = [e for e in state.active_events if not e.resolved]
    if unresolved:
        return None

    if state.deterministic:
        key = DETERMINISTIC_EVENT_SCHEDULE.get(target_day)
        return build_simulated_event(key, target_day) if key else None

    # Seeded reproducible pseudo-random trigger per (seed, target_day)
    rng = random.Random(state.seed + target_day * 131)
    if target_day >= 2 and rng.random() < 0.55:
        chosen_key = rng.choice(ORDERED_EVENT_KEYS)
        return build_simulated_event(chosen_key, target_day)

    return None


def apply_unresolved_events(state: GameState) -> List[str]:
    """
    If the player advances the day while an active event was left unresolved,
    apply its passive gameplay consequence scaled by difficulty severity.
    """
    notes: List[str] = []
    sev_mult = config.DIFFICULTY_SETTINGS[state.difficulty]["event_severity_multiplier"]

    remaining_events: List[SimulatedEvent] = []
    for event in state.active_events:
        if event.resolved:
            continue

        if event.source_type == "NASA" and event.source_event_type == "SEP":
            if state.subsystems.radiation_shelter_active and state.resources.shield >= 50:
                loss = round(5.0 * sev_mult, 1)
                state.resources.shield = clamp_resource(state.resources.shield - loss)
                notes.append(
                    "SIMULATED GAME CONSEQUENCE: your active shelter reduced the "
                    "game-only shield change for this NASA SEP learning scenario."
                )
            else:
                shield_loss = round(8.0 * sev_mult, 1)
                rad_gain = round(8.0 * sev_mult, 1)
                state.resources.shield = clamp_resource(state.resources.shield - shield_loss)
                state.crew_status.radiation_exposure = clamp_resource(
                    state.crew_status.radiation_exposure + rad_gain
                )
                notes.append(
                    "SIMULATED GAME CONSEQUENCE: the shelter decision was missed, "
                    "so game-only shield and exposure indicators changed. This is "
                    "not an observed dose or actual crew exposure."
                )
        elif event.source_type == "NASA":
            notes.append(
                "SIMULATED GAME CONSEQUENCE: the solar-activity monitoring alert "
                "expired without changing crew exposure or applying an automatic hazard."
            )
        elif "solar_storm_warning" in event.event_id:
            if state.subsystems.radiation_shelter_active and state.resources.shield >= 50:
                loss = round(5.0 * sev_mult, 1)
                state.resources.shield = clamp_resource(state.resources.shield - loss)
                notes.append(
                    "Your active Radiation Shelter absorbed most of the simulated solar storm!"
                )
            else:
                shield_loss = round(12.0 * sev_mult, 1)
                rad_gain = round(18.0 * sev_mult, 1)
                state.resources.shield = clamp_resource(state.resources.shield - shield_loss)
                state.crew_status.radiation_exposure = clamp_resource(
                    state.crew_status.radiation_exposure + rad_gain
                )
                notes.append(
                    "Solar Storm Warning went unanswered! Shield Protection dropped and crew radiation exposure increased."
                )
        elif "solar_panel_dust" in event.event_id:
            state.subsystems.solar_efficiency = round(
                max(config.MIN_SOLAR_EFFICIENCY, state.subsystems.solar_efficiency - 0.20 * sev_mult),
                2,
            )
            notes.append(
                "Lunar dust remained on the solar panels! Daily electricity generation is reduced until you repair them."
            )
        elif "greenhouse_equipment_failure" in event.event_id:
            food_loss = round(9.0 * sev_mult, 1)
            state.resources.food = clamp_resource(state.resources.food - food_loss)
            state.subsystems.greenhouse_growth_days = 0
            notes.append(
                "Unrepaired greenhouse nozzle spoiled a crop tray! Food reserves decreased."
            )
        elif "water_recovery_fault" in event.event_id:
            water_loss = round(10.0 * sev_mult, 1)
            state.resources.water = clamp_resource(state.resources.water - water_loss)
            state.subsystems.water_recovery_active = False
            notes.append(
                "Water Recovery Fault leaked clean water and shut off recycling! Activate Water Recovery to restore it."
            )
        elif "communication_interruption" in event.event_id:
            state.science_points = max(0, state.science_points - 5)
            notes.append(
                "Unaligned antenna caused minor telemetry loss (-5 Science Points)."
            )

        event.resolved = True
        # Archive resolved event out of active list

    state.active_events = remaining_events
    return notes


def resolve_event_decision(
    state: GameState, event_id: str, choice_id: str
) -> Tuple[str, str]:
    """
    Execute a player's chosen response to an active SIMULATED TRAINING EVENT.
    Raises ValueError if event/choice is invalid or resources are insufficient.
    Returns (feedback_message, educational_note).
    """
    target: Optional[SimulatedEvent] = next(
        (e for e in state.active_events if e.event_id == event_id and not e.resolved),
        None,
    )
    if target is None:
        raise ValueError(f"Active event '{event_id}' was not found or is already resolved.")
    if choice_id not in {decision.choice_id for decision in target.decisions}:
        raise ValueError(
            f"Decision option '{choice_id}' is not available for event '{event_id}'."
        )

    sev_mult = config.DIFFICULTY_SETTINGS[state.difficulty]["event_severity_multiplier"]
    res = state.resources
    sub = state.subsystems

    if choice_id == "energize_storm_shelter":
        if res.power < 10.0:
            raise ValueError("Not enough battery power (requires 10 Power) to energize the shelter!")
        res.power = clamp_resource(res.power - 10.0)
        res.shield = clamp_resource(res.shield + 16.0)
        sub.radiation_shelter_active = True
        sub.shelter_boost_days_left = max(sub.shelter_boost_days_left, 2)
        sub.research_active = False
        state.crew_status.radiation_exposure = clamp_resource(
            state.crew_status.radiation_exposure - 6.0
        )
        feedback = "Radiation Shelter energized! Crew protected from the simulated solar storm."
        edu = "Radiation shelters use extra electricity, so pausing lab research during solar storms keeps astronauts safe!"

    elif target.source_type == "NASA" and choice_id == "nasa_activate_shelter":
        feedback, edu = activate_radiation_shelter(state, charge_power=True)
        edu = (
            "Shelters use power to help protect astronauts. Any change to the "
            "radiation indicator here is simulated and is not a NASA measurement."
        )
        feedback = (
            "SIMULATED GAME CONSEQUENCE: " + feedback
            + " The NASA observation itself does not provide a radiation-dose reading."
        )

    elif target.source_type == "NASA" and choice_id == "nasa_pause_outdoor_monitor":
        if res.power < 3.0:
            raise ValueError("Not enough battery power (requires 3 Power) to pause and monitor.")
        res.power = clamp_resource(res.power - 3.0)
        state.science_points += 3
        feedback = (
            "SIMULATED GAME CONSEQUENCE: outdoor work was paused, 3 game Power "
            "units were used, and the crew earned 3 practice Science points."
        )
        edu = (
            "Monitoring NASA updates helps astronauts plan. The practice points "
            "and resource changes are game values, not measurements."
        )

    elif target.source_type == "NASA" and choice_id == "nasa_continue_operations":
        shield_loss = round(8.0 * sev_mult, 1)
        exposure_gain = round(8.0 * sev_mult, 1)
        res.shield = clamp_resource(res.shield - shield_loss)
        state.crew_status.radiation_exposure = clamp_resource(
            state.crew_status.radiation_exposure + exposure_gain
        )
        feedback = (
            "SIMULATED GAME CONSEQUENCE: normal operations continued and the "
            "game-only shield and exposure indicators changed. No real dose "
            "or astronaut exposure was calculated."
        )
        edu = (
            "Some energetic particles can be relevant to astronaut safety. "
            "DONKI event records do not directly measure radiation at a lunar outpost."
        )

    elif target.source_type == "NASA" and choice_id == "nasa_monitor_solar_conditions":
        if res.power < 2.0:
            raise ValueError("Not enough battery power (requires 2 Power) to monitor conditions.")
        res.power = clamp_resource(res.power - 2.0)
        state.science_points += 4
        feedback = (
            "SIMULATED GAME CONSEQUENCE: the crew used 2 game Power units to "
            "review updates and earned 4 practice Science points."
        )
        edu = (
            "Solar flares are solar X-ray observations. Monitoring is a learning "
            "choice; this record does not measure lunar radiation exposure."
        )

    elif target.source_type == "NASA" and choice_id == "nasa_pause_outdoor_observations":
        science_lost = min(2, state.science_points)
        state.science_points -= science_lost
        feedback = (
            "SIMULATED GAME CONSEQUENCE: outdoor observations paused and "
            f"{science_lost} game Science points were not earned."
        )
        edu = (
            "The schedule trade-off is fictional. A flare class is not a measure "
            "of astronaut radiation dose."
        )

    elif target.source_type == "NASA" and choice_id == "nasa_continue_scheduled_research":
        if res.power < 3.0:
            raise ValueError("Not enough battery power (requires 3 Power) to continue research.")
        res.power = clamp_resource(res.power - 3.0)
        state.science_points += 6
        feedback = (
            "SIMULATED GAME CONSEQUENCE: scheduled research continued, using "
            "3 game Power units and earning 6 practice Science points."
        )
        edu = (
            "DONKI reports the flare; it does not say the lunar outpost received "
            "a radiation dose or that this activity is dangerous."
        )

    elif choice_id == "stay_on_normal_ops":
        res.shield = clamp_resource(res.shield - round(12.0 * sev_mult, 1))
        state.crew_status.radiation_exposure = clamp_resource(
            state.crew_status.radiation_exposure + round(18.0 * sev_mult, 1)
        )
        feedback = "Maintained standard operations during the solar storm. Radiation exposure increased."
        edu = "On the Moon, there is no thick atmosphere to block solar storms—shielding is essential for astronaut safety!"

    elif choice_id == "dispatch_dust_sweep":
        if res.power < 6.0 or res.oxygen < 3.0:
            raise ValueError("Requires at least 6 Power and 3 Oxygen for an astronaut dust-sweep EVA!")
        res.power = clamp_resource(res.power - 6.0)
        res.oxygen = clamp_resource(res.oxygen - 3.0)
        sub.solar_efficiency = min(config.MAX_SOLAR_EFFICIENCY, 1.05)
        state.science_points += 8
        feedback = "Astronauts brushed lunar dust off the solar panels! Efficiency restored to 105% (+8 Science Points)."
        edu = "Real Apollo astronauts discovered that sharp, statically charged Moon dust sticks to everything—especially solar panels!"

    elif choice_id == "postpone_sweep":
        sub.solar_efficiency = round(
            max(config.MIN_SOLAR_EFFICIENCY, sub.solar_efficiency - 0.20), 2
        )
        feedback = "Dust sweep postponed. Solar panel output dropped by 20%."
        edu = "Dusty solar panels generate less electricity each day until astronauts clean or repair them."

    elif choice_id == "fix_greenhouse_nozzle":
        if res.power < 7.0 or res.water < 3.0:
            raise ValueError("Requires 7 Power and 3 Water to repair and flush the greenhouse misting nozzle!")
        res.power = clamp_resource(res.power - 7.0)
        res.water = clamp_resource(res.water - 3.0)
        res.food = clamp_resource(res.food + 8.0)
        sub.greenhouse_active = True
        feedback = "Greenhouse misting nozzle repaired! Crops saved (+8 Food)."
        edu = "Plants in lunar hydroponics get water and nutrients sprayed right onto their roots instead of using heavy Earth soil."

    elif choice_id == "shut_down_affected_tray":
        res.food = clamp_resource(res.food - round(10.0 * sev_mult, 1))
        sub.greenhouse_growth_days = 0
        feedback = "Affected crop tray shut down. Lost 10 Food units and reset current harvest timer."
        edu = "Conserving power and water sometimes means sacrificing a crop batch—plan ahead so food doesn't run out!"

    elif choice_id == "replace_water_seal":
        if res.power < 8.0:
            raise ValueError("Requires 8 Power to run diagnostics and seal the water recovery pump!")
        res.power = clamp_resource(res.power - 8.0)
        res.water = clamp_resource(res.water + 8.0)
        sub.water_recovery_active = True
        feedback = "Spare seal installed! Water Recovery restored (+8 Water)."
        edu = "Every drop of water on the Moon is precious—fixing leaks fast protects your whole crew!"

    elif choice_id == "accept_water_rationing":
        res.water = clamp_resource(res.water - round(12.0 * sev_mult, 1))
        sub.water_recovery_active = False
        feedback = "Water rationing enacted (-12 Water, Water Recovery offline)."
        edu = "Without water recycling, astronauts use up stored drinking water much faster!"

    elif choice_id == "realign_dish":
        if res.power < 6.0:
            raise ValueError("Requires 6 Power to drive the antenna alignment motors!")
        res.power = clamp_resource(res.power - 6.0)
        state.science_points += 10
        feedback = "High-gain antenna realigned with Earth! (+10 Science Points)."
        edu = "Keeping your antenna aimed straight at Earth lets you send science discoveries home!"

    elif choice_id == "use_low_gain_backup":
        state.science_points = max(0, state.science_points - 5)
        feedback = "Switched to low-gain backup radio (-5 Science Points, 0 Power spent)."
        edu = "Backup radios use less electricity, though they transmit much less science data back to Earth."

    else:
        raise ValueError(f"Unknown decision option '{choice_id}' for event '{event_id}'.")

    selected_decision = next(
        option for option in target.decisions if option.choice_id == choice_id
    )
    state.mission_decisions.append(
        MissionDecisionRecord(
            day=state.current_day,
            decision_type="mission_event",
            subject=target.name,
            choice=selected_decision.label,
            source_label=(
                "REAL NASA DATA"
                if target.source_type == "NASA"
                else target.label
            ),
            consequence=feedback,
            lesson=edu,
        )
    )
    target.resolved = True
    state.active_events = [e for e in state.active_events if not e.resolved]
    return feedback, edu


def resolve_nasa_training_event_decision(
    state: GameState, event_id: str, choice_id: str
) -> Tuple[str, str]:
    """Resolve an optional NASA-informed lesson without entering the active event queue."""
    target = next(
        (
            event
            for event in state.nasa_training_events
            if event.event_id == event_id and not event.resolved
        ),
        None,
    )
    if target is None:
        raise ValueError(
            f"Training event '{event_id}' was not found or is already resolved."
        )
    decision = next(
        (option for option in target.decisions if option.choice_id == choice_id),
        None,
    )
    if decision is None:
        raise ValueError(
            f"Decision option '{choice_id}' is not available for training event '{event_id}'."
        )

    resources = state.resources
    for resource_name, required in decision.required_resources.items():
        if getattr(resources, resource_name) < required:
            raise ValueError(
                f"Not enough {resource_name.title()} for this training choice "
                f"(requires {required:g} simulated units)."
            )

    before = {
        "power": resources.power,
        "water": resources.water,
        "oxygen": resources.oxygen,
        "food": resources.food,
        "shield": resources.shield,
        "radiation_exposure": state.crew_status.radiation_exposure,
        "science_points": state.science_points,
        "power_allocation.radiation_shelter": state.power_allocation.radiation_shelter,
        "power_allocation.scientific_research": state.power_allocation.scientific_research,
    }

    if choice_id == "environment_power_plan":
        resources.power = clamp_resource(resources.power - 2.0)
        state.science_points += 3
    elif choice_id == "environment_terrain_review":
        resources.power = clamp_resource(resources.power - 3.0)
        state.science_points += 4
    elif choice_id == "environment_keep_plan":
        state.science_points += 1
    elif choice_id == "space_weather_shelter":
        feedback, _ = activate_radiation_shelter(state, charge_power=True)
    elif choice_id == "space_weather_pause_activity":
        state.science_points = max(0, state.science_points - 2)
    elif choice_id == "space_weather_monitor":
        resources.power = clamp_resource(resources.power - 2.0)
        state.science_points += 3
    elif choice_id == "communication_wait":
        resources.power = clamp_resource(resources.power - 2.0)
        state.science_points += 2
    elif choice_id == "communication_autonomous":
        state.science_points += 3
    elif choice_id == "communication_schedule":
        resources.power = clamp_resource(resources.power - 1.0)
        state.science_points += 1
    else:
        raise ValueError(
            f"Unknown decision option '{choice_id}' for training event '{event_id}'."
        )

    after = {
        "power": resources.power,
        "water": resources.water,
        "oxygen": resources.oxygen,
        "food": resources.food,
        "shield": resources.shield,
        "radiation_exposure": state.crew_status.radiation_exposure,
        "science_points": state.science_points,
        "power_allocation.radiation_shelter": state.power_allocation.radiation_shelter,
        "power_allocation.scientific_research": state.power_allocation.scientific_research,
    }
    target.resource_changes = {
        key: round(after[key] - value, 2)
        for key, value in before.items()
        if after[key] != value
    }
    target.resolved = True
    target.selected_choice_id = choice_id
    target.decision_rationale = decision.rationale
    target.result_message = (
        "SIMULATED GAME CONSEQUENCE: "
        + (
            feedback
            if choice_id == "space_weather_shelter"
            else decision.consequence_text
        )
    )
    if choice_id == "space_weather_shelter":
        target.result_message += (
            " Any changes to game indicators are simulated, not NASA measurements."
        )
        educational_note = (
            "The real NASA event metadata does not provide lunar radiation dosimetry. "
            "The shelter's game effects are simulated."
        )
    else:
        educational_note = (
            "This is a fictional training outcome. Resource and Science point "
            "changes are simulated game values, not NASA measurements."
        )
    state.mission_decisions.append(
        MissionDecisionRecord(
            day=state.current_day,
            decision_type="training_event",
            subject=target.title,
            choice=decision.label,
            source_label=target.label,
            consequence=target.result_message,
            lesson=decision.rationale or educational_note,
        )
    )
    return target.result_message, educational_note
