"""
LUNAR GUARDIANS — Simulation Balancing Constants & Configuration.

All numerical values here represent fictional SIMULATED GAME UNITS designed for
educational gameplay (ages 7–12). None of these values represent real NASA
hardware specifications or astronaut medical measurements.
"""

from typing import Dict, Any

# Resource clamps (Simulated Game Units)
MIN_RESOURCE: float = 0.0
MAX_RESOURCE: float = 100.0

# Baseline starting resources (Commander / Standard baseline)
BASE_STARTING_RESOURCES: Dict[str, float] = {
    "oxygen": 100.0,
    "water": 100.0,
    "power": 100.0,
    "food": 100.0,
    "shield": 50.0,
}

# Difficulty modifiers affecting starting resources, consumption rate, and event severity
DIFFICULTY_SETTINGS: Dict[str, Dict[str, Any]] = {
    "explorer": {
        "label": "Explorer",
        "starting_resources": {
            "oxygen": 100.0,
            "water": 100.0,
            "power": 100.0,
            "food": 100.0,
            "shield": 65.0,
        },
        "consumption_multiplier": 0.82,
        "event_severity_multiplier": 0.75,
        "starting_science_points": 10,
    },
    "commander": {
        "label": "Commander",
        "starting_resources": {
            "oxygen": 100.0,
            "water": 100.0,
            "power": 100.0,
            "food": 100.0,
            "shield": 50.0,
        },
        "consumption_multiplier": 1.0,
        "event_severity_multiplier": 1.0,
        "starting_science_points": 0,
    },
    "expert": {
        "label": "Expert",
        "starting_resources": {
            "oxygen": 85.0,
            "water": 85.0,
            "power": 85.0,
            "food": 85.0,
            "shield": 40.0,
        },
        "consumption_multiplier": 1.15,
        "event_severity_multiplier": 1.25,
        "starting_science_points": 0,
    },
}

ALLOWED_CREW_SIZES = (2, 4, 6)
ALLOWED_DURATIONS = (5, 10, 15)

# Daily per-astronaut resource consumption (Simulated Game Units)
DAILY_OXYGEN_PER_ASTRONAUT: float = 3.0
DAILY_WATER_PER_ASTRONAUT: float = 2.6
DAILY_FOOD_PER_ASTRONAUT: float = 2.4

# Extra oxygen loss multiplier when oxygen recycling is turned OFF
NO_OXYGEN_RECYCLING_PENALTY_MULTIPLIER: float = 1.35
# Extra water loss multiplier when water recovery is turned OFF
NO_WATER_RECOVERY_PENALTY_MULTIPLIER: float = 1.30

# Solar power generation constants
BASE_DAILY_SOLAR_GENERATION: float = 68.0
INITIAL_SOLAR_EFFICIENCY: float = 1.0
MIN_SOLAR_EFFICIENCY: float = 0.45
MAX_SOLAR_EFFICIENCY: float = 1.20
SOLAR_REPAIR_EFFICIENCY_GAIN: float = 0.20

# Default power allocation (sum = 72, sustainable against 68 solar generation)
DEFAULT_POWER_ALLOCATION: Dict[str, float] = {
    "life_support": 26.0,
    "radiation_shelter": 12.0,
    "greenhouse": 14.0,
    "communication": 10.0,
    "scientific_research": 10.0,
}

# Power system priority order (highest operational priority first)
POWER_PRIORITY_ORDER = (
    "life_support",
    "radiation_shelter",
    "greenhouse",
    "communication",
    "scientific_research",
)

# Operational power thresholds (Simulated Game Units)
MIN_LIFE_SUPPORT_POWER_FOR_RECYCLING: float = 15.0
OPTIMAL_LIFE_SUPPORT_POWER: float = 25.0
LIFE_SUPPORT_OXYGEN_PER_POWER: float = 0.24
OXYGEN_RECYCLING_DAILY_RECOVERY: float = 5.5
WATER_RECOVERY_DAILY_RECOVERY: float = 5.2

MIN_GREENHOUSE_POWER: float = 12.0
GREENHOUSE_DAILY_WATER_USE: float = 3.5
GREENHOUSE_HARVEST_INTERVAL_DAYS: int = 2
GREENHOUSE_FOOD_HARVEST_AMOUNT: float = 18.0

MIN_SHELTER_POWER: float = 12.0
SHELTER_ACTIVE_SHIELD_GAIN: float = 7.0
SHELTER_PASSIVE_SHIELD_DECAY: float = 2.0
BASE_DAILY_RADIATION_DRIFT: float = 3.0
SHELTER_RADIATION_REDUCTION: float = 5.0

