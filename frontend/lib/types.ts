export type Risk = "low" | "medium" | "high";

export type IncidentStatus =
  | "investigating"
  | "awaiting_approval"
  | "remediating"
  | "verifying"
  | "resolved"
  | "escalation_required"
  | "failed";

export type RemediationStatus =
  | "proposed"
  | "awaiting_approval"
  | "approved"
  | "rejected"
  | "applied"
  | "verified"
  | "failed"
  | "blocked";

export interface Incident {
  id: string;
  service_id: string;
  status: IncidentStatus;
  severity: string | null;
  root_cause: string | null;
  confidence: number | null;
  started_at: string;
  resolved_at: string | null;
  current_hypothesis: string | null;
  next_action: string | null;
  attempted_actions: string[];
}

export interface Remediation {
  id: string;
  incident_id: string;
  action: string;
  risk: Risk;
  status: RemediationStatus;
  reason: string | null;
  verified: boolean;
}

export interface IncidentEvent {
  type: string;
  message: string;
  created_at: string;
}

export interface IncidentResponse {
  incident: Incident;
  remediations: Remediation[];
  events: IncidentEvent[];
}

export interface HealthySnapshot {
  status: "healthy";
  message: string;
}

export type StartIncidentResponse = IncidentResponse | HealthySnapshot;

export function isHealthySnapshot(r: StartIncidentResponse): r is HealthySnapshot {
  return (r as HealthySnapshot).status === "healthy" && !("incident" in r);
}
