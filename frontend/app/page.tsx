"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

const FEATURES = [
  {
    icon: "◆",
    title: "Safety Policy Engine",
    description:
      "LOW risk executes automatically. Everything else waits for a human. Unknown or HIGH risk actions are never executed — no exceptions.",
  },
  {
    icon: "◎",
    title: "Incident Memory",
    description:
      "Every diagnosis is checked against past incidents — successes and failures — so the agent never blindly repeats a fix that already failed.",
  },
  {
    icon: "▤",
    title: "Full Audit Trail",
    description:
      "Every decision — who approved it, why the policy engine allowed or blocked it, which tools the agent used — is recorded and explorable.",
  },
  {
    icon: "⚠",
    title: "Autonomy You Control",
    description:
      "Observe Only, Recommend Only, Approval Required, or Autonomous Low-Risk — plus a global kill switch that stops automation instantly.",
  },
];

export default function WelcomePage() {
  const { user, loading, signInWithGoogle } = useAuth();
  const router = useRouter();
  const [signingIn, setSigningIn] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/overview");
    }
  }, [loading, user, router]);

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

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <div className="mx-auto flex max-w-5xl flex-col items-center px-6 py-20 text-center">
        <div className="mb-3 text-xs font-semibold uppercase tracking-widest text-[var(--color-accent)]">
          Autonomous Incident Resolver
        </div>
        <h1 className="max-w-3xl text-4xl font-bold leading-tight text-[var(--color-text-primary)] sm:text-5xl">
          An agent that investigates, decides, and acts —{" "}
          <span style={{ color: "var(--color-accent)" }}>safely</span>.
        </h1>
        <p className="mt-5 max-w-xl text-base text-[var(--color-text-secondary)]">
          Observe, diagnose, act, verify, and re-plan — powered by Gemini 3 and Google ADK, gated by a
          deterministic safety policy engine that never trusts the model&apos;s own opinion of risk.
        </p>

        <div className="mt-10">
          <button
            onClick={handleSignIn}
            disabled={signingIn || loading}
            className="flex items-center gap-3 rounded-lg bg-white px-6 py-3 text-sm font-semibold text-[#1f1f1f] shadow-lg transition hover:shadow-xl disabled:opacity-60"
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
        </div>

        <div className="mt-20 grid w-full gap-4 sm:grid-cols-2">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 text-left"
            >
              <div className="mb-2 text-lg" style={{ color: "var(--color-primary)" }}>
                {f.icon}
              </div>
              <div className="mb-1 text-sm font-semibold text-[var(--color-text-primary)]">{f.title}</div>
              <div className="text-xs leading-relaxed text-[var(--color-text-muted)]">{f.description}</div>
            </div>
          ))}
        </div>

        <div className="mt-16 text-xs text-[var(--color-text-muted)]">
          Built for the Google Cloud &quot;All Things Agentic&quot; hackathon — Taskmaster track.
        </div>
      </div>
    </div>
  );
}
