"use client";

import { useState } from "react";
import {
  approveRemediation,
  getIncident,
  rejectRemediation,
  resetDemo,
  startInvestigation,
  triggerDemoScenario,
} from "@/lib/api";
import { isHealthySnapshot, type IncidentResponse } from "@/lib/types";
import { ActivityTimeline } from "./components/ActivityTimeline";
import { IncidentOverview } from "./components/IncidentOverview";
import { RemediationPanel } from "./components/RemediationPanel";
import { ScenarioTrigger } from "./components/ScenarioTrigger";

export default function Home() {
  const [data, setData] = useState<IncidentResponse | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>(
    "Trigger a failure scenario below to see the agent investigate and resolve it."
  );
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleTrigger(scenario: string) {
    setLoading(true);
    setError(null);
    setData(null);
    setStatusMessage("Incident triggered. Agent is investigating...");
    try {
      await triggerDemoScenario(scenario);
      const result = await startInvestigation();
      if (isHealthySnapshot(result)) {
        setStatusMessage(result.message);
      } else {
        setData(result);
        setStatusMessage("");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    setLoading(true);
    setError(null);
    try {
      await resetDemo();
      setData(null);
      setStatusMessage("Demo service reset to healthy baseline.");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(remediationId: string) {
    if (!data) return;
    setBusy(true);
    setError(null);
    try {
      const result = await approveRemediation(data.incident.id, remediationId);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleReject(remediationId: string) {
    if (!data) return;
    setBusy(true);
    setError(null);
    try {
      const result = await rejectRemediation(data.incident.id, remediationId);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleRefresh() {
    if (!data) return;
    setError(null);
    try {
      const result = await getIncident(data.incident.id);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  const latestRemediation = data?.remediations[data.remediations.length - 1];

  return (
    <div className="min-h-screen bg-zinc-50 px-4 py-10 dark:bg-zinc-950">
      <main className="mx-auto flex max-w-3xl flex-col gap-6">
        <header>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            Autonomous Incident Resolver Agent
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            Observe → investigate → diagnose → act → verify → re-plan, powered by Gemini + Google ADK.
          </p>
        </header>

        <ScenarioTrigger onTrigger={handleTrigger} onReset={handleReset} disabled={loading} />

        {error && (
          <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </div>
        )}

        {loading && (
          <div className="rounded-xl border border-dashed border-zinc-300 p-6 text-center text-sm text-zinc-500 dark:border-zinc-700">
            Agent is investigating — reading logs, checking config, diagnosing root cause...
          </div>
        )}

        {!loading && !data && statusMessage && (
          <div className="rounded-xl border border-zinc-200 bg-white p-6 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900">
            {statusMessage}
          </div>
        )}

        {data && (
          <>
            <div className="flex justify-end">
              <button
                onClick={handleRefresh}
                className="text-xs font-medium text-zinc-500 underline hover:text-zinc-800 dark:hover:text-zinc-200"
              >
                Refresh
              </button>
            </div>
            <IncidentOverview incident={data.incident} />
            {latestRemediation && (
              <RemediationPanel
                remediation={latestRemediation}
                onApprove={() => handleApprove(latestRemediation.id)}
                onReject={() => handleReject(latestRemediation.id)}
                busy={busy}
              />
            )}
            <ActivityTimeline events={data.events} />
          </>
        )}
      </main>
    </div>
  );
}
