"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const NAV_ITEMS = [
  { href: "/overview", label: "Overview", icon: "◈" },
  { href: "/incidents", label: "Incidents", icon: "⚠" },
  { href: "/memory", label: "Memory", icon: "◎" },
  { href: "/safety", label: "Safety", icon: "◆" },
  { href: "/services", label: "Services", icon: "▣" },
  { href: "/postmortems", label: "Postmortems", icon: "▤" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isGuest, signOut, signInWithGoogle } = useAuth();

  async function handleSignOut() {
    await signOut();
    router.push("/");
  }

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
          const active = pathname.startsWith(item.href);
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

      <div className="mt-auto flex flex-col gap-3">
        {user && (
          <div className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-3 py-2">
            {user.photoURL ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={user.photoURL} alt="" className="h-7 w-7 rounded-full" referrerPolicy="no-referrer" />
            ) : (
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--color-primary)] text-xs font-bold text-white">
                {(user.displayName || user.email || "?")[0].toUpperCase()}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-medium text-[var(--color-text-primary)]">
                {user.displayName || user.email}
              </div>
              <button
                onClick={handleSignOut}
                className="text-[11px] text-[var(--color-text-muted)] hover:text-[var(--color-critical)]"
              >
                Sign out
              </button>
            </div>
          </div>
        )}
        {isGuest && !user && (
          <div className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-3 py-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--color-text-muted)] text-xs font-bold text-white">
              G
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-medium text-[var(--color-text-primary)]">Guest</div>
              <div className="flex items-center gap-2">
                <button
                  onClick={signInWithGoogle}
                  className="text-[11px] text-[var(--color-text-muted)] hover:text-[var(--color-primary)]"
                >
                  Sign in with Google
                </button>
                <span className="text-[11px] text-[var(--color-border)]">·</span>
                <button
                  onClick={handleSignOut}
                  className="text-[11px] text-[var(--color-text-muted)] hover:text-[var(--color-critical)]"
                >
                  Exit
                </button>
              </div>
            </div>
          </div>
        )}
        <div className="px-2 text-[11px] text-[var(--color-text-muted)]">
          Gemini 3 + Google ADK
          <br />
          Cloud Run · Firestore
        </div>
      </div>
    </aside>
  );
}
