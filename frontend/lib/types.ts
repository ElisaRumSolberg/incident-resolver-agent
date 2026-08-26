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

export interface SimilarIncident {
  incident_id: string;
  service_id: string;
  root_cause: string;
  action: string | null;
  result: string;
  similarity: number;
}

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
  rejected_actions: string[];
  similar_incidents: SimilarIncident[];
}

export interface OverviewStats {
  active_count: number;
  resolved_today: number;
  resolved_total: number;
  avg_recovery_seconds: number | null;
  auto_resolved_rate: number;
  awaiting_approval_count: number;
  incidents_learned_from: number;
}

export interface RootCauseCategory {
  category: string;
  percent: number;
}

export interface RemediationSuccessRate {
  action: string;
  success_rate: number;
  attempts: number;
}

export interface AnalyticsData {
  top_root_causes: RootCauseCategory[];
  remediation_success_rate: RemediationSuccessRate[];
}

export interface SafetyStats {
  auto_executed: number;
  approved: number;
  rejected: number;
  awaiting_approval: number;
  blocked: number;
}

export interface Postmortem {
  incident_id: string;
  service_id: string;
  summary: string;
  recovery_seconds: number | null;
  root_cause: string | null;
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
