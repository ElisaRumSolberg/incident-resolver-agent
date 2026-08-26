import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 ${className}`}
    >
      {children}
    </div>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[var(--color-text-muted)]">
      {children}
    </h2>
  );
}

export function StatTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div className="flex-1 border-r border-[var(--color-border)] px-6 py-5 last:border-r-0">
      <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
        {label}
      </div>
      <div
        className="mt-1 text-3xl font-bold tabular-nums"
        style={{ color: accent || "var(--color-text-primary)" }}
      >
        {value}
      </div>
    </div>
  );
}

export function ProgressBar({
  percent,
  color = "var(--color-primary)",
  label,
}: {
  percent: number;
  color?: string;
  label?: string;
}) {
  return (
    <div>
      {label && (
        <div className="mb-1 flex items-center justify-between text-xs">
          <span className="text-[var(--color-text-secondary)]">{label}</span>
          <span className="font-medium text-[var(--color-text-primary)]">{percent}%</span>
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--color-surface-elevated)]">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${Math.min(percent, 100)}%`, background: color }}
        />
      </div>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-[var(--color-border)] p-8 text-center text-sm text-[var(--color-text-muted)]">
      {children}
    </div>
  );
}
