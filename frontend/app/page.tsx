"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getOverview, listIncidents } from "@/lib/api";
import type { Incident, OverviewStats } from "@/lib/types";
import { SeverityLabel, StatusBadge } from "./components/Badges";
import { Card, EmptyState, SectionLabel, StatTile } from "./components/ui";

const ACTIVE_STATUSES = new Set(["investigating", "awaiting_approval", "remediating", "verifying"]);

function formatSeconds(s: number | null): string {
  if (s === null) return "—";
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

export default function OverviewPage() {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [live, setLive] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getOverview(), listIncidents()])
      .then(([overview, { incidents }]) => {
        setStats(overview);
        setLive(incidents.filter((i) => ACTIVE_STATUSES.has(i.status)));
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="px-8 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
          Autonomous Incident Resolver
        </h1>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
          Production Operations Center — observe, diagnose, act, verify, re-plan.
        </p>
      </header>

      {loading && <EmptyState>Loading operations data...</EmptyState>}

      {!loading && stats && (
        <>
          <Card className="mb-6 flex p-0">
            <StatTile label="Active" value={String(stats.active_count)} accent="var(--color-critical)" />
            <StatTile label="Resolved today" value={String(stats.resolved_today)} accent="var(--color-success)" />
            <StatTile label="Auto-fix rate" value={`${stats.auto_resolved_rate}%`} accent="var(--color-accent)" />
            <StatTile label="Avg recovery" value={formatSeconds(stats.avg_recovery_seconds)} />
            <StatTile
              label="Awaiting approval"
              value={String(stats.awaiting_approval_count)}
              accent="var(--color-warning)"
            />
          </Card>

          <div className="mb-6 flex items-center gap-2 rounded-lg border border-[var(--color-accent)]/30 bg-[var(--color-accent)]/10 px-4 py-3 text-sm text-[var(--color-accent)]">
            <span>◎</span>
            Agent learned from {stats.incidents_learned_from} previous incident
            {stats.incidents_learned_from === 1 ? "" : "s"}.
          </div>

          <SectionLabel>Live incidents</SectionLabel>
          {live.length === 0 ? (
            <EmptyState>
              No active incidents.{" "}
              <Link href="/incidents" className="text-[var(--color-primary)] underline">
                Trigger a demo scenario
              </Link>{" "}
              to see the agent in action.
            </EmptyState>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
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
                      {incident.confidence !== null && (
                        <span className="text-[var(--color-text-muted)]">
                          {Math.round(incident.confidence * 100)}% confidence
                        </span>
                      )}
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
