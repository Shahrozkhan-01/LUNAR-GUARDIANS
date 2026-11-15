"""
LUNAR GUARDIANS — Resource Management Engine.

Handles all daily resource consumption, production, recycling, solar generation,
and priority-based power load-shedding using configurable constants from app.config.
"""

from typing import Dict, List, Tuple
from app import config
from app.models.schemas import GameState, PowerAllocation, PowerUpdateRequest


def clamp_resource(value: float) -> float:
    """Ensure resource values remain strictly within [MIN_RESOURCE, MAX_RESOURCE]."""
    return round(max(config.MIN_RESOURCE, min(config.MAX_RESOURCE, value)), 1)


def validate_power_allocation(
    request: PowerUpdateRequest, available_power: float
) -> Tuple[bool, str, List[str]]:
    """
    Validate that total requested power allocation does not exceed available power.
    Returns (is_valid, message, educational_notes).
    """
    total_requested = round(
        request.life_support
        + request.radiation_shelter
        + request.greenhouse
        + request.communication
        + request.scientific_research,
        1,
    )

    if total_requested > round(available_power + 1e-6, 1):
        return (
            False,
            (
                f"Total allocated electricity ({total_requested} units) cannot exceed "
                f"your available battery power ({available_power} units)."
            ),
            [
                "Try lowering power to Scientific Research or Greenhouse first so Life Support stays funded!"
            ],
        )

    notes: List[str] = []
    if request.life_support < config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING:
        notes.append(
            "Warning: Life Support has very low power! Oxygen and water recycling need at least "
            f"{int(config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING)} power units to work properly."
        )
    elif request.life_support < config.OPTIMAL_LIFE_SUPPORT_POWER:
        notes.append(
            "Tip: Giving Life Support at least 25 power units helps produce steady breathable oxygen."
        )

    if request.greenhouse > 0 and request.greenhouse < config.MIN_GREENHOUSE_POWER:
        notes.append(
            f"Your greenhouse needs at least {int(config.MIN_GREENHOUSE_POWER)} electricity units for its grow-lights to grow food."
        )

    return True, "Power allocation updated successfully.", notes


def compute_effective_power_distribution(
    available_power_pool: float,
    allocation: PowerAllocation,
    conservation_active: bool,
) -> Tuple[Dict[str, float], float, List[str]]:
    """
    Distribute electricity strictly in operational priority order:
    1. Life Support -> 2. Radiation Shelter -> 3. Greenhouse -> 4. Communication -> 5. Scientific Research.

    If available electricity is insufficient, lower-priority systems are reduced or shut down first.
    """
    remaining = max(0.0, available_power_pool)
    effective: Dict[str, float] = {}
    notes: List[str] = []

    for sys_key in config.POWER_PRIORITY_ORDER:
        requested = getattr(allocation, sys_key)

        if conservation_active:
            if sys_key == "scientific_research":
                requested = 0.0
            elif sys_key in ("greenhouse", "communication"):
                requested = round(requested * config.CONSERVATION_NON_ESSENTIAL_POWER_FACTOR, 1)

        granted = round(min(requested, remaining), 1)
        effective[sys_key] = granted
        remaining = round(max(0.0, remaining - granted), 1)

        if requested > 0 and granted < requested:
            pretty_name = sys_key.replace("_", " ").title()
            if granted == 0:
                notes.append(
                    f"Low electricity! {pretty_name} was temporarily shut down so higher-priority systems like Life Support could stay online."
                )
            else:
                notes.append(
                    f"Low electricity! {pretty_name} received reduced power ({granted}/{requested} units) to protect Life Support."
                )

    total_used = round(sum(effective.values()), 1)
    return effective, total_used, notes


