import type { IncidentStatus, Risk } from "@/lib/types";

const STATUS_STYLES: Record<IncidentStatus, string> = {
  investigating: "bg-blue-100 text-blue-800 border-blue-300",
  awaiting_approval: "bg-amber-100 text-amber-800 border-amber-300",
  remediating: "bg-purple-100 text-purple-800 border-purple-300",
  verifying: "bg-purple-100 text-purple-800 border-purple-300",
  resolved: "bg-emerald-100 text-emerald-800 border-emerald-300",
  escalation_required: "bg-red-100 text-red-800 border-red-300",
  failed: "bg-red-100 text-red-800 border-red-300",
};

export function StatusBadge({ status }: { status: IncidentStatus }) {
  return (
    <span
      className={`inline-block rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${STATUS_STYLES[status]}`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

const RISK_STYLES: Record<Risk, string> = {
  low: "bg-emerald-100 text-emerald-800 border-emerald-300",
  medium: "bg-amber-100 text-amber-800 border-amber-300",
  high: "bg-red-100 text-red-800 border-red-300",
};

export function RiskBadge({ risk }: { risk: Risk }) {
  return (
    <span
      className={`inline-block rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${RISK_STYLES[risk]}`}
    >
      {risk} risk
    </span>
  );
}

const SEVERITY_STYLES: Record<string, string> = {
  low: "text-emerald-700",
  medium: "text-amber-700",
  high: "text-orange-700",
  critical: "text-red-700",
};

export function SeverityLabel({ severity }: { severity: string | null }) {
  if (!severity) return null;
  return (
    <span className={`font-semibold uppercase ${SEVERITY_STYLES[severity] || "text-zinc-700"}`}>
      {severity}
    </span>
  );
}
