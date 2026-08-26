"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listPostmortems } from "@/lib/api";
import type { Postmortem } from "@/lib/types";
import { Card, EmptyState } from "../components/ui";

function formatSeconds(s: number | null): string {
  if (s === null) return "—";
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

export default function PostmortemsPage() {
  const [postmortems, setPostmortems] = useState<Postmortem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listPostmortems()
      .then(({ postmortems }) => setPostmortems(postmortems))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="px-8 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Postmortems</h1>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
          Auto-generated summaries of resolved incidents, grounded in their own timeline.
        </p>
      </header>

      {loading && <EmptyState>Loading...</EmptyState>}

      {!loading && postmortems.length === 0 && (
        <EmptyState>
          No postmortems yet — open a resolved incident and click &quot;Generate postmortem&quot;.
        </EmptyState>
      )}

      <div className="flex flex-col gap-4">
        {postmortems.map((p) => (
          <Link key={p.incident_id} href={`/incidents/${p.incident_id}`}>
            <Card className="transition hover:border-[var(--color-primary)]/50">
              <div className="mb-2 flex items-center justify-between">
                <span className="font-mono text-sm text-[var(--color-text-secondary)]">{p.service_id}</span>
                <span className="text-xs text-[var(--color-text-muted)]">
                  Recovery: {formatSeconds(p.recovery_seconds)}
                </span>
              </div>
              <p className="text-sm leading-relaxed text-[var(--color-text-primary)]">{p.summary}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
