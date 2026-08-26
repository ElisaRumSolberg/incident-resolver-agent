import type { Incident } from "@/lib/types";
import { SeverityLabel, StatusBadge } from "./Badges";

export function IncidentOverview({ incident }: { incident: Incident }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Incident on {incident.service_id}
        </h2>
        <StatusBadge status={incident.status} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <div className="text-xs text-zinc-500">Severity</div>
          <div className="mt-1">
            <SeverityLabel severity={incident.severity} />
          </div>
        </div>
        <div>
          <div className="text-xs text-zinc-500">Confidence</div>
          <div className="mt-1 font-semibold text-zinc-900 dark:text-zinc-100">
            {incident.confidence !== null ? `${Math.round(incident.confidence * 100)}%` : "—"}
          </div>
        </div>
        <div className="sm:col-span-2">
          <div className="text-xs text-zinc-500">Likely root cause</div>
          <div className="mt-1 text-zinc-900 dark:text-zinc-100">
            {incident.root_cause || "Investigating..."}
          </div>
        </div>
        <div className="sm:col-span-2">
          <div className="text-xs text-zinc-500">Agent's next action</div>
          <div className="mt-1 font-medium text-zinc-900 dark:text-zinc-100">
            {incident.next_action ? incident.next_action.replace(/_/g, " ") : "—"}
          </div>
        </div>
        {incident.attempted_actions.length > 0 && (
          <div className="sm:col-span-2">
            <div className="text-xs text-zinc-500">Attempted actions</div>
            <div className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">
              {incident.attempted_actions.map((a) => a.replace(/_/g, " ")).join(" → ")}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
