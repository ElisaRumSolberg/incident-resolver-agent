import type { Incident, Remediation, RemediationSuccessRate } from "@/lib/types";
import { Card, ProgressBar, SectionLabel } from "./ui";

const TOOL_LABELS: Record<string, string> = {
  read_recent_logs: "read_recent_logs",
  extract_error_patterns: "extract_error_patterns",
  inspect_service_config: "inspect_service_config",
  propose_remediation: "propose_remediation",
  search_incident_memory: "search_incident_memory",
  evaluate_safety_policy: "evaluate_safety_policy",
  verify_recovery: "verify_recovery",
};

export function EvidencePanel({
  incident,
  remediation,
  successRate,
}: {
  incident: Incident;
  remediation: Remediation | undefined;
  successRate: RemediationSuccessRate | undefined;
}) {
  return (
    <Card>
      <SectionLabel>Evidence & explainability</SectionLabel>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <div className="text-xs text-[var(--color-text-muted)]">Root cause confidence</div>
          <div className="mt-1">
            <ProgressBar
              percent={incident.confidence !== null ? Math.round(incident.confidence * 100) : 0}
              color="var(--color-accent)"
            />
          </div>
        </div>

        {successRate && (
          <div>
            <div className="text-xs text-[var(--color-text-muted)]">
              Historical success rate of &quot;{remediation?.action.replace(/_/g, " ")}&quot;
            </div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-lg font-bold text-[var(--color-text-primary)]">
                {successRate.success_rate}%
              </span>
              <span className="text-xs text-[var(--color-text-muted)]">
                ({successRate.attempts} previous attempt{successRate.attempts === 1 ? "" : "s"})
              </span>
            </div>
          </div>
        )}
      </div>

      {remediation?.reason && (
        <div className="mt-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
            Why this action?
          </div>
          <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{remediation.reason}</p>
        </div>
      )}

      {incident.tools_used.length > 0 && (
        <div className="mt-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
            Tools used
          </div>
          <div className="mt-2 flex flex-wrap gap-2 font-mono text-xs">
            {incident.tools_used.map((tool, i) => (
              <span
                key={`${tool}-${i}`}
                className="rounded-md border border-[var(--color-success)]/30 bg-[var(--color-success)]/10 px-2 py-1 text-[var(--color-success)]"
              >
                ✓ {TOOL_LABELS[tool] || tool}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-3">
          <div className="text-xs font-semibold uppercase text-[var(--color-text-muted)]">Logs</div>
          <div className="mt-1 text-xs text-[var(--color-text-secondary)]">
            {incident.tools_used.includes("read_recent_logs")
              ? "Recent log entries inspected."
              : "Not inspected for this incident."}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-3">
          <div className="text-xs font-semibold uppercase text-[var(--color-text-muted)]">Configuration</div>
          <div className="mt-1 text-xs text-[var(--color-text-secondary)]">
            {incident.tools_used.includes("inspect_service_config")
              ? "Service configuration snapshot inspected."
              : "Not inspected for this incident."}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-3">
          <div className="text-xs font-semibold uppercase text-[var(--color-text-muted)]">
            Historical incidents
          </div>
          <div className="mt-1 text-xs text-[var(--color-text-secondary)]">
            {incident.similar_incidents.length > 0
              ? `${incident.similar_incidents.length} similar past incident${incident.similar_incidents.length === 1 ? "" : "s"} found.`
              : "No similar past incidents found."}
          </div>
        </div>
      </div>
    </Card>
  );
}
