from typing import Literal, Optional

from pydantic import BaseModel, Field

Risk = Literal["low", "medium", "high"]
IncidentStatus = Literal[
    "investigating",
    "awaiting_approval",
    "remediating",
    "verifying",
    "resolved",
    "escalation_required",
    "failed",
]
RemediationStatus = Literal[
    "proposed",
    "awaiting_approval",
    "approved",
    "rejected",
    "applied",
    "verified",
    "failed",
    "blocked",
]


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


class IncidentEvent(BaseModel):
    id: str
    incident_id: str
    type: str
    message: str
    created_at: str


class RemediationRecord(BaseModel):
    id: str
    incident_id: str
    action: str
    risk: Risk
    status: RemediationStatus
    reason: Optional[str] = None
    verified: bool = False
