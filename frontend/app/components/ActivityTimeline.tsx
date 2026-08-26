import type { IncidentEvent } from "@/lib/types";
import { Card, EmptyState, SectionLabel } from "./ui";

const TYPE_ICON: Record<string, string> = {
  investigation_started: "🔍",
  diagnosis: "🧠",
  similar_incident_found: "◎",
  auto_approved: "⚡",
  awaiting_approval: "⏸",
  approved: "✅",
  rejected: "🚫",
  remediation_applying: "🔧",
  verifying: "🔁",
  resolved: "🎉",
  remediation_failed: "⚠️",
  escalation: "🆘",
};

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return iso;
  }
}

export function ActivityTimeline({ events }: { events: IncidentEvent[] }) {
  if (events.length === 0) {
    return <EmptyState>No activity yet.</EmptyState>;
  }
  return (
    <Card>
      <SectionLabel>Agent activity</SectionLabel>
      <ul className="space-y-2 font-mono text-sm">
        {events.map((e, i) => (
          <li key={i} className="flex gap-3 text-[var(--color-text-secondary)]">
            <span className="shrink-0 text-[var(--color-text-muted)]">{formatTime(e.created_at)}</span>
            <span>{TYPE_ICON[e.type] || "•"}</span>
            <span>{e.message}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