MIN_COMMUNICATION_POWER: float = 8.0
COMMUNICATION_DAILY_SCIENCE_BONUS: int = 3

MIN_RESEARCH_POWER: float = 10.0
RESEARCH_DAILY_SCIENCE_POINTS: int = 12

# Emergency conservation mode modifiers
CONSERVATION_NON_ESSENTIAL_POWER_FACTOR: float = 0.50
CONSERVATION_DURATION_DAYS: int = 2

# Player action definitions (costs, durations, benefits)
ACTION_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "activate_oxygen_recycling": {
        "id": "activate_oxygen_recycling",
        "name": "Activate Oxygen Recycling",
        "description": "Energize carbon-dioxide scrubbers to clean cabin air and recover breathable oxygen.",
        "cost": {"power": 6.0},
        "benefit_summary": "+4 Oxygen now and +5.5 Oxygen recovered per day while Life Support is powered.",
        "duration_days": None,
        "immediate_oxygen_gain": 4.0,
    },
    "activate_water_recovery": {
        "id": "activate_water_recovery",
        "name": "Activate Water Recovery",
        "description": "Run multi-filtration pumps to recycle cabin moisture and wastewater into clean water.",
        "cost": {"power": 6.0},
        "benefit_summary": "+4 Water now and +5.2 Water recycled per day while Life Support is powered.",
        "duration_days": None,
        "immediate_water_gain": 4.0,
    },
    "activate_greenhouse": {
        "id": "activate_greenhouse",
        "name": "Activate Greenhouse",
        "description": "Irrigate lunar hydroponic trays and turn on LED grow-lights to cultivate fresh food.",
        "cost": {"power": 7.0, "water": 4.0},
        "benefit_summary": "Produces +18 Food every 2 simulated growth days (uses daily water and electricity).",
        "duration_days": 2,
    },
    "activate_radiation_shelter": {
        "id": "activate_radiation_shelter",
        "name": "Activate Radiation Shelter",
        "description": "Boost protective shielding around the crew bay to block incoming space radiation.",
        "cost": {"power": 10.0},
        "benefit_summary": "+15 Shield Protection now and strong radiation protection for 3 days (may pause Research if power is tight).",
        "duration_days": 3,
        "immediate_shield_gain": 15.0,
    },
    "start_scientific_research": {
        "id": "start_scientific_research",
        "name": "Start Scientific Research",
        "description": "Analyze lunar rock samples and habitat experiments to earn Science Points.",
        "cost": {"power": 8.0},
        "benefit_summary": "+15 Science Points now and +12 Science Points/day while powered (suspended during conservation or severe storms).",
        "duration_days": 3,
        "immediate_science_gain": 15,
    },
    "emergency_conservation_mode": {
        "id": "emergency_conservation_mode",
        "name": "Enter Emergency Conservation Mode",
        "description": "Cut non-essential electricity use in half and pause Scientific Research to save battery reserves.",
        "cost": {"power": 0.0},
        "benefit_summary": "+10 Battery Power saved immediately and 50% lower non-essential power draw for 2 days (pauses Research).",
        "duration_days": 2,
        "immediate_power_saved": 10.0,
    },
    "repair_solar_panels": {
        "id": "repair_solar_panels",
        "name": "Repair Solar Panels",
        "description": "Send astronauts in spacesuits to brush off lunar dust and tune solar array wiring.",
        "cost": {"power": 8.0, "oxygen": 3.0},
        "benefit_summary": "Restores and boosts solar panel efficiency (+20%, up to 120%) for stronger daily electricity generation.",
        "duration_days": None,
    },
}

# Crew condition thresholds (Simulated Game Units)
WARNING_RESOURCE_THRESHOLD: float = 35.0
CRITICAL_RESOURCE_THRESHOLD: float = 15.0
WARNING_RADIATION_THRESHOLD: float = 40.0
CRITICAL_RADIATION_THRESHOLD: float = 75.0
MAX_RADIATION_FAILURE_LIMIT: float = 100.0
CONSECUTIVE_CRITICAL_DAYS_FOR_FAILURE: int = 2

CREW_ROLE_TITLES = (
    "Outpost Commander",
    "Life Support Engineer",
    "Lunar Botanist",
    "Power Grid Specialist",
    "Flight Medical Officer",
    "Surface Geologist",
)
