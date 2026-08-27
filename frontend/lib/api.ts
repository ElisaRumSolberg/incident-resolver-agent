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
import { auth } from "./firebase";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  // Attached whenever a real (non-guest) Firebase user is signed in — the
  // backend only enforces it when DEMO_MODE=false, but sending it now means
  // guest-mode's relaxed default and a locked-down deployment both work
  // without any further frontend changes.
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const idToken = await auth.currentUser?.getIdToken().catch(() => undefined);
  if (idToken) headers.Authorization = `Bearer ${idToken}`;

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...headers, ...(options?.headers || {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    // The backend's error body is usually {"detail": "human-readable message"}
    // — surface that directly instead of dumping the raw status line + JSON
    // blob in front of a judge watching a live demo.
    let message = text;
    try {
      const parsed = JSON.parse(text);
      if (parsed && typeof parsed.detail === "string") message = parsed.detail;
    } catch {
      // Not JSON — fall back to the raw body.
    }
    throw new Error(message || `${res.status} ${res.statusText}`);
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

export function approveRemediation(incidentId: string, remediationId: string, approvedBy = "guest") {
  return request<IncidentResponse>(
    `/incidents/${incidentId}/remediations/${remediationId}/approve`,
    { method: "POST", body: JSON.stringify({ approved_by: approvedBy }) }
  );
}

export function rejectRemediation(incidentId: string, remediationId: string, rejectedBy = "guest") {
  return request<IncidentResponse>(
    `/incidents/${incidentId}/remediations/${remediationId}/reject`,
    { method: "POST", body: JSON.stringify({ rejected_by: rejectedBy }) }
  );
}

export function getSettings() {
  return request<GlobalSettings>("/settings");
}

export function setAutonomyMode(mode: string, changedBy = "guest") {
  return request<GlobalSettings>("/settings/autonomy-mode", {
    method: "PUT",
    body: JSON.stringify({ mode, changed_by: changedBy }),
  });
}

export function setKillSwitch(enabled: boolean, changedBy = "guest") {
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
