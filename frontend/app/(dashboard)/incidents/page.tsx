"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listIncidents, resetDemo, startInvestigation, triggerDemoScenario } from "@/lib/api";
import { isHealthySnapshot, type Incident } from "@/lib/types";
import { SeverityLabel, StatusBadge } from "@/app/components/Badges";
import { ScenarioTrigger } from "@/app/components/ScenarioTrigger";
import { Card, EmptyState, SectionLabel } from "@/app/components/ui";

const ACTIVE_STATUSES = new Set(["investigating", "awaiting_approval", "remediating", "verifying"]);

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString([], { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [serviceFilter, setServiceFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  function refresh() {
    setLoading(true);
    fetchIncidents();
  }

  function fetchIncidents() {
    listIncidents()
      .then(({ incidents }) => setIncidents(incidents))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchIncidents();
  }, []);

  async function handleTrigger(scenario: string) {
    setTriggering(true);
    setStatusMessage("Incident triggered. Agent is investigating...");
    try {
      await triggerDemoScenario(scenario);
      const result = await startInvestigation();
      if (isHealthySnapshot(result)) {
        setStatusMessage(result.message);
      } else {
        setStatusMessage(null);
        refresh();
      }
    } catch (e) {
      setStatusMessage(e instanceof Error ? e.message : String(e));
    } finally {
      setTriggering(false);
    }
  }

  async function handleReset() {
    setTriggering(true);
    try {
      await resetDemo();
      setStatusMessage("Demo service reset to healthy baseline.");
    } finally {
      setTriggering(false);
    }
  }

  const live = incidents.filter((i) => ACTIVE_STATUSES.has(i.status));
  const history = incidents.filter((i) => !ACTIVE_STATUSES.has(i.status));
  const filteredHistory = history.filter(
    (i) =>
      (!serviceFilter || i.service_id.includes(serviceFilter)) &&
      (!statusFilter || i.status === statusFilter)
  );

  return (
    <div className="px-8 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Incidents</h1>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
          Live incidents and full history.
        </p>
      </header>

      <div className="mb-6">
        <ScenarioTrigger onTrigger={handleTrigger} onReset={handleReset} disabled={triggering} />
      </div>

      {statusMessage && (
        <div className="mb-6 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm text-[var(--color-text-secondary)]">
          {statusMessage}
        </div>
      )}

      <SectionLabel>Live incidents ({live.length})</SectionLabel>
      {loading ? (
        <EmptyState>Loading...</EmptyState>
      ) : live.length === 0 ? (
        <EmptyState>No active incidents right now.</EmptyState>
      ) : (
        <div className="mb-8 grid gap-3 sm:grid-cols-2">
          {live.map((incident) => (
            <Link key={incident.id} href={`/incidents/${incident.id}`}>
              <Card className="transition hover:border-[var(--color-primary)]/50">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-mono text-sm text-[var(--color-text-secondary)]">
                    {incident.service_id}
                  </span>
                  <StatusBadge status={incident.status} />
                </div>
                <div className="text-sm text-[var(--color-text-primary)]">
                  {incident.root_cause || "Investigating..."}
                </div>
                <div className="mt-2 flex items-center gap-3 text-xs">
                  <SeverityLabel severity={incident.severity} />
                  {incident.next_action && (
                    <span className="text-[var(--color-text-muted)]">
                      → {incident.next_action.replace(/_/g, " ")}
                    </span>
                  )}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <div className="mb-3 flex items-center justify-between">
        <SectionLabel>History ({filteredHistory.length})</SectionLabel>
        <div className="flex gap-2">
          <input
            placeholder="filter by service..."
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-3 py-1.5 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-3 py-1.5 text-xs text-[var(--color-text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
          >
            <option value="">all statuses</option>
            <option value="resolved">resolved</option>
            <option value="escalation_required">escalation required</option>
            <option value="failed">failed</option>
          </select>
        </div>
      </div>

      {filteredHistory.length === 0 ? (
        <EmptyState>No past incidents yet — trigger a scenario above to build history.</EmptyState>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface)] text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
                <th className="px-4 py-3">Incident</th>
                <th className="px-4 py-3">Service</th>
                <th className="px-4 py-3">Root cause</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Started</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((incident) => (
                <tr
                  key={incident.id}
                  className="border-b border-[var(--color-border)] bg-[var(--color-surface)] last:border-0 hover:bg-[var(--color-surface-elevated)]"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/incidents/${incident.id}`}
                      className="font-mono text-[var(--color-primary)] hover:underline"
                    >
                      INC-{incident.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-secondary)]">{incident.service_id}</td>
                  <td className="max-w-xs truncate px-4 py-3 text-[var(--color-text-secondary)]">
                    {incident.root_cause || "—"}
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-secondary)]">
                    {incident.attempted_actions[incident.attempted_actions.length - 1]?.replace(/_/g, " ") || "—"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={incident.status} />
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)]">{formatDate(incident.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
