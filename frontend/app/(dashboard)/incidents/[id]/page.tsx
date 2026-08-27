"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  approveRemediation,
  getAnalytics,
  getIncident,
  getPostmortem,
  rejectRemediation,
} from "@/lib/api";
import type { AnalyticsData, IncidentResponse, Postmortem } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";
import { ActivityTimeline } from "@/app/components/ActivityTimeline";
import { EvidencePanel } from "@/app/components/EvidencePanel";
import { IncidentOverview } from "@/app/components/IncidentOverview";
import { RemediationPanel } from "@/app/components/RemediationPanel";
import { SimilarIncidents } from "@/app/components/SimilarIncidents";
import { Card, EmptyState, SectionLabel } from "@/app/components/ui";

export default function IncidentDetailPage() {
  const params = useParams<{ id: string }>();
  const incidentId = params.id;

  const [data, setData] = useState<IncidentResponse | null>(null);
  const [postmortem, setPostmortem] = useState<Postmortem | null>(null);
  const [postmortemLoading, setPostmortemLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const { user } = useAuth();
  const actorName = user?.displayName || user?.email || "guest";

  useEffect(() => {
    getAnalytics().then(setAnalytics);
  }, []);

  function refresh() {
    setLoading(true);
    fetchIncident();
  }

  function fetchIncident() {
    getIncident(incidentId)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchIncident();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incidentId]);

  async function handleApprove(remediationId: string) {
    setBusy(true);
    setError(null);
    try {
      setData(await approveRemediation(incidentId, remediationId, actorName));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleReject(remediationId: string) {
    setBusy(true);
    setError(null);
    try {
      setData(await rejectRemediation(incidentId, remediationId, actorName));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleGeneratePostmortem() {
    setPostmortemLoading(true);
    try {
      setPostmortem(await getPostmortem(incidentId));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPostmortemLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="px-8 py-8">
        <EmptyState>Loading incident...</EmptyState>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="px-8 py-8">
        <div className="rounded-lg border border-[var(--color-critical)]/30 bg-[var(--color-critical)]/10 p-4 text-sm text-[var(--color-critical)]">
          {error}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const latestRemediation = data.remediations[data.remediations.length - 1];

  return (
    <div className="px-8 py-8">
      <Link href="/incidents" className="text-xs text-[var(--color-text-muted)] hover:underline">
        ← Back to incidents
      </Link>
      <header className="mb-6 mt-2 flex items-center justify-between">
        <h1 className="font-mono text-lg text-[var(--color-text-muted)]">INC-{data.incident.id.slice(0, 8)}</h1>
        <button onClick={refresh} className="text-xs text-[var(--color-text-muted)] hover:underline">
          Refresh
        </button>
      </header>

      {error && (
        <div className="mb-4 rounded-lg border border-[var(--color-critical)]/30 bg-[var(--color-critical)]/10 p-4 text-sm text-[var(--color-critical)]">
          {error}
        </div>
      )}

      <div className="flex flex-col gap-6">
        <IncidentOverview incident={data.incident} />

        {latestRemediation && (
          <RemediationPanel
            remediation={latestRemediation}
            onApprove={() => handleApprove(latestRemediation.id)}
            onReject={() => handleReject(latestRemediation.id)}
            busy={busy}
          />
        )}

        <EvidencePanel
          incident={data.incident}
          remediation={latestRemediation}
          successRate={analytics?.remediation_success_rate.find((r) => r.action === latestRemediation?.action)}
        />

        <SimilarIncidents items={data.incident.similar_incidents} />

        {data.incident.status === "resolved" && (
          <Card>
            <SectionLabel>Postmortem</SectionLabel>
            {postmortem ? (
              <p className="text-sm leading-relaxed text-[var(--color-text-secondary)]">{postmortem.summary}</p>
            ) : (
              <button
                onClick={handleGeneratePostmortem}
                disabled={postmortemLoading}
                className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)] disabled:opacity-50"
              >
                {postmortemLoading ? "Generating..." : "Generate postmortem"}
              </button>
            )}
          </Card>
        )}

        <ActivityTimeline events={data.events} />
      </div>
    </div>
  );
}
