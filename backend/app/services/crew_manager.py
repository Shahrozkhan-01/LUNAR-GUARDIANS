"""
LUNAR GUARDIANS — Crew Management System.

Evaluates crew condition (Healthy, Warning, Critical), resource availability,
simulated radiation indicator, and friendly educational explanations for ages 7–12.
"""

from typing import List
from app import config
from app.models.schemas import (
    AvailabilityType,
    CrewMemberStatus,
    CrewStatus,
    HealthConditionType,
    ResourcesState,
)


def _classify_availability(amount: float) -> AvailabilityType:
    if amount <= config.CRITICAL_RESOURCE_THRESHOLD:
        return "Depleted" if amount <= 0.0 else "Low"
    if amount <= config.WARNING_RESOURCE_THRESHOLD:
        return "Low"
    return "Adequate"


def _classify_radiation_level(exposure: float) -> str:
    if exposure >= config.CRITICAL_RADIATION_THRESHOLD:
        return "High"
    if exposure >= config.WARNING_RADIATION_THRESHOLD:
        return "Moderate"
    return "Low"


def build_initial_crew_status(crew_size: int) -> CrewStatus:
    members = [
        CrewMemberStatus(
            id=i + 1,
            name=f"Astronaut #{i + 1:02d}",
            role=config.CREW_ROLE_TITLES[i % len(config.CREW_ROLE_TITLES)],
            condition="Healthy",
        )
        for i in range(crew_size)
    ]
    return CrewStatus(
        crew_size=crew_size,
        general_health="Healthy",
        oxygen_availability="Adequate",
        water_availability="Adequate",
        food_availability="Adequate",
        radiation_exposure=0.0,
        radiation_level="Low",
        critical_days_streak=0,
        educational_explanations=[
            "All astronauts are healthy and ready for lunar outpost duties!"
        ],
        members=members,
    )


def update_crew_condition(
    crew_status: CrewStatus, resources: ResourcesState
) -> List[str]:
    """
    Update crew health category, availability indicators, and educational explanations
    based on current simulated resources and radiation exposure.
    """
    explanations: List[str] = []

    o2_avail = _classify_availability(resources.oxygen)
    water_avail = _classify_availability(resources.water)
    food_avail = _classify_availability(resources.food)
    rad_level = _classify_radiation_level(crew_status.radiation_exposure)

    # Determine overall educational health category
    is_critical = (
        resources.oxygen <= config.CRITICAL_RESOURCE_THRESHOLD
        or resources.water <= config.CRITICAL_RESOURCE_THRESHOLD
        or resources.food <= 5.0
        or crew_status.radiation_exposure >= config.CRITICAL_RADIATION_THRESHOLD
    )
    is_warning = (
        not is_critical
        and (
            resources.oxygen <= config.WARNING_RESOURCE_THRESHOLD
            or resources.water <= config.WARNING_RESOURCE_THRESHOLD
            or resources.food <= config.WARNING_RESOURCE_THRESHOLD
            or crew_status.radiation_exposure >= config.WARNING_RADIATION_THRESHOLD
        )
    )

    if is_critical:
        health: HealthConditionType = "Critical"
        crew_status.critical_days_streak += 1
    elif is_warning:
        health = "Warning"
        crew_status.critical_days_streak = 0
    else:
        health = "Healthy"
        crew_status.critical_days_streak = 0

    # Kid-friendly educational explanations
    if resources.oxygen <= config.CRITICAL_RESOURCE_THRESHOLD:
        explanations.append(
            "Your crew needs oxygen to breathe. The life-support system is not producing enough oxygen!"
        )
    elif resources.oxygen <= config.WARNING_RESOURCE_THRESHOLD:
        explanations.append(
            "Oxygen is running low! Give Life Support plenty of power and keep Oxygen Recycling active."
        )

    if resources.water <= config.CRITICAL_RESOURCE_THRESHOLD:
        explanations.append(
            "Clean drinking water is critically low! Activate Water Recovery right away to keep your astronauts hydrated."
        )
    elif resources.water <= config.WARNING_RESOURCE_THRESHOLD:
        explanations.append(
            "Water supplies are getting low. Recycling water helps astronauts survive on the Moon!"
        )

    if resources.food <= config.CRITICAL_RESOURCE_THRESHOLD:
        explanations.append(
            "Food rations are nearly empty! Power and water your Greenhouse so your astronauts have energy to work."
        )
    elif resources.food <= config.WARNING_RESOURCE_THRESHOLD:
        explanations.append(
            "Food supplies are dipping. Make sure the Greenhouse stays active for your next crop harvest."
        )

    if crew_status.radiation_exposure >= config.CRITICAL_RADIATION_THRESHOLD:
        explanations.append(
            "Simulated radiation exposure is dangerously high! Activate the Radiation Shelter immediately to protect your crew."
        )
    elif crew_status.radiation_exposure >= config.WARNING_RADIATION_THRESHOLD:
        explanations.append(
            "Radiation shelters use power, but they help protect astronauts during solar storm events."
        )

    if not explanations:
        explanations.append(
            "Your astronauts are healthy! Oxygen, water, food, and radiation shielding are all in safe ranges."
        )

    crew_status.general_health = health
    crew_status.oxygen_availability = o2_avail
    crew_status.water_availability = water_avail
    crew_status.food_availability = food_avail
    crew_status.radiation_level = rad_level  # type: ignore[assignment]
    crew_status.educational_explanations = explanations

    # Update individual crew member indicators
    for idx, member in enumerate(crew_status.members):
        if health == "Critical":
            member.condition = "Critical"
        elif health == "Warning":
            # Stagger warning slightly across crew for realistic visual feedback
            member.condition = "Warning" if idx % 2 == 0 else "Healthy"
        else:
            member.condition = "Healthy"

    return explanations
