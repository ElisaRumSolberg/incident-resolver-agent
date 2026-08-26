import Link from "next/link";
import type { SimilarIncident } from "@/lib/types";
import { Card, SectionLabel } from "./ui";

export function SimilarIncidents({ items }: { items: SimilarIncident[] }) {
  if (items.length === 0) return null;
  return (
    <Card>
      <SectionLabel>Similar past incidents</SectionLabel>
      <div className="flex flex-col gap-3">
        {items.map((s) => (
          <Link
            key={s.incident_id}
            href={`/incidents/${s.incident_id}`}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-3 transition hover:border-[var(--color-accent)]/50"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-[var(--color-text-muted)]">
                INC-{s.incident_id.slice(0, 8)}
              </span>
              <span className="text-sm font-semibold text-[var(--color-accent)]">
                {Math.round(s.similarity * 100)}% similar
              </span>
            </div>
            <div className="mt-1 text-sm text-[var(--color-text-primary)]">{s.root_cause}</div>
            {s.action && (
              <div className="mt-1 text-xs text-[var(--color-success)]">
                Fixed with {s.action.replace(/_/g, " ")} — {s.result}
              </div>
            )}
          </Link>
        ))}
      </div>
    </Card>
  );
}
