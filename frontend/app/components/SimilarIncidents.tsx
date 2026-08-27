import Link from "next/link";
import type { SimilarIncident } from "@/lib/types";
import { Card, SectionLabel } from "./ui";

function formatSeconds(s: number | null | undefined): string {
  if (s === null || s === undefined) return "";
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

export function SimilarIncidents({ items }: { items: SimilarIncident[] }) {
  if (items.length === 0) return null;
  return (
    <Card>
      <SectionLabel>Similar past incidents</SectionLabel>
      <div className="flex flex-col gap-3">
        {items.map((s) => {
          const successful = s.result === "successful";
          const color = successful ? "var(--color-success)" : "var(--color-critical)";
          return (
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
                <div className="mt-1 text-xs" style={{ color }}>
                  {successful ? "Fixed" : "Tried"} with {s.action.replace(/_/g, " ")} — {s.result}
                  {s.recovery_seconds != null && ` in ${formatSeconds(s.recovery_seconds)}`}
                </div>
              )}
            </Link>
          );
        })}
      </div>
    </Card>
  );
}
