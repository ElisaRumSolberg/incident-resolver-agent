"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Logo } from "./components/Logo";

function ShieldIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z" />
      <path d="M9.5 12l1.8 1.8L14.8 10" />
    </svg>
  );
}

function HistoryIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12a9 9 0 1 0 3-6.7" />
      <path d="M3 4v4h4" />
      <path d="M12 8v4l3 2" />
    </svg>
  );
}

function AuditIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 3h9l3 3v15a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M9 10h6M9 13.5h6M9 17h4" />
    </svg>
  );
}

function SlidersIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h13M21 18h0" />
      <circle cx="15" cy="6" r="2" />
      <circle cx="7" cy="12" r="2" />
      <circle cx="17" cy="18" r="2" />
    </svg>
  );
}

function SparkleIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2z" />
    </svg>
  );
}

function LinkIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M9 15l6-6M10 6l1-1a4 4 0 0 1 6 6l-1 1M14 18l-1 1a4 4 0 0 1-6-6l1-1" />
    </svg>
  );
}

function CloudRunIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 18a4 4 0 0 1-1-7.9 5 5 0 0 1 9.6-2A4.5 4.5 0 0 1 17 18H7z" />
    </svg>
  );
}

function DatabaseIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <ellipse cx="12" cy="5" rx="7" ry="2.5" />
      <path d="M5 5v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V5M5 11v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
    </svg>
  );
}

function BrainIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 4a2.5 2.5 0 0 0-2.5 2.5V7A2.5 2.5 0 0 0 4 9.5a2.5 2.5 0 0 0 1 4 2.5 2.5 0 0 0 2 4A2.5 2.5 0 0 0 9 20V6.5A2.5 2.5 0 0 0 9 4z" />
      <path d="M15 4a2.5 2.5 0 0 1 2.5 2.5V7A2.5 2.5 0 0 1 20 9.5a2.5 2.5 0 0 1-1 4 2.5 2.5 0 0 1-2 4 2.5 2.5 0 0 1-2.5 2.5V6.5A2.5 2.5 0 0 1 15 4z" />
    </svg>
  );
}

function GearCheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10" cy="10" r="6" />
      <path d="M10 3v1.3M10 15.7V17M17 10h-1.3M4.3 10H3M15.2 4.8l-0.9 0.9M5.7 14.3l-0.9 0.9M15.2 15.2l-0.9-0.9M5.7 5.7l-0.9-0.9" />
      <path d="M16 17l2 2 4-4" />
    </svg>
  );
}

function GuestIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20c0-3.9 3.1-7 7-7s7 3.1 7 7" />
    </svg>
  );
}

const TECH_BADGES = [
  { icon: SparkleIcon, label: "Gemini 3" },
  { icon: LinkIcon, label: "Google ADK" },
  { icon: CloudRunIcon, label: "Cloud Run" },
  { icon: DatabaseIcon, label: "Firestore" },
];

const FEATURES = [
  {
    icon: ShieldIcon,
    title: "Safety Policy Engine",
    description:
      "LOW risk executes automatically. Everything else waits for a human. Unknown or HIGH risk actions are never executed — no exceptions.",
  },
  {
    icon: HistoryIcon,
    title: "Incident Memory",
    description:
      "Every diagnosis is checked against past incidents — successes and failures — so the agent never blindly repeats a fix that already failed.",
  },
  {
    icon: AuditIcon,
    title: "Full Audit Trail",
    description:
      "Every decision — who approved it, why the policy engine allowed or blocked it, which tools the agent used — is recorded and explorable.",
  },
  {
    icon: SlidersIcon,
    title: "Autonomy You Control",
    description:
      "Observe Only, Recommend Only, Approval Required, or Autonomous Low-Risk — plus a global kill switch that stops automation instantly.",
  },
];

const STEPS = [
  { label: "Observe", detail: "Health checks, logs, and config are pulled from the live service.", icon: SearchIcon },
  { label: "Diagnose", detail: "Gemini 3 proposes a root cause and a remediation action.", icon: BrainIcon },
  {
    label: "Decide",
    detail: "A deterministic policy engine — not the model — decides what happens next.",
    icon: ShieldIcon,
    badge: "Safety Engine",
  },
  { label: "Act & Verify", detail: "The fix runs, health is re-checked, and the result is recorded.", icon: GearCheckIcon },
];

