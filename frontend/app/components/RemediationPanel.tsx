"use client";

import type { Remediation } from "@/lib/types";
import { RiskBadge } from "./Badges";

export function RemediationPanel({
  remediation,
  onApprove,
  onReject,
  busy,
}: {
  remediation: Remediation;
  onApprove: () => void;
  onReject: () => void;
  busy: boolean;
}) {
  const needsApproval = remediation.status === "awaiting_approval";
  const blocked = remediation.status === "blocked";

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Proposed remediation
        </h2>
        <RiskBadge risk={remediation.risk} />
      </div>

      <div className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        {remediation.action.replace(/_/g, " ")}
      </div>
      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">{remediation.reason}</p>

      {blocked && (
        <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-300">
          This action is not on the safe-remediation whitelist and will never be auto-executed.
          A human needs to handle this manually.
        </p>
      )}

      {needsApproval && (
        <div className="mt-4 flex gap-3">
          <button
            onClick={onApprove}
            disabled={busy}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:opacity-50"
          >
            Approve
          </button>
          <button
            onClick={onReject}
            disabled={busy}
            className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Reject
          </button>
        </div>
      )}

      {!needsApproval && !blocked && (
        <div className="mt-3 text-xs text-zinc-500">
          Status: <span className="font-medium">{remediation.status}</span>
          {remediation.verified && " — verified healthy"}
        </div>
      )}
    </div>
  );
}
