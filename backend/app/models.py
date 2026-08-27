from typing import Literal, Optional

from pydantic import BaseModel, Field

Risk = Literal["low", "medium", "high"]
IncidentStatus = Literal[
    "investigating",
    "recommended",  # observe_only / recommend_only modes: diagnosed, never executed
    "awaiting_approval",
    "remediating",
    "verifying",
    "resolved",
    "escalation_required",
    "failed",
]
RemediationStatus = Literal[
    "proposed",  # recommend-only: surfaced but will never be executed
    "awaiting_approval",
    "approved",
    "rejected",
    "applied",
    "verified",
    "failed",
    "blocked",
]
AutonomyMode = Literal["observe_only", "recommend_only", "approval_required", "autonomous_low_risk"]
PolicyDecision = Literal["auto_execute", "requires_approval", "blocked", "recommend_only"]
Actor = Literal["agent", "human", "safety_engine", "monitoring_system"]
Criticality = Literal["low", "medium", "high", "critical"]
Environment = Literal["development", "staging", "production"]

POLICY_VERSION = "v2"


class HealthResult(BaseModel):
    status: Literal["healthy", "unhealthy"]
    checks: dict
    revision: Optional[str] = None
    timestamp: str


class LogEntry(BaseModel):
    id: str
    timestamp: str
    level: str
    message: str


class ErrorPattern(BaseModel):
    pattern: str
    count: int
    level: str
    confidence: float


class ConfigSnapshot(BaseModel):
    revision: Optional[str] = None
    details: dict = Field(default_factory=dict)


class RemediationProposal(BaseModel):
    root_cause: str
    confidence: float
    severity: Literal["low", "medium", "high", "critical"]
    action: str
    reason: str


class Incident(BaseModel):
    id: str
    service_id: str
    status: IncidentStatus
    severity: Optional[str] = None
    root_cause: Optional[str] = None
    confidence: Optional[float] = None
    started_at: str
    resolved_at: Optional[str] = None
    current_hypothesis: Optional[str] = None
    next_action: Optional[str] = None
    attempted_actions: list[str] = Field(default_factory=list)
    rejected_actions: list[str] = Field(default_factory=list)
    similar_incidents: list[dict] = Field(default_factory=list)
    autonomy_mode: Optional[AutonomyMode] = None  # the mode active when this incident was opened
    tools_used: list[str] = Field(default_factory=list)


class IncidentEvent(BaseModel):
    id: str
    incident_id: str
    type: str
    message: str
    created_at: str
    actor: Actor = "agent"


class RemediationRecord(BaseModel):
    id: str
    incident_id: str
    service_id: Optional[str] = None
    action: str
    risk: Risk
    status: RemediationStatus
    reason: Optional[str] = None
    verified: bool = False
    created_at: Optional[str] = None
    # Audit trail
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    executed_by: Optional[Actor] = None
    execution_id: Optional[str] = None
    policy_decision: Optional[PolicyDecision] = None
    policy_version: Optional[str] = None
    policy_reason: Optional[str] = None


class PolicyEvaluation(BaseModel):
    """The Safety Policy Engine's full verdict for one proposed action."""

    decision: PolicyDecision
    risk: Optional[Risk]
    reason: str
    policy_version: str = POLICY_VERSION


class GlobalSettings(BaseModel):
    autonomy_mode: AutonomyMode = "autonomous_low_risk"
    autonomy_mode_changed_at: Optional[str] = None
    autonomy_mode_changed_by: Optional[str] = None
    kill_switch_enabled: bool = False
    kill_switch_changed_at: Optional[str] = None
    kill_switch_changed_by: Optional[str] = None


class ServiceProfile(BaseModel):
    service_id: str
    criticality: Criticality = "medium"
    environment: Environment = "production"
    autonomy_level: AutonomyMode = "autonomous_low_risk"
    allowed_automatic_actions: list[str] = Field(default_factory=list)
    actions_requiring_approval: list[str] = Field(default_factory=list)
    action_risk_overrides: dict[str, Risk] = Field(default_factory=dict)