export default function WelcomePage() {
  const { user, loading, isGuest, signInWithGoogle, continueAsGuest, signOut } = useAuth();
  const router = useRouter();
  const [signingIn, setSigningIn] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // A previously-chosen guest session skips straight to the app — that
    // choice was already explicit. A signed-in Google session still stops
    // here, so someone else's account left logged in on this browser gets
    // a chance to continue as guest or switch accounts instead of being
    // silently redirected in as that user.
    if (!loading && isGuest) {
      router.replace("/overview");
    }
  }, [loading, isGuest, router]);

  async function handleSignIn() {
    setSigningIn(true);
    setError(null);
    try {
      await signInWithGoogle();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSigningIn(false);
    }
  }

  function handleGuest() {
    continueAsGuest();
    router.replace("/overview");
  }

  function handleContinue() {
    router.replace("/overview");
  }

  async function handleSwitchAccount() {
    await signOut();
    await handleSignIn();
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--color-bg)]">
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-[-10%] h-[560px] w-[900px] -translate-x-1/2 rounded-full opacity-30 blur-[120px]"
        style={{ background: "radial-gradient(circle, var(--color-primary), transparent 65%)" }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute right-[5%] top-[20%] h-[380px] w-[380px] rounded-full opacity-20 blur-[100px]"
        style={{ background: "radial-gradient(circle, var(--color-accent), transparent 65%)" }}
      />

      <div className="relative mx-auto max-w-6xl px-6 py-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Logo />
          <div className="hidden items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)]/60 px-3 py-1.5 text-xs font-medium text-[var(--color-text-secondary)] backdrop-blur md:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-success)]" />
            Autonomous Incident Response
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {TECH_BADGES.map((t) => {
              const Icon = t.icon;
              return (
                <div
                  key={t.label}
                  className="flex items-center gap-1.5 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)]/60 px-2.5 py-1 text-[11px] font-medium text-[var(--color-text-secondary)] backdrop-blur"
                >
                  <span className="text-[var(--color-accent)]">
                    <Icon />
                  </span>
                  {t.label}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="relative mx-auto flex max-w-5xl flex-col items-center px-6 pb-20 pt-8 text-center">
        <h1 className="max-w-3xl text-4xl font-bold leading-tight text-[var(--color-text-primary)] sm:text-5xl">
          An agent that investigates, decides, and acts —{" "}
          <span
            className="bg-clip-text text-transparent"
            style={{ backgroundImage: "linear-gradient(90deg, var(--color-accent), var(--color-primary))" }}
          >
            safely
          </span>
          .
        </h1>
        <p className="mt-5 max-w-xl text-base text-[var(--color-text-secondary)]">
          Observe, diagnose, act, verify, and re-plan — powered by Gemini 3 and Google ADK, gated by a
          deterministic safety policy engine that never trusts the model&apos;s own opinion of risk.
        </p>

        <div className="mt-10">
          {user ? (
            <div className="flex flex-col items-center gap-3">
              <div className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                {user.photoURL && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={user.photoURL}
                    alt=""
                    className="h-6 w-6 rounded-full"
                    referrerPolicy="no-referrer"
                  />
                )}
                <span>Signed in as {user.displayName ?? user.email}</span>
              </div>
              <button
                onClick={handleContinue}
                className="rounded-lg px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-black/20 transition hover:-translate-y-0.5 hover:shadow-xl"
                style={{ background: "var(--color-primary)" }}
              >
                Continue
              </button>
              <div className="flex items-center gap-4 text-xs">
                <button
                  onClick={handleGuest}
                  className="text-[var(--color-text-muted)] underline underline-offset-2 transition hover:text-[var(--color-text-secondary)]"
                >
                  Continue as guest instead
                </button>
                <span className="text-[var(--color-border)]">·</span>
                <button
                  onClick={handleSwitchAccount}
                  className="text-[var(--color-text-muted)] underline underline-offset-2 transition hover:text-[var(--color-text-secondary)]"
                >
                  Not you? Switch account
                </button>
              </div>
              {error && <p className="mt-1 text-xs text-[var(--color-critical)]">{error}</p>}
            </div>
          ) : (
            <>
              <button
                onClick={handleSignIn}
                disabled={signingIn || loading}
                className="flex items-center gap-3 rounded-lg bg-white px-6 py-3 text-sm font-semibold text-[#1f1f1f] shadow-lg shadow-black/20 transition hover:-translate-y-0.5 hover:shadow-xl disabled:opacity-60 disabled:hover:translate-y-0"
              >
                <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
                  <path
                    fill="#FFC107"
                    d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8c-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C12.955 4 4 12.955 4 24s8.955 20 20 20s20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"
                  />
                  <path
                    fill="#FF3D00"
                    d="m6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C16.318 4 9.656 8.337 6.306 14.691z"
                  />
                  <path
                    fill="#4CAF50"
                    d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z"
                  />
                  <path
                    fill="#1976D2"
                    d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002l6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z"
                  />
                </svg>
                {signingIn ? "Signing in..." : "Sign in with Google"}
              </button>
              {error && <p className="mt-3 text-xs text-[var(--color-critical)]">{error}</p>}
              <div className="mt-4 text-[11px] uppercase tracking-widest text-[var(--color-text-muted)]">or</div>
              <button
                onClick={handleGuest}
                className="mt-4 flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-6 py-3 text-sm font-semibold text-[var(--color-text-secondary)] transition hover:-translate-y-0.5 hover:border-[var(--color-primary)]/50 hover:text-[var(--color-text-primary)]"
              >
                <GuestIcon />
                Continue without signing in
              </button>
            </>
          )}
        </div>

        {/* How it works */}
        <div className="mt-24 w-full">
          <div className="mb-8 text-xs font-semibold uppercase tracking-widest text-[var(--color-text-muted)]">
            How it works — four steps, fully visible
          </div>
          <div className="grid gap-3 sm:grid-cols-4">
            {STEPS.map((step, i) => {
              const StepIcon = step.icon;
              const highlighted = Boolean(step.badge);
              return (
              <div key={step.label} className="relative">
                <div
                  className="flex h-full flex-col rounded-xl border p-4 text-left backdrop-blur transition hover:border-[var(--color-primary)]/50"
                  style={{
                    borderColor: highlighted ? "var(--color-blocked)" : "var(--color-border)",
                    background: highlighted
                      ? "color-mix(in srgb, var(--color-blocked) 8%, var(--color-surface))"
                      : "color-mix(in srgb, var(--color-surface) 70%, transparent)",
                  }}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <div
                      className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold"
                      style={{ background: highlighted ? "var(--color-blocked)" : "var(--color-primary)", color: "#fff" }}
                    >
                      {i + 1}
                    </div>
                    <span style={{ color: highlighted ? "var(--color-blocked)" : "var(--color-text-muted)" }}>
                      <StepIcon />
                    </span>
                  </div>
                  {step.badge && (
                    <div
                      className="mb-2 inline-flex w-fit items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
                      style={{ background: "color-mix(in srgb, var(--color-blocked) 20%, transparent)", color: "var(--color-blocked)" }}
                    >
                      {step.badge}
                    </div>
                  )}
                  <div className="mb-1 text-sm font-semibold text-[var(--color-text-primary)]">{step.label}</div>
                  <div className="text-xs leading-relaxed text-[var(--color-text-muted)]">{step.detail}</div>
                </div>
                {i < STEPS.length - 1 && (
                  <div
                    aria-hidden
                    className="absolute right-[-14px] top-1/2 hidden -translate-y-1/2 text-[var(--color-border)] sm:block"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M9 6l6 6-6 6" />
                    </svg>
                  </div>
                )}
              </div>
              );
            })}
          </div>
        </div>

        {/* Live dashboard preview */}
        <div className="mt-20 w-full">
          <div className="mb-8 text-xs font-semibold uppercase tracking-widest text-[var(--color-text-muted)]">
            What operators actually see
          </div>
          <div className="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/70 text-left backdrop-blur">
            <div className="flex items-center gap-2 border-b border-[var(--color-border)] px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-[var(--color-critical)]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[var(--color-warning)]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[var(--color-success)]" />
              <span className="ml-3 text-xs text-[var(--color-text-muted)]">payment-api — incident timeline</span>
            </div>
            <div className="grid gap-0 sm:grid-cols-[1.1fr_1fr]">
              <div className="space-y-3 border-b border-[var(--color-border)] p-5 sm:border-b-0 sm:border-r">
                {[
                  { t: "Diagnosis", d: "Root cause: missing DATABASE_URL env var (92% confidence).", c: "var(--color-text-secondary)" },
                  { t: "Safety Engine", d: "Policy decision: requires_approval (medium risk).", c: "var(--color-primary)" },
                  { t: "Human", d: "Elisa approved 'restore_env_var'.", c: "var(--color-success)" },
                  { t: "Resolved", d: "Service healthy again in 4.2s.", c: "var(--color-success)" },
                ].map((row) => (
                  <div key={row.t} className="flex gap-3 text-xs">
                    <span className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full" style={{ background: row.c }} />
                    <div>
                      <span className="font-semibold text-[var(--color-text-primary)]">{row.t}: </span>
                      <span className="text-[var(--color-text-muted)]">{row.d}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-5">
                <div className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
                  Safety verdict
                </div>
                <div className="mb-4 inline-flex items-center gap-2 rounded-lg border border-[var(--color-blocked)]/40 bg-[var(--color-blocked)]/10 px-3 py-2 text-xs font-semibold text-[var(--color-blocked)]">
                  rotate_credentials — BLOCKED
                </div>
                <div className="text-xs leading-relaxed text-[var(--color-text-muted)]">
                  The agent&apos;s own confidence is never enough — high-risk actions are escalated to a human, and
                  unknown actions are refused outright, regardless of what the model recommends.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature grid */}
        <div className="mt-20 grid w-full gap-4 sm:grid-cols-2">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/70 p-5 text-left backdrop-blur transition hover:-translate-y-0.5 hover:border-[var(--color-primary)]/50"
              >
                <div
                  className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg"
                  style={{ background: "color-mix(in srgb, var(--color-primary) 15%, transparent)", color: "var(--color-primary)" }}
                >
                  <Icon />
                </div>
                <div className="mb-1 text-sm font-semibold text-[var(--color-text-primary)]">{f.title}</div>
                <div className="text-xs leading-relaxed text-[var(--color-text-muted)]">{f.description}</div>
              </div>
            );
          })}
        </div>

        <div className="mt-16 text-xs text-[var(--color-text-muted)]">
          Built for the Google Cloud &quot;All Things Agentic&quot; hackathon — Taskmaster track.
        </div>
      </div>
    </div>
  );
}
