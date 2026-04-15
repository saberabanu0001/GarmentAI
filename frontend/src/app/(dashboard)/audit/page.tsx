"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, FileCheck2, Search, ShieldAlert } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { getHrDashboard } from "@/lib/api/hr";
import { postRag } from "@/lib/api/rag";
import type { RagHit } from "@/lib/types/rag";
import type { AppRole } from "@/lib/types/auth";
import type { HrDashboardResponse } from "@/lib/types/hr";

const QUICK_AUDIT_PROMPTS = [
  "Show me the latest fire safety audit report.",
  "What were the non-compliance issues last month?",
  "Show training evidence for new workers.",
  "What corrective actions were taken after the last inspection?",
  "Which department had safety violations recently?",
];

function roleForAuditRag(role: AppRole | undefined): "worker" | "hr_staff" | "compliance_officer" {
  if (role === "hr_staff") return "hr_staff";
  if (role === "compliance_officer") return "compliance_officer";
  return "worker";
}

export default function FactoryAuditPage() {
  const { user } = useAuth();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [hits, setHits] = useState<RagHit[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<HrDashboardResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    getHrDashboard()
      .then((d) => {
        if (!cancelled) setDashboard(d);
      })
      .catch(() => {
        if (!cancelled) setDashboard(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const auditRole = roleForAuditRag(user?.role);

  async function askAuditAi(nextQ: string) {
    const q = nextQ.trim();
    if (!q || pending) return;
    setPending(true);
    setError(null);
    try {
      const res = await postRag({
        question: q,
        role: auditRole,
        top_k: 10,
      });
      setQuestion(q);
      setAnswer(res.answer);
      setHits(res.hits);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Audit AI request failed");
      setAnswer(null);
      setHits([]);
    } finally {
      setPending(false);
    }
  }

  const evidenceHits = useMemo(() => hits.slice(0, 8), [hits]);

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-zinc-900">Factory audit assistant</h1>
        <p className="mt-2 max-w-4xl text-sm text-zinc-600">
          During sudden audits, HR often needs to search many PDFs and remember exact file names.
          This workspace reduces that pressure by retrieving evidence from indexed documents and
          helping you answer quickly with proof.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900">
              <Search className="size-4 text-[#004D40]" />
              Instant retrieval
            </div>
            <p className="mt-1 text-xs text-zinc-600">
              Find relevant findings from multiple reports in seconds.
            </p>
          </div>
          <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900">
              <FileCheck2 className="size-4 text-[#004D40]" />
              Evidence support
            </div>
            <p className="mt-1 text-xs text-zinc-600">
              Show source document and matching excerpts while responding to auditors.
            </p>
          </div>
          <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900">
              <ShieldAlert className="size-4 text-[#004D40]" />
              Reduced panic
            </div>
            <p className="mt-1 text-xs text-zinc-600">
              Ask naturally instead of searching folder-by-folder under pressure.
            </p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Link
            href="/library"
            className="inline-flex rounded-lg bg-[#004D40] px-4 py-2 text-sm font-semibold text-white hover:bg-[#00695c]"
          >
            Open document library
          </Link>
          <span className="text-xs text-zinc-500">
            Tip: Upload audit evidence under Compliance & legal for best retrieval.
          </span>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-zinc-900">Ask Audit AI</h2>
          <p className="mt-1 text-xs text-zinc-600">
            Ask exactly how an auditor asks. The answer is grounded in indexed evidence.
          </p>
          <div className="mt-3 flex flex-col gap-2 sm:flex-row">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What corrective actions were taken after the last fire safety audit?"
              className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm text-zinc-900"
            />
            <button
              type="button"
              onClick={() => void askAuditAi(question)}
              disabled={pending}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-800 disabled:opacity-60"
            >
              {pending ? "Asking…" : "Ask"}
            </button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {QUICK_AUDIT_PROMPTS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => void askAuditAi(p)}
                disabled={pending}
                className="rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs text-zinc-700 hover:bg-zinc-100 disabled:opacity-60"
              >
                {p}
              </button>
            ))}
          </div>

          {error ? (
            <p className="mt-3 rounded-lg border border-red-100 bg-red-50 p-2 text-xs text-red-700">
              {error}
            </p>
          ) : null}

          {answer ? (
            <div className="mt-4 rounded-xl border border-zinc-100 bg-zinc-50 p-4">
              <div className="text-xs font-semibold uppercase text-zinc-500">AI response</div>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-zinc-800">
                {answer}
              </p>
            </div>
          ) : null}
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-zinc-900">Evidence panel</h2>
            <p className="mt-1 text-xs text-zinc-600">
              Use these citations as proof while answering auditors.
            </p>
            {evidenceHits.length === 0 ? (
              <p className="mt-3 text-xs text-zinc-500">
                Ask a question to see supporting document excerpts.
              </p>
            ) : (
              <ul className="mt-3 space-y-2">
                {evidenceHits.map((h) => (
                  <li key={`${h.chunk_uid}-${h.rank}`} className="rounded-lg border border-zinc-100 p-2">
                    <p className="text-xs font-semibold text-zinc-800">
                      {h.document_name || h.source_name}
                    </p>
                    <p className="mt-1 text-[11px] text-zinc-600">
                      Score {(h.similarity * 100).toFixed(1)}% · {h.collection}
                    </p>
                    <p className="mt-1 line-clamp-3 text-xs text-zinc-700">{h.text}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-zinc-900">Recent non-compliance tracker</h2>
            {!dashboard ? (
              <p className="mt-2 text-xs text-zinc-500">Tracker will appear when dashboard data is available.</p>
            ) : (
              <>
                <p className="mt-1 text-xs text-zinc-600">
                  Active violations:{" "}
                  <span className="font-semibold text-red-700">{dashboard.overview.activeViolations}</span>
                </p>
                <ul className="mt-3 space-y-2">
                  {dashboard.auditLog.slice(0, 5).map((row) => (
                    <li key={row.id} className="rounded-lg border border-zinc-100 p-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-semibold text-zinc-800">{row.category}</span>
                        <span className="text-[11px] text-zinc-500">{row.timestampLabel}</span>
                      </div>
                      <p className="mt-1 text-xs text-zinc-700">{row.summary}</p>
                      <p className="mt-1 inline-flex items-center gap-1 text-[11px] text-amber-700">
                        <AlertTriangle className="size-3" />
                        Confidence {row.confidencePct}%
                      </p>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
      </section>
      <div className="pb-1 text-xs text-zinc-500">
        This assistant helps HR/compliance respond faster with evidence; final audit decisions stay human-owned.
      </div>
    </div>
  );
}
