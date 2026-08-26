import type { Incident } from "@/lib/types";
import { SeverityLabel, StatusBadge } from "./Badges";
import { Card } from "./ui";

export function IncidentOverview({ incident }: { incident: Incident }) {
  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-text-muted)]">
          Incident on {incident.service_id}
        </h2>
        <StatusBadge status={incident.status} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <div className="text-xs text-[var(--color-text-muted)]">Severity</div>
          <div className="mt-1">
            <SeverityLabel severity={incident.severity} />
          </div>
        </div>
        <div>
          <div className="text-xs text-[var(--color-text-muted)]">Confidence</div>
          <div className="mt-1 font-semibold text-[var(--color-text-primary)]">
            {incident.confidence !== null ? `${Math.round(incident.confidence * 100)}%` : "—"}
          </div>
        </div>
        <div className="sm:col-span-2">
          <div className="text-xs text-[var(--color-text-muted)]">Likely root cause</div>
          <div className="mt-1 text-[var(--color-text-primary)]">
            {incident.root_cause || "Investigating..."}
          </div>
        </div>
        <div className="sm:col-span-2">
          <div className="text-xs text-[var(--color-text-muted)]">Agent&apos;s next action</div>
          <div className="mt-1 font-medium text-[var(--color-text-primary)]">
            {incident.next_action ? incident.next_action.replace(/_/g, " ") : "—"}
          </div>
        </div>
        {incident.attempted_actions.length > 0 && (
          <div className="sm:col-span-2">
            <div className="text-xs text-[var(--color-text-muted)]">Attempted actions</div>
            <div className="mt-1 text-sm text-[var(--color-text-secondary)]">
              {incident.attempted_actions.map((a) => a.replace(/_/g, " ")).join(" → ")}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
