"use client";

import { useEffect, useState } from "react";
import { getSettings, setAutonomyMode, setKillSwitch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { AutonomyMode, GlobalSettings } from "@/lib/types";
import { Card, SectionLabel } from "./ui";

const MODES: { id: AutonomyMode; label: string; description: string }[] = [
  { id: "observe_only", label: "Observe Only", description: "Investigates and diagnoses. Never proposes execution." },
  { id: "recommend_only", label: "Recommend Only", description: "Proposes a fix but never asks to run it." },
  { id: "approval_required", label: "Approval Required", description: "Every action, even LOW risk, waits for a human." },
  { id: "autonomous_low_risk", label: "Autonomous Low-Risk", description: "LOW risk runs automatically; everything else needs approval." },
];

function formatTime(iso: string | null): string {
  if (!iso) return "never";
  try {
    return new Date(iso).toLocaleString([], { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export function AutonomyControls() {
  const [settings, setSettings] = useState<GlobalSettings | null>(null);
  const [busy, setBusy] = useState(false);
  const { user } = useAuth();
  const actorName = user?.displayName || user?.email || "dashboard user";

  useEffect(() => {
    getSettings().then(setSettings);
  }, []);

  async function handleModeChange(mode: AutonomyMode) {
    setBusy(true);
    try {
      setSettings(await setAutonomyMode(mode, actorName));
    } finally {
      setBusy(false);
    }
  }

  async function handleKillSwitchToggle() {
    if (!settings) return;
    setBusy(true);
    try {
      setSettings(await setKillSwitch(!settings.kill_switch_enabled, actorName));
    } finally {
      setBusy(false);
    }
  }

  if (!settings) return null;

  return (
    <div className="mb-6 grid gap-4 lg:grid-cols-2">
      <Card>
        <SectionLabel>Autonomy mode</SectionLabel>
        <div className="grid gap-2 sm:grid-cols-2">
          {MODES.map((m) => {
            const active = settings.autonomy_mode === m.id;
            return (
              <button
                key={m.id}
                disabled={busy}
                onClick={() => handleModeChange(m.id)}
                className="rounded-lg border p-3 text-left transition disabled:opacity-50"
                style={{
                  borderColor: active ? "var(--color-primary)" : "var(--color-border)",
                  background: active
                    ? "color-mix(in srgb, var(--color-primary) 15%, transparent)"
                    : "var(--color-surface-elevated)",
                }}
              >
                <div
                  className="text-sm font-semibold"
                  style={{ color: active ? "var(--color-primary)" : "var(--color-text-primary)" }}
                >
                  {m.label}
                </div>
                <div className="mt-1 text-xs text-[var(--color-text-muted)]">{m.description}</div>
              </button>
            );
          })}
        </div>
        <div className="mt-3 text-xs text-[var(--color-text-muted)]">
          Last changed {formatTime(settings.autonomy_mode_changed_at)}
          {settings.autonomy_mode_changed_by && ` by ${settings.autonomy_mode_changed_by}`}
        </div>
      </Card>

      <Card>
        <SectionLabel>Global kill switch</SectionLabel>
        <div className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-4">
          <div>
            <div
              className="text-lg font-bold"
              style={{ color: settings.kill_switch_enabled ? "var(--color-critical)" : "var(--color-success)" }}
            >
              Automation {settings.kill_switch_enabled ? "OFF" : "ON"}
            </div>
            <div className="mt-1 text-xs text-[var(--color-text-muted)]">
              Monitoring, investigation, and recommendations always keep running — this only stops
              automatic execution.
            </div>
          </div>
          <button
            onClick={handleKillSwitchToggle}
            disabled={busy}
            className="shrink-0 rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            style={{ background: settings.kill_switch_enabled ? "var(--color-success)" : "var(--color-critical)" }}
          >
            {settings.kill_switch_enabled ? "Re-enable automation" : "Disable automatic actions"}
          </button>
        </div>
        <div className="mt-3 text-xs text-[var(--color-text-muted)]">
          Last changed {formatTime(settings.kill_switch_changed_at)}
          {settings.kill_switch_changed_by && ` by ${settings.kill_switch_changed_by}`}
        </div>
      </Card>
    </div>
  );
}
