"use client";

import { useEffect, useState } from "react";
import { getService, listServices, putService } from "@/lib/api";
import type { AutonomyMode, Criticality, Environment, ServiceProfile } from "@/lib/types";
import { Card, EmptyState, SectionLabel } from "@/app/components/ui";

const CRITICALITY_COLOR: Record<Criticality, string> = {
  low: "var(--color-success)",
  medium: "var(--color-warning)",
  high: "#fb923c",
  critical: "var(--color-critical)",
};

const KNOWN_ACTIONS = [
  "retry_service",
  "rerun_health_check",
  "gather_logs",
  "restore_env_var",
  "rollback_revision",
  "fix_dependency_config",
];

function ServiceForm({
  profile,
  onSaved,
}: {
  profile: ServiceProfile;
  onSaved: (p: ServiceProfile) => void;
}) {
  const [draft, setDraft] = useState<ServiceProfile>(profile);
  const [busy, setBusy] = useState(false);

  function toggleAction(list: "allowed_automatic_actions" | "actions_requiring_approval", action: string) {
    setDraft((d) => {
      const has = d[list].includes(action);
      return { ...d, [list]: has ? d[list].filter((a) => a !== action) : [...d[list], action] };
    });
  }

  async function save() {
    setBusy(true);
    try {
      onSaved(await putService(draft.service_id, draft));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="font-mono text-sm font-semibold text-[var(--color-text-primary)]">
          {draft.service_id}
        </span>
        <span
          className="rounded-full border px-3 py-1 text-xs font-semibold uppercase"
          style={{
            color: CRITICALITY_COLOR[draft.criticality],
            borderColor: `${CRITICALITY_COLOR[draft.criticality]}55`,
          }}
        >
          {draft.criticality}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs text-[var(--color-text-muted)]">
          Criticality
          <select
            value={draft.criticality}
            onChange={(e) => setDraft({ ...draft, criticality: e.target.value as Criticality })}
            className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-3 py-1.5 text-sm text-[var(--color-text-primary)]"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </label>
        <label className="text-xs text-[var(--color-text-muted)]">
          Environment
          <select
            value={draft.environment}
            onChange={(e) => setDraft({ ...draft, environment: e.target.value as Environment })}
            className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-3 py-1.5 text-sm text-[var(--color-text-primary)]"
          >
            <option value="development">Development</option>
            <option value="staging">Staging</option>
            <option value="production">Production</option>
          </select>
        </label>
        <label className="text-xs text-[var(--color-text-muted)] sm:col-span-2">
          Autonomy for this service
          <select
            value={draft.autonomy_level}
            onChange={(e) => setDraft({ ...draft, autonomy_level: e.target.value as AutonomyMode })}
            className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-3 py-1.5 text-sm text-[var(--color-text-primary)]"
          >
            <option value="observe_only">Observe Only</option>
            <option value="recommend_only">Recommend Only</option>
            <option value="approval_required">Approval Required</option>
            <option value="autonomous_low_risk">Autonomous Low-Risk</option>
          </select>
        </label>
      </div>

      <div>
        <div className="mb-1 text-xs text-[var(--color-text-muted)]">
          Allowed automatic actions (empty = use the global whitelist)
        </div>
        <div className="flex flex-wrap gap-2">
          {KNOWN_ACTIONS.map((a) => (
            <button
              key={a}
              onClick={() => toggleAction("allowed_automatic_actions", a)}
              className="rounded-full border px-3 py-1 text-xs"
              style={
                draft.allowed_automatic_actions.includes(a)
                  ? { borderColor: "var(--color-success)", color: "var(--color-success)" }
                  : { borderColor: "var(--color-border)", color: "var(--color-text-muted)" }
              }
            >
              {a.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-1 text-xs text-[var(--color-text-muted)]">Always require approval for</div>
        <div className="flex flex-wrap gap-2">
          {KNOWN_ACTIONS.map((a) => (
            <button
              key={a}
              onClick={() => toggleAction("actions_requiring_approval", a)}
              className="rounded-full border px-3 py-1 text-xs"
              style={
                draft.actions_requiring_approval.includes(a)
                  ? { borderColor: "var(--color-warning)", color: "var(--color-warning)" }
                  : { borderColor: "var(--color-border)", color: "var(--color-text-muted)" }
              }
            >
              {a.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={save}
        disabled={busy}
        className="self-start rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        style={{ background: "var(--color-primary)" }}
      >
        {busy ? "Saving..." : "Save service policy"}
      </button>
    </Card>
  );
}

export default function ServicesPage() {
  const [services, setServices] = useState<ServiceProfile[]>([]);
  const [newServiceId, setNewServiceId] = useState("");
  const [loading, setLoading] = useState(true);

  function refresh() {
    setLoading(true);
    fetchServices();
  }

  function fetchServices() {
    listServices()
      .then(({ services }) => setServices(services))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchServices();
  }, []);

  async function addService() {
    if (!newServiceId.trim()) return;
    const profile = await getService(newServiceId.trim());
    setServices((s) => [...s.filter((p) => p.service_id !== profile.service_id), profile]);
    setNewServiceId("");
  }

  function handleSaved(updated: ServiceProfile) {
    setServices((s) => s.map((p) => (p.service_id === updated.service_id ? updated : p)));
  }

  return (
    <div className="px-8 py-8">
      <header className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Service Risk Profiles</h1>
          <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
            Per-service overrides on top of the global safety policy — criticality, environment,
            autonomy, and which actions can run automatically.
          </p>
        </div>
        <button onClick={refresh} className="text-xs text-[var(--color-text-muted)] hover:underline">
          Refresh
        </button>
      </header>

      <Card className="mb-6 flex items-end gap-3">
        <label className="flex-1 text-xs text-[var(--color-text-muted)]">
          Add / edit a service
          <input
            value={newServiceId}
            onChange={(e) => setNewServiceId(e.target.value)}
            placeholder="e.g. demo-service, payment-api"
            className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-3 py-1.5 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)]"
          />
        </label>
        <button
          onClick={addService}
          className="rounded-lg border border-[var(--color-border)] px-4 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)]"
        >
          Load
        </button>
      </Card>

      {loading && <EmptyState>Loading...</EmptyState>}

      {!loading && services.length === 0 && (
        <EmptyState>No service profiles yet — add one above (e.g. &quot;demo-service&quot;).</EmptyState>
      )}

      {!loading && services.length > 0 && (
        <>
          <SectionLabel>Services ({services.length})</SectionLabel>
          <div className="grid gap-4 lg:grid-cols-2">
            {services.map((p) => (
              <ServiceForm key={p.service_id} profile={p} onSaved={handleSaved} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
