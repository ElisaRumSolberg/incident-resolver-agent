"use client";

import { Card, SectionLabel } from "./ui";

const SCENARIOS: { id: string; label: string; description: string }[] = [
  {
    id: "missing_env_var",
    label: "Missing env var",
    description: "DATABASE_URL is unset — service can't reach its datastore.",
  },
  {
    id: "broken_dependency",
    label: "Broken dependency",
    description: "Upstream payments-api is failing repeatedly.",
  },
  {
    id: "bad_deployment",
    label: "Bad deployment",
    description: "The latest revision is crash-looping on startup.",
  },
];

export function ScenarioTrigger({
  onTrigger,
  onReset,
  disabled,
}: {
  onTrigger: (scenario: string) => void;
  onReset: () => void;
  disabled: boolean;
}) {
  return (
    <Card>
      <SectionLabel>Demo: trigger an incident</SectionLabel>
      <div className="grid gap-3 sm:grid-cols-3">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            disabled={disabled}
            onClick={() => onTrigger(s.id)}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-3 text-left transition hover:border-[var(--color-critical)]/60 hover:bg-[var(--color-critical)]/10 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <div className="font-medium text-[var(--color-text-primary)]">{s.label}</div>
            <div className="mt-1 text-xs text-[var(--color-text-muted)]">{s.description}</div>
          </button>
        ))}
      </div>
      <button
        onClick={onReset}
        className="mt-3 text-xs font-medium text-[var(--color-text-muted)] underline hover:text-[var(--color-text-primary)]"
      >
        Reset demo service to healthy baseline
      </button>
    </Card>
  );
}
