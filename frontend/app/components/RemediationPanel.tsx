"use client";

import type { Remediation } from "@/lib/types";
import { RiskBadge } from "./Badges";
import { Card, SectionLabel } from "./ui";

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
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <SectionLabel>Proposed remediation</SectionLabel>
        <RiskBadge risk={remediation.risk} />
      </div>

      <div className="text-lg font-semibold text-[var(--color-text-primary)]">
        {remediation.action.replace(/_/g, " ")}
      </div>
      <p className="mt-2 text-sm text-[var(--color-text-secondary)]">{remediation.reason}</p>

      {blocked && (
        <p className="mt-4 rounded-lg border border-[var(--color-blocked)]/30 bg-[var(--color-blocked)]/10 p-3 text-sm text-[var(--color-blocked)]">
          This action is not on the safe-remediation whitelist and will never be auto-executed.
          A human needs to handle this manually.
        </p>
      )}

      {needsApproval && (
        <div className="mt-4 flex gap-3">
          <button
            onClick={onApprove}
            disabled={busy}
            className="rounded-lg px-4 py-2 text-sm font-medium text-white transition disabled:opacity-50"
            style={{ background: "var(--color-success)" }}
          >
            Approve
          </button>
          <button
            onClick={onReject}
            disabled={busy}
            className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition hover:bg-[var(--color-surface-elevated)] disabled:opacity-50"
          >
            Reject
          </button>
        </div>
      )}

      {!needsApproval && !blocked && (
        <div className="mt-3 text-xs text-[var(--color-text-muted)]">
          Status: <span className="font-medium text-[var(--color-text-secondary)]">{remediation.status}</span>
          {remediation.verified && " — verified healthy"}
        </div>
      )}
    </Card>
  );
}
