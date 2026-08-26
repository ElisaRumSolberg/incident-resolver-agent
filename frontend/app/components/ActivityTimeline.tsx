import type { IncidentEvent } from "@/lib/types";

const TYPE_ICON: Record<string, string> = {
  investigation_started: "🔍",
  diagnosis: "🧠",
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
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-5 text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900">
        No activity yet.
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
        Agent activity
      </h2>
      <ul className="space-y-2 font-mono text-sm">
        {events.map((e, i) => (
          <li key={i} className="flex gap-3 text-zinc-700 dark:text-zinc-300">
            <span className="shrink-0 text-zinc-400">{formatTime(e.created_at)}</span>
            <span>{TYPE_ICON[e.type] || "•"}</span>
            <span>{e.message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
