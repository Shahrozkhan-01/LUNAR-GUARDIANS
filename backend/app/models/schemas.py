"""
LUNAR GUARDIANS — Pydantic Request & Response Schemas.

All gameplay units are clearly typed and labeled as SIMULATED GAME UNITS.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


DifficultyType = Literal["explorer", "commander", "expert"]
MissionStatusType = Literal[
    "In Progress",
    "Mission Successful",
    "Mission Completed with Difficulties",
    "Mission Failed",
]
HealthConditionType = Literal["Healthy", "Warning", "Critical"]
AvailabilityType = Literal["Adequate", "Low", "Depleted"]


class ResourcesState(BaseModel):
    unit_label: str = "SIMULATED GAME UNITS"
    oxygen: float = Field(..., ge=0.0, le=100.0)
    water: float = Field(..., ge=0.0, le=100.0)
    power: float = Field(..., ge=0.0, le=100.0)
    food: float = Field(..., ge=0.0, le=100.0)
    shield: float = Field(..., ge=0.0, le=100.0)


class PowerAllocation(BaseModel):
    life_support: float = Field(..., ge=0.0, le=100.0)
    radiation_shelter: float = Field(..., ge=0.0, le=100.0)
    greenhouse: float = Field(..., ge=0.0, le=100.0)
    communication: float = Field(..., ge=0.0, le=100.0)
    scientific_research: float = Field(..., ge=0.0, le=100.0)

    def total(self) -> float:
        return round(
            self.life_support
            + self.radiation_shelter
            + self.greenhouse
            + self.communication
            + self.scientific_research,
            2,
        )


class SubsystemStatus(BaseModel):
    oxygen_recycling_active: bool = True
    water_recovery_active: bool = True
    greenhouse_active: bool = True
    greenhouse_growth_days: int = 0
    radiation_shelter_active: bool = False
    shelter_boost_days_left: int = 0
    research_active: bool = False
    research_days_left: int = 0
    conservation_mode_days_left: int = 0
    solar_efficiency: float = 1.0


class CrewMemberStatus(BaseModel):
    id: int
    name: str
    role: str
    condition: HealthConditionType


class CrewStatus(BaseModel):
    data_label: str = "SIMULATED GAME INDICATORS"
    crew_size: int
    general_health: HealthConditionType
    oxygen_availability: AvailabilityType
    water_availability: AvailabilityType
    food_availability: AvailabilityType
    radiation_exposure: float = Field(..., ge=0.0, le=100.0)
    radiation_level: Literal["Low", "Moderate", "High"]
    critical_days_streak: int = 0
    educational_explanations: List[str] = Field(default_factory=list)
    members: List[CrewMemberStatus] = Field(default_factory=list)


class EventDecisionOption(BaseModel):
    choice_id: str
    label: str
    cost_text: str
    consequence_text: str
    rationale: Optional[str] = None
    required_resources: Dict[str, float] = Field(default_factory=dict)


class NasaTrainingDataContext(BaseModel):
    dataset_id: str
    data_label: Literal["REAL NASA DATA", "COMPUTED EPHEMERIS", "DERIVED VALUE"]
    dataset_name: str
    source: str
    source_url: Optional[str] = None
    measurement: str
    value: str
    unit: Optional[str] = None
    date_or_coverage: Optional[str] = None
    note: Optional[str] = None


class NasaTrainingEvent(BaseModel):
    event_id: str
    category: Literal[
        "south_polar_environment",
        "space_weather_preparedness",
        "earth_moon_communication",
    ]
    label: str = "SIMULATED TRAINING EVENT"
    consequence_label: str = "SIMULATED GAME CONSEQUENCE"
    title: str
    description: str
    scientific_context: str
    data_availability: Literal["available", "partial", "unavailable"]
    data_unavailable_note: Optional[str] = None
    data_context: List[NasaTrainingDataContext] = Field(default_factory=list)
    scientific_limitations: List[str] = Field(default_factory=list)
    decisions: List[EventDecisionOption] = Field(default_factory=list)
    day_triggered: int
    resolved: bool = False
    selected_choice_id: Optional[str] = None
    result_message: Optional[str] = None
    decision_rationale: Optional[str] = None
    resource_changes: Dict[str, float] = Field(default_factory=dict)


class SimulatedEvent(BaseModel):
    event_id: str
    label: str = "SIMULATED TRAINING EVENT"
    source_type: Literal["SIMULATED", "NASA"] = "SIMULATED"
    source_event_type: Optional[str] = None
    source_event_id: Optional[str] = None
    source_event_time: Optional[str] = None
    source_url: Optional[str] = None
    event_category: Optional[str] = None
    educational_explanation: Optional[str] = None
    mission_situation: Optional[str] = None
    consequence_label: str = "SIMULATED GAME CONSEQUENCE"
    name: str
    description: str
    severity: Literal["low", "medium", "high"]
    day_triggered: int
    resolved: bool = False
    decisions: List[EventDecisionOption] = Field(default_factory=list)


class PlayerActionDefinition(BaseModel):
    id: str
    name: str
    description: str
    cost: Dict[str, float]
    benefit_summary: str
    duration_days: Optional[int] = None


class ActivityLogEntry(BaseModel):
    id: str
    day: int
    category: Literal["info", "action", "event", "warning", "outcome"] = "info"
    message: str


class MissionDecisionRecord(BaseModel):
    day: int
    decision_type: Literal["mission_event", "training_event", "outpost_action"]
    subject: str
    choice: str
    source_label: str
    consequence_label: str = "SIMULATED GAME CONSEQUENCE"
    consequence: str
    lesson: str


class MissionEventRecord(BaseModel):
    day: int
    title: str
    source_label: str
    description: str
    event_type: Optional[str] = None
    source_event_id: Optional[str] = None


class StartMissionRequest(BaseModel):
    destination: str = "lunar-outpost"
    difficulty: DifficultyType = "commander"
    crew_size: Literal[2, 4, 6] = 4
    duration: Literal[5, 10, 15] = 10
    mission_name: Optional[str] = "Lunar Outpost Alpha"
    deterministic: bool = False
    enable_random_events: bool = True
    seed: Optional[int] = None


class PowerUpdateRequest(BaseModel):
    life_support: float = Field(..., ge=0.0, le=100.0)
    radiation_shelter: float = Field(..., ge=0.0, le=100.0)
    greenhouse: float = Field(..., ge=0.0, le=100.0)
    communication: float = Field(..., ge=0.0, le=100.0)
    scientific_research: float = Field(..., ge=0.0, le=100.0)


class ExecuteActionRequest(BaseModel):
    action_id: str
    event_id: Optional[str] = None
    choice_id: Optional[str] = None


class GameState(BaseModel):
    mission_id: str
    data_notice: str = (
        "NASA DONKI observations are real; all gameplay values and consequences "
        "are simulated game units."
    )
    mission_name: str
    destination: str
    difficulty: DifficultyType
    crew_size: int
    duration: int
    current_day: int
    mission_status: MissionStatusType
    outcome_explanation: Optional[str] = None
    science_points: int = 0
    deterministic: bool = False
    enable_random_events: bool = True
    seed: int = 42
    resources: ResourcesState
    power_allocation: PowerAllocation
    subsystems: SubsystemStatus
    crew_status: CrewStatus
    active_events: List[SimulatedEvent] = Field(default_factory=list)
    nasa_training_events: List[NasaTrainingEvent] = Field(default_factory=list)
    mission_decisions: List[MissionDecisionRecord] = Field(default_factory=list)
    mission_events: List[MissionEventRecord] = Field(default_factory=list)
    seen_nasa_event_ids: List[str] = Field(default_factory=list)
    available_actions: List[PlayerActionDefinition] = Field(default_factory=list)
    educational_tips: List[str] = Field(default_factory=list)
    activity_log: List[ActivityLogEntry] = Field(default_factory=list)


class ActionResponse(BaseModel):
    action_name: str
    feedback_message: str
    educational_note: str
    game_state: GameState


class AdvanceDayResponse(BaseModel):
    day_summary: str
    educational_notes: List[str]
    game_state: GameState


class EventsListResponse(BaseModel):
    mission_id: str
    notice: str = "NASA observations are real; gameplay event consequences are simulated."
    active_events: List[SimulatedEvent]