def process_daily_resources(state: GameState) -> Tuple[List[str], int]:
    """
    Execute daily solar generation, power consumption, crew resource consumption,
    recycling, greenhouse food harvest, and research point generation.
    Mutates state.resources, state.subsystems, and returns (educational_notes, science_gained).
    """
    notes: List[str] = []
    science_gained: int = 0

    diff_cfg = config.DIFFICULTY_SETTINGS[state.difficulty]
    cons_mult = diff_cfg["consumption_multiplier"]
    crew = state.crew_size
    sub = state.subsystems
    res = state.resources

    # 1. Solar Power Generation
    solar_generated = round(
        config.BASE_DAILY_SOLAR_GENERATION * sub.solar_efficiency, 1
    )
    power_pool = res.power + solar_generated

    # 2. Priority Power Allocation & Consumption (Systems 5, 6, 7, 8 + Research)
    conservation_on = sub.conservation_mode_days_left > 0
    effective_power, total_power_used, power_notes = compute_effective_power_distribution(
        available_power_pool=power_pool,
        allocation=state.power_allocation,
        conservation_active=conservation_on,
    )
    notes.extend(power_notes)

    new_power = clamp_resource(power_pool - total_power_used)

    ls_power = effective_power["life_support"]
    shelter_power = effective_power["radiation_shelter"]
    gh_power = effective_power["greenhouse"]
    comm_power = effective_power["communication"]
    research_power = effective_power["scientific_research"]

    # 3. Daily Oxygen Consumption & Recycling
    base_o2_use = crew * config.DAILY_OXYGEN_PER_ASTRONAUT * cons_mult
    if not sub.oxygen_recycling_active or ls_power < config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING:
        base_o2_use *= config.NO_OXYGEN_RECYCLING_PENALTY_MULTIPLIER

    ls_o2_generated = ls_power * config.LIFE_SUPPORT_OXYGEN_PER_POWER
    o2_recycled = (
        config.OXYGEN_RECYCLING_DAILY_RECOVERY
        if (sub.oxygen_recycling_active and ls_power >= config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING)
        else 0.0
    )
    if ls_power < config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING:
        notes.append(
            "Oxygen is dropping faster because Life Support does not have enough electricity to run Oxygen Recycling!"
        )

    new_oxygen = clamp_resource(res.oxygen - base_o2_use + ls_o2_generated + o2_recycled)

    # 4. Daily Water Consumption & Recycling
    base_water_use = crew * config.DAILY_WATER_PER_ASTRONAUT * cons_mult
    if not sub.water_recovery_active or ls_power < config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING:
        base_water_use *= config.NO_WATER_RECOVERY_PENALTY_MULTIPLIER

    water_recycled = (
        config.WATER_RECOVERY_DAILY_RECOVERY
        if (sub.water_recovery_active and ls_power >= config.MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING)
        else 0.0
    )
    working_water = res.water - base_water_use + water_recycled

    # 5. Daily Food Consumption & Greenhouse Production
    base_food_use = crew * config.DAILY_FOOD_PER_ASTRONAUT * cons_mult
    working_food = res.food - base_food_use

    if sub.greenhouse_active:
        if gh_power >= config.MIN_GREENHOUSE_POWER and working_water >= config.GREENHOUSE_DAILY_WATER_USE:
            working_water -= config.GREENHOUSE_DAILY_WATER_USE
            sub.greenhouse_growth_days += 1
            if sub.greenhouse_growth_days >= config.GREENHOUSE_HARVEST_INTERVAL_DAYS:
                working_food += config.GREENHOUSE_FOOD_HARVEST_AMOUNT
                sub.greenhouse_growth_days = 0
                notes.append(
                    f"Greenhouse harvest ready! Your crew harvested +{int(config.GREENHOUSE_FOOD_HARVEST_AMOUNT)} fresh food units."
                )
        else:
            notes.append(
                "Your greenhouse needs electricity and water before it can produce food."
            )

    new_water = clamp_resource(working_water)
    new_food = clamp_resource(working_food)

    # 6. Radiation Shelter & Shield Protection
    shelter_powered = (
        (sub.radiation_shelter_active or sub.shelter_boost_days_left > 0)
        and shelter_power >= config.MIN_SHELTER_POWER
    )
    if shelter_powered:
        new_shield = clamp_resource(res.shield + config.SHELTER_ACTIVE_SHIELD_GAIN)
        state.crew_status.radiation_exposure = clamp_resource(
            state.crew_status.radiation_exposure - config.SHELTER_RADIATION_REDUCTION
        )
    else:
        # Gentle passive adjustment depending on allocated shelter standby power
        shield_delta = (
            2.0 if shelter_power >= config.MIN_SHELTER_POWER else -config.SHELTER_PASSIVE_SHIELD_DECAY
        )
        new_shield = clamp_resource(res.shield + shield_delta)
        if new_shield < 40.0:
            state.crew_status.radiation_exposure = clamp_resource(
                state.crew_status.radiation_exposure + config.BASE_DAILY_RADIATION_DRIFT
            )

    # 7. Communication & Scientific Research
    if comm_power >= config.MIN_COMMUNICATION_POWER:
        science_gained += config.COMMUNICATION_DAILY_SCIENCE_BONUS
    else:
        notes.append(
            "Communication antenna has low power. Keep it powered to maintain full Earth telemetry!"
        )

    has_severe_storm = any(
        e.severity == "high" and not e.resolved for e in state.active_events
    )
    if conservation_on:
        notes.append(
            "Emergency Conservation Mode is active: non-essential electricity use was reduced and Scientific Research paused."
        )
    elif has_severe_storm and not shelter_powered:
        notes.append(
            "Scientific Research paused while crew responds to an unshielded solar storm alert!"
        )
    elif research_power >= config.MIN_RESEARCH_POWER:
        pts = config.RESEARCH_DAILY_SCIENCE_POINTS + (4 if sub.research_active else 0)
        science_gained += pts

    # Save clamped resources back to state
    res.oxygen = new_oxygen
    res.water = new_water
    res.power = new_power
    res.food = new_food
    res.shield = new_shield

    # If battery dropped below current power_allocation sum, proportionally trim lowest-priority allocations
    if state.power_allocation.total() > res.power:
        excess = round(state.power_allocation.total() - res.power, 1)
        for sys_key in reversed(config.POWER_PRIORITY_ORDER):
            if excess <= 0:
                break
            current_val = getattr(state.power_allocation, sys_key)
            cut = min(current_val, excess)
            setattr(state.power_allocation, sys_key, round(current_val - cut, 1))
            excess = round(excess - cut, 1)

    return notes, science_gained
