"use client";

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
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
        Demo: trigger an incident
      </h2>
      <div className="grid gap-3 sm:grid-cols-3">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            disabled={disabled}
            onClick={() => onTrigger(s.id)}
            className="rounded-lg border border-zinc-200 p-3 text-left transition hover:border-red-400 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-red-950/30"
          >
            <div className="font-medium text-zinc-900 dark:text-zinc-100">{s.label}</div>
            <div className="mt-1 text-xs text-zinc-500">{s.description}</div>
          </button>
        ))}
      </div>
      <button
        onClick={onReset}
        className="mt-3 text-xs font-medium text-zinc-500 underline hover:text-zinc-800 dark:hover:text-zinc-200"
      >
        Reset demo service to healthy baseline
      </button>
    </div>
  );
}
