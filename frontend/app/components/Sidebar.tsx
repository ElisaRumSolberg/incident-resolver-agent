"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: "◈" },
  { href: "/incidents", label: "Incidents", icon: "⚠" },
  { href: "/memory", label: "Memory", icon: "◎" },
  { href: "/safety", label: "Safety", icon: "◆" },
  { href: "/postmortems", label: "Postmortems", icon: "▤" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-6">
      <div className="mb-8 px-2">
        <div className="text-xs font-semibold uppercase tracking-widest text-[var(--color-accent)]">
          Autonomous
        </div>
        <div className="text-sm font-bold text-[var(--color-text-primary)]">Incident Resolver</div>
        <div className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">Production Operations Center</div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                active
                  ? "bg-[var(--color-surface-elevated)] font-medium text-[var(--color-text-primary)]"
                  : "text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)]/60 hover:text-[var(--color-text-primary)]"
              }`}
            >
              <span className={active ? "text-[var(--color-primary)]" : "text-[var(--color-text-muted)]"}>
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto px-2 text-[11px] text-[var(--color-text-muted)]">
        Gemini 3 + Google ADK
        <br />
        Cloud Run · Firestore
      </div>
    </aside>
  );
}
