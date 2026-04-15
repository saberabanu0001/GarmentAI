"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { getHrDashboard } from "@/lib/api/hr";
import { postRag } from "@/lib/api/rag";
import { HrDashboardEditor } from "@/components/hr/HrDashboardEditor";
import type { HrCategoryVariant, HrDashboardResponse } from "@/lib/types/hr";

const badgeStyles: Record<HrCategoryVariant, string> = {
  overtime: "bg-red-50 text-red-700 ring-red-100",
  identity: "bg-blue-50 text-blue-700 ring-blue-100",
  wage: "bg-amber-50 text-amber-800 ring-amber-100",
  ppe: "bg-violet-50 text-violet-800 ring-violet-100",
};

const HR_RAG_ROLE = "hr_staff";

export function HrDashboardClient() {
  const { token } = useAuth();
  const [data, setData] = useState<HrDashboardResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [ragAnswer, setRagAnswer] = useState<string | null>(null);
  const [ragPending, setRagPending] = useState(false);
  const [ragError, setRagError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    getHrDashboard()
      .then((d) => {
        if (!cancelled) {
          setData(d);
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setLoadError(
            e instanceof Error
              ? e.message
              : "Could not load HR dashboard. Is the API running on NEXT_PUBLIC_API_URL?",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const askHr = useCallback(async (question: string) => {
    const q = question.trim();
    if (!q || ragPending) return;
    setRagError(null);
    setRagPending(true);
    try {
      const res = await postRag({
        question: q,
        role: HR_RAG_ROLE,
        top_k: 5,
      });
      setRagAnswer(res.answer);
    } catch (e) {
      setRagError(e instanceof Error ? e.message : "RAG request failed");
      setRagAnswer(null);
    } finally {
      setRagPending(false);
    }
  }, [ragPending]);

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl space-y-6 animate-pulse">
        <div className="h-8 w-64 rounded bg-zinc-200" />
        <div className="grid gap-4 md:grid-cols-3">
          <div className="h-28 rounded-xl bg-zinc-200" />
          <div className="h-28 rounded-xl bg-zinc-200" />
          <div className="h-28 rounded-xl bg-zinc-200" />
        </div>
        <div className="h-64 rounded-xl bg-zinc-200" />
      </div>
    );
  }

  if (loadError || !data) {
    return (
      <div className="mx-auto max-w-7xl rounded-xl border border-red-200 bg-red-50 p-6 text-red-900">
        <h1 className="text-lg font-semibold">HR dashboard unavailable</h1>
        <p className="mt-2 text-sm">{loadError}</p>
        <p className="mt-3 text-sm text-red-800/90">
          Start the API from the repo root:{" "}
            <code className="rounded bg-red-100 px-1 py-0.5 text-xs">
            uvicorn backend.main:app --port 5050
          </code>
        </p>
      </div>
    );
  }

  const o = data.overview;
  const reg = data.regulatoryUpdate;
  const asst = data.assistant;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Compliance Overview</h1>
          <p className="mt-1 text-sm text-zinc-600">
            HR intelligence —{" "}
            <code className="rounded bg-zinc-100 px-1 py-0.5 text-xs">GET /api/hr/dashboard</code>{" "}
            is public for demos;{" "}
            <code className="rounded bg-zinc-100 px-1 py-0.5 text-xs">PUT</code> requires a
            signed-in HR account (JWT). Data file:{" "}
            <code className="text-xs">data/hr_dashboard.json</code>. Assistant uses{" "}
            <code className="rounded bg-zinc-100 px-1 py-0.5 text-xs">POST /api/chat</code>{" "}
            (role <code className="text-xs">{HR_RAG_ROLE}</code>).
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/library"
            className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white px-4 text-sm font-semibold text-zinc-800 shadow-sm hover:bg-zinc-50"
          >
            Document library
          </Link>
          <Link
            href="/audit"
            className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-[#004D40] px-4 text-sm font-semibold text-white shadow hover:bg-[#00695c]"
          >
            <Plus className="size-4" />
            Factory audit
          </Link>
        </div>
      </div>

      <HrDashboardEditor
        initial={data}
        onSaved={(next) => setData(next)}
        accessToken={token}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl bg-white p-5 shadow-md">
          <div className="text-xs font-semibold uppercase text-zinc-500">
            Total workforce
          </div>
          <div className="mt-2 text-3xl font-bold text-zinc-900">
            {o.workforceTotal}
          </div>
          <div className="mt-1 text-xs font-medium text-emerald-700">
            {o.workforceTrendLabel}
          </div>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-md ring-1 ring-red-100">
          <div className="text-xs font-semibold uppercase text-zinc-500">
            Active violations
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-[#c62828]">
              {o.activeViolations}
            </span>
            <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700">
              Critical
            </span>
          </div>
          <p className="mt-2 text-xs text-zinc-600">{data.violationsNote}</p>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-md">
          <div className="text-xs font-semibold uppercase text-zinc-500">
            Pending audits
          </div>
          <div className="mt-2 text-3xl font-bold text-zinc-900">
            {o.pendingAudits}
          </div>
          <p className="mt-1 text-xs text-zinc-600">{o.pendingAuditsHint}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="overflow-hidden rounded-xl bg-white shadow-md">
          <div className="border-b border-zinc-100 px-5 py-4">
            <h2 className="font-semibold text-zinc-900">AI automated audit log</h2>
            <p className="text-xs text-zinc-500">
              Rows come from your saved dashboard (expand “Edit factory dashboard data” above).
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-zinc-50 text-xs font-semibold uppercase text-zinc-500">
                <tr>
                  <th className="px-5 py-3">Timestamp</th>
                  <th className="px-5 py-3">Category</th>
                  <th className="px-5 py-3">Incident</th>
                  <th className="px-5 py-3">Confidence</th>
                  <th className="px-5 py-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {data.auditLog.map((row) => (
                  <tr
                    key={row.id}
                    className="border-t border-zinc-100 hover:bg-zinc-50/60"
                  >
                    <td className="whitespace-nowrap px-5 py-3 text-zinc-600">
                      {row.timestampLabel}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${badgeStyles[row.categoryVariant]}`}
                      >
                        {row.category}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-zinc-700">{row.summary}</td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-20 overflow-hidden rounded-full bg-zinc-100">
                          <div
                            className="h-full rounded-full bg-[#004D40]"
                            style={{ width: `${row.confidencePct}%` }}
                          />
                        </div>
                        <span className="text-xs text-zinc-600">
                          {row.confidencePct}%
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <button
                        type="button"
                        className="text-xs font-semibold text-[#004D40] hover:underline"
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-zinc-100 bg-white p-4 shadow-md">
            <h3 className="text-sm font-semibold text-zinc-900">
              Compliance AI assistant
            </h3>
            <p className="mt-2 text-xs leading-relaxed text-zinc-600">
              {asst.welcome}
            </p>
            <div className="mt-3 flex flex-col gap-2">
              <button
                type="button"
                disabled={ragPending}
                onClick={() => askHr(asst.suggestedPrompt)}
                className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-left text-xs text-zinc-700 hover:border-[#004D40]/30 disabled:opacity-60"
              >
                {ragPending ? "Asking…" : asst.suggestedPrompt}
              </button>
            </div>
            {ragError ? (
              <p className="mt-2 text-xs text-red-700" role="alert">
                {ragError}
              </p>
            ) : null}
            {ragAnswer ? (
              <div className="mt-3 max-h-48 overflow-y-auto rounded-lg border border-zinc-100 bg-zinc-50/80 p-3 text-xs leading-relaxed text-zinc-800">
                {ragAnswer}
              </div>
            ) : null}
          </div>
          <div className="rounded-xl bg-[#004D40] p-4 text-white shadow-md">
            <div className="text-xs font-semibold uppercase text-white/80">
              {reg.title}
            </div>
            <p className="mt-2 text-sm text-white/95">{reg.body}</p>
            <button
              type="button"
              disabled={ragPending}
              onClick={() => askHr(reg.briefQuestion)}
              className="mt-3 text-left text-xs font-bold uppercase tracking-wide text-white/90 hover:underline disabled:opacity-60"
            >
              {ragPending ? "Loading…" : reg.ctaLabel}
            </button>
            {ragAnswer && !ragError ? (
              <p className="mt-2 text-[11px] text-white/70">
                See assistant panel for the latest answer.
              </p>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
