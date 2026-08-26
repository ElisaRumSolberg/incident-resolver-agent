import type { IncidentStatus, Risk } from "@/lib/types";

const STATUS_COLOR: Record<IncidentStatus, string> = {
  investigating: "var(--color-primary)",
  awaiting_approval: "var(--color-warning)",
  remediating: "var(--color-accent)",
  verifying: "var(--color-accent)",
  resolved: "var(--color-success)",
  escalation_required: "var(--color-blocked)",
  failed: "var(--color-critical)",
};

export function StatusBadge({ status }: { status: IncidentStatus }) {
  const color = STATUS_COLOR[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide"
      style={{ color, borderColor: `${color}55`, background: `${color}1a` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
      {status.replace(/_/g, " ")}
    </span>
  );
}

const RISK_COLOR: Record<Risk, string> = {
  low: "var(--color-success)",
  medium: "var(--color-warning)",
  high: "var(--color-critical)",
};

export function RiskBadge({ risk }: { risk: Risk }) {
  const color = RISK_COLOR[risk];
  return (
    <span
      className="inline-block rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide"
      style={{ color, borderColor: `${color}55`, background: `${color}1a` }}
    >
      {risk} risk
    </span>
  );
}

const SEVERITY_COLOR: Record<string, string> = {
  low: "var(--color-success)",
  medium: "var(--color-warning)",
  high: "#fb923c",
  critical: "var(--color-critical)",
};

export function SeverityLabel({ severity }: { severity: string | null }) {
  if (!severity) return null;
  return (
    <span
      className="font-semibold uppercase"
      style={{ color: SEVERITY_COLOR[severity] || "var(--color-text-secondary)" }}
    >
      {severity}
    </span>
  );
}
