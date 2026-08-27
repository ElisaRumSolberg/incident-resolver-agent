export type Risk = "low" | "medium" | "high";

export type IncidentStatus =
  | "investigating"
  | "recommended"
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

export type AutonomyMode = "observe_only" | "recommend_only" | "approval_required" | "autonomous_low_risk";
export type PolicyDecision = "auto_execute" | "requires_approval" | "blocked" | "recommend_only";
export type Actor = "agent" | "human" | "safety_engine" | "monitoring_system";
export type Criticality = "low" | "medium" | "high" | "critical";
export type Environment = "development" | "staging" | "production";

export interface SimilarIncident {
  incident_id: string;
  service_id: string;
  root_cause: string;
  action: string | null;
  result: string;
  recovery_seconds?: number | null;
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
  autonomy_mode: AutonomyMode | null;
  tools_used: string[];
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
  service_id: string | null;
  action: string;
  risk: Risk;
  status: RemediationStatus;
  reason: string | null;
  verified: boolean;
  created_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
  executed_by: Actor | null;
  execution_id: string | null;
  policy_decision: PolicyDecision | null;
  policy_version: string | null;
  policy_reason: string | null;
}

export interface IncidentEvent {
  type: string;
  message: string;
  created_at: string;
  actor?: Actor;
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

export interface GlobalSettings {
  autonomy_mode: AutonomyMode;
  autonomy_mode_changed_at: string | null;
  autonomy_mode_changed_by: string | null;
  kill_switch_enabled: boolean;
  kill_switch_changed_at: string | null;
  kill_switch_changed_by: string | null;
}

export interface ServiceProfile {
  service_id: string;
  criticality: Criticality;
  environment: Environment;
  autonomy_level: AutonomyMode;
  allowed_automatic_actions: string[];
  actions_requiring_approval: string[];
  action_risk_overrides: Record<string, Risk>;
}
