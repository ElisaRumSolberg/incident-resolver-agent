import type {
  AnalyticsData,
  GlobalSettings,
  IncidentResponse,
  OverviewStats,
  Postmortem,
  SafetyStats,
  ServiceProfile,
  StartIncidentResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export function triggerDemoScenario(scenario: string) {
  return request<{ status: string; scenario: string }>("/demo/trigger", {
    method: "POST",
    body: JSON.stringify({ scenario }),
  });
}

export function resetDemo() {
  return request<{ status: string }>("/demo/reset", { method: "POST" });
}

export function startInvestigation() {
  return request<StartIncidentResponse>("/incidents", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function getIncident(incidentId: string) {
  return request<IncidentResponse>(`/incidents/${incidentId}`);
}

export function listIncidents(filters?: { service_id?: string; status?: string }) {
  const params = new URLSearchParams();
  if (filters?.service_id) params.set("service_id", filters.service_id);
  if (filters?.status) params.set("status", filters.status);
  const qs = params.toString();
  return request<{ incidents: IncidentResponse["incident"][] }>(`/incidents${qs ? `?${qs}` : ""}`);
}

export function getOverview() {
  return request<OverviewStats>("/overview");
}

export function getAnalytics() {
  return request<AnalyticsData>("/analytics");
}

export function getSafetyStats() {
  return request<SafetyStats>("/safety/stats");
}

export function getPostmortem(incidentId: string) {
  return request<Postmortem>(`/incidents/${incidentId}/postmortem`);
}

export function listPostmortems() {
  return request<{ postmortems: Postmortem[] }>("/postmortems");
}

export function approveRemediation(incidentId: string, remediationId: string, approvedBy = "dashboard user") {
  return request<IncidentResponse>(
    `/incidents/${incidentId}/remediations/${remediationId}/approve`,
    { method: "POST", body: JSON.stringify({ approved_by: approvedBy }) }
  );
}

export function rejectRemediation(incidentId: string, remediationId: string, rejectedBy = "dashboard user") {
  return request<IncidentResponse>(
    `/incidents/${incidentId}/remediations/${remediationId}/reject`,
    { method: "POST", body: JSON.stringify({ rejected_by: rejectedBy }) }
  );
}

export function getSettings() {
  return request<GlobalSettings>("/settings");
}

export function setAutonomyMode(mode: string, changedBy = "dashboard user") {
  return request<GlobalSettings>("/settings/autonomy-mode", {
    method: "PUT",
    body: JSON.stringify({ mode, changed_by: changedBy }),
  });
}

export function setKillSwitch(enabled: boolean, changedBy = "dashboard user") {
  return request<GlobalSettings>("/settings/kill-switch", {
    method: "PUT",
    body: JSON.stringify({ enabled, changed_by: changedBy }),
  });
}

export function listServices() {
  return request<{ services: ServiceProfile[] }>("/services");
}

export function getService(serviceId: string) {
  return request<ServiceProfile>(`/services/${serviceId}`);
}

export function putService(serviceId: string, profile: Partial<ServiceProfile>) {
  return request<ServiceProfile>(`/services/${serviceId}`, {
    method: "PUT",
    body: JSON.stringify(profile),
  });
}
