"use client";

import { useEffect, useState } from "react";
import { getAnalytics, getOverview } from "@/lib/api";
import type { AnalyticsData, OverviewStats } from "@/lib/types";
import { Card, EmptyState, ProgressBar, SectionLabel } from "@/app/components/ui";

const CATEGORY_COLORS: Record<string, string> = {
  "Configuration errors": "var(--color-warning)",
  "Bad deployments": "var(--color-critical)",
  "Dependency failures": "var(--color-blocked)",
  "Transient failures": "var(--color-accent)",
  "Security incidents": "var(--color-critical)",
  Unknown: "var(--color-text-muted)",
};

export default function MemoryPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getAnalytics(), getOverview()])
      .then(([a, o]) => {
        setAnalytics(a);
        setOverview(o);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="px-8 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Memory</h1>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
          What the agent has learned from past incidents.
        </p>
      </header>

      {loading && <EmptyState>Loading...</EmptyState>}

      {!loading && overview && (
        <div className="mb-6 flex items-center gap-2 rounded-lg border border-[var(--color-accent)]/30 bg-[var(--color-accent)]/10 px-4 py-3 text-sm text-[var(--color-accent)]">
          <span>◎</span>
          Agent learned from {overview.incidents_learned_from} previous incident
          {overview.incidents_learned_from === 1 ? "" : "s"}.
        </div>
      )}

      {!loading && analytics && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <SectionLabel>Top root causes</SectionLabel>
            {analytics.top_root_causes.length === 0 ? (
              <EmptyState>No resolved incidents yet.</EmptyState>
            ) : (
              <div className="flex flex-col gap-3">
                {analytics.top_root_causes.map((rc) => (
                  <ProgressBar
                    key={rc.category}
                    label={rc.category}
                    percent={rc.percent}
                    color={CATEGORY_COLORS[rc.category] || "var(--color-primary)"}
                  />
                ))}
              </div>
            )}
          </Card>

          <Card>
            <SectionLabel>Remediation success rate</SectionLabel>
            {analytics.remediation_success_rate.length === 0 ? (
              <EmptyState>No remediations attempted yet.</EmptyState>
            ) : (
              <div className="flex flex-col gap-3">
                {analytics.remediation_success_rate.map((r) => (
                  <ProgressBar
                    key={r.action}
                    label={`${r.action.replace(/_/g, " ")} (${r.attempts} attempt${r.attempts === 1 ? "" : "s"})`}
                    percent={r.success_rate}
                    color="var(--color-success)"
                  />
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
