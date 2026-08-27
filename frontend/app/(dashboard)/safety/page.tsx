"use client";

import { useEffect, useState } from "react";
import { getSafetyStats } from "@/lib/api";
import type { SafetyStats } from "@/lib/types";
import { AutonomyControls } from "@/app/components/AutonomyControls";
import { Card, EmptyState, SectionLabel } from "@/app/components/ui";

function StatBlock({
  label,
  value,
  color,
  description,
}: {
  label: string;
  value: number;
  color: string;
  description: string;
}) {
  return (
    <Card>
      <div className="mb-2 h-1.5 w-full rounded-full" style={{ background: color }} />
      <div className="text-3xl font-bold tabular-nums" style={{ color }}>
        {value}
      </div>
      <div className="mt-1 text-sm font-semibold text-[var(--color-text-primary)]">{label}</div>
      <div className="mt-1 text-xs text-[var(--color-text-muted)]">{description}</div>
    </Card>
  );
}

export default function SafetyPage() {
  const [stats, setStats] = useState<SafetyStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSafetyStats()
      .then(setStats)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="px-8 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Safety Center</h1>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
          Every remediation decision, and why it was auto-executed, approved, or blocked.
        </p>
      </header>

      <AutonomyControls />

      {loading && <EmptyState>Loading...</EmptyState>}

      {!loading && stats && (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <StatBlock
              label="Auto-executed"
              value={stats.auto_executed}
              color="var(--color-success)"
              description="LOW risk — ran without human approval"
            />
            <StatBlock
              label="Approved"
              value={stats.approved}
              color="var(--color-warning)"
              description="MEDIUM risk — human approved before running"
            />
            <StatBlock
              label="Awaiting approval"
              value={stats.awaiting_approval}
              color="var(--color-primary)"
              description="MEDIUM risk — still pending a decision"
            />
            <StatBlock
              label="Rejected"
              value={stats.rejected}
              color="var(--color-accent)"
              description="Human rejected the proposed action"
            />
            <StatBlock
              label="Blocked"
              value={stats.blocked}
              color="var(--color-blocked)"
              description="HIGH risk or unrecognized — never auto-executed"
            />
          </div>

          <Card>
            <SectionLabel>The whitelist</SectionLabel>
            <p className="mb-4 text-sm text-[var(--color-text-secondary)]">
              The agent&apos;s own opinion of an action&apos;s risk is never trusted for execution decisions.
              Only the action name is looked up here — anything not listed is treated as unsafe.
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-[var(--color-success)]/30 bg-[var(--color-success)]/10 p-3">
                <div className="text-xs font-semibold uppercase text-[var(--color-success)]">Low — auto</div>
                <div className="mt-1 text-xs text-[var(--color-text-secondary)]">
                  retry_service, rerun_health_check, gather_logs
                </div>
              </div>
              <div className="rounded-lg border border-[var(--color-warning)]/30 bg-[var(--color-warning)]/10 p-3">
                <div className="text-xs font-semibold uppercase text-[var(--color-warning)]">
                  Medium — approval
                </div>
                <div className="mt-1 text-xs text-[var(--color-text-secondary)]">
                  restore_env_var, rollback_revision, fix_dependency_config
                </div>
              </div>
              <div className="rounded-lg border border-[var(--color-blocked)]/30 bg-[var(--color-blocked)]/10 p-3">
                <div className="text-xs font-semibold uppercase text-[var(--color-blocked)]">
                  High / unknown — never
                </div>
                <div className="mt-1 text-xs text-[var(--color-text-secondary)]">
                  delete_data, rotate_credentials, anything not whitelisted
                </div>
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
