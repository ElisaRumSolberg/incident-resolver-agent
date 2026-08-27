"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

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
  { label: "Observe", detail: "Health checks, logs, and config are pulled from the live service." },
  { label: "Diagnose", detail: "Gemini 3 proposes a root cause and a remediation action." },
  { label: "Decide", detail: "A deterministic policy engine — not the model — decides what happens next." },
  { label: "Act & Verify", detail: "The fix runs, health is re-checked, and the result is recorded." },
];

export default function WelcomePage() {
  const { user, loading, isGuest, signInWithGoogle, continueAsGuest } = useAuth();
  const router = useRouter();
  const [signingIn, setSigningIn] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && (user || isGuest)) {
      router.replace("/overview");
    }
  }, [loading, user, isGuest, router]);

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

      <div className="relative mx-auto flex max-w-5xl flex-col items-center px-6 py-20 text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)]/60 px-3 py-1 text-[11px] font-semibold uppercase tracking-widest text-[var(--color-accent)] backdrop-blur">
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-accent)]" />
          Autonomous Incident Resolver
        </div>
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
          <div className="mt-4">
            <button
              onClick={handleGuest}
              className="text-xs text-[var(--color-text-muted)] underline underline-offset-2 transition hover:text-[var(--color-text-secondary)]"
            >
              Continue without signing in
            </button>
          </div>
        </div>

        {/* How it works */}
        <div className="mt-24 w-full">
          <div className="mb-8 text-xs font-semibold uppercase tracking-widest text-[var(--color-text-muted)]">
            How it works — four steps, fully visible
          </div>
          <div className="grid gap-3 sm:grid-cols-4">
            {STEPS.map((step, i) => (
              <div key={step.label} className="relative">
                <div className="flex h-full flex-col rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/70 p-4 text-left backdrop-blur transition hover:border-[var(--color-primary)]/50">
                  <div
                    className="mb-3 flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold"
                    style={{ background: "var(--color-primary)", color: "#fff" }}
                  >
                    {i + 1}
                  </div>
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
            ))}
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
