"use client";

import { useCallback, useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Plus, Trash2 } from "lucide-react";
import { putHrDashboard } from "@/lib/api/hr";
import type {
  HrAuditLogRow,
  HrCategoryVariant,
  HrDashboardResponse,
} from "@/lib/types/hr";

const CATEGORY_VARIANTS: HrCategoryVariant[] = [
  "overtime",
  "identity",
  "wage",
  "ppe",
];

type Props = {
  initial: HrDashboardResponse;
  onSaved: (next: HrDashboardResponse) => void;
};

function emptyRow(): HrAuditLogRow {
  return {
    id: crypto.randomUUID().slice(0, 8),
    timestampLabel: "",
    category: "",
    categoryVariant: "overtime",
    summary: "",
    confidencePct: 80,
  };
}

export function HrDashboardEditor({ initial, onSaved }: Props) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<HrDashboardResponse>(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) setDraft(structuredClone(initial));
  }, [initial, open]);

  const updateOverview = useCallback(
    (field: keyof HrDashboardResponse["overview"], value: string | number) => {
      setDraft((d) => ({
        ...d,
        overview: { ...d.overview, [field]: value },
      }));
    },
    [],
  );

  const save = useCallback(async () => {
    setError(null);
    setSaving(true);
    try {
      const next = await putHrDashboard(draft);
      onSaved(next);
      setOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }, [draft, onSaved]);

  const inputCls =
    "mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 outline-none ring-[#004D40] focus:ring-2";

  return (
    <div className="rounded-xl border border-zinc-200 bg-zinc-50/80 shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-zinc-800"
      >
        <span>
          Edit factory dashboard data
          <span className="ml-2 font-normal text-zinc-500">
            (saved to server as <code className="text-xs">data/hr_dashboard.json</code>)
          </span>
        </span>
        {open ? (
          <ChevronUp className="size-5 text-zinc-500" />
        ) : (
          <ChevronDown className="size-5 text-zinc-500" />
        )}
      </button>
      {open ? (
        <div className="space-y-6 border-t border-zinc-200 px-4 py-4">
          <section>
            <h3 className="text-xs font-bold uppercase tracking-wide text-zinc-500">
              Overview cards
            </h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <label className="block text-xs text-zinc-600">
                Total workforce
                <input
                  type="number"
                  min={0}
                  className={inputCls}
                  value={draft.overview.workforceTotal}
                  onChange={(e) =>
                    updateOverview("workforceTotal", Number(e.target.value) || 0)
                  }
                />
              </label>
              <label className="block text-xs text-zinc-600 sm:col-span-2">
                Workforce trend label
                <input
                  type="text"
                  className={inputCls}
                  value={draft.overview.workforceTrendLabel}
                  onChange={(e) =>
                    updateOverview("workforceTrendLabel", e.target.value)
                  }
                />
              </label>
              <label className="block text-xs text-zinc-600">
                Active violations
                <input
                  type="number"
                  min={0}
                  className={inputCls}
                  value={draft.overview.activeViolations}
                  onChange={(e) =>
                    updateOverview("activeViolations", Number(e.target.value) || 0)
                  }
                />
              </label>
              <label className="block text-xs text-zinc-600">
                Pending audits
                <input
                  type="number"
                  min={0}
                  className={inputCls}
                  value={draft.overview.pendingAudits}
                  onChange={(e) =>
                    updateOverview("pendingAudits", Number(e.target.value) || 0)
                  }
                />
              </label>
              <label className="block text-xs text-zinc-600 sm:col-span-2">
                Pending audits hint
                <input
                  type="text"
                  className={inputCls}
                  value={draft.overview.pendingAuditsHint}
                  onChange={(e) =>
                    updateOverview("pendingAuditsHint", e.target.value)
                  }
                />
              </label>
            </div>
            <label className="mt-3 block text-xs text-zinc-600">
              Violations note (under “Critical” card)
              <textarea
                rows={2}
                className={inputCls}
                value={draft.violationsNote}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, violationsNote: e.target.value }))
                }
              />
            </label>
          </section>

          <section>
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wide text-zinc-500">
                Audit log rows
              </h3>
              <button
                type="button"
                onClick={() =>
                  setDraft((d) => ({
                    ...d,
                    auditLog: [...d.auditLog, emptyRow()],
                  }))
                }
                className="inline-flex items-center gap-1 rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs font-medium text-zinc-700 hover:border-[#004D40]/40"
              >
                <Plus className="size-3.5" />
                Add row
              </button>
            </div>
            <div className="mt-3 space-y-4">
              {draft.auditLog.map((row, idx) => (
                <div
                  key={row.id}
                  className="rounded-lg border border-zinc-200 bg-white p-3 shadow-sm"
                >
                  <div className="mb-2 flex justify-end">
                    <button
                      type="button"
                      aria-label="Remove row"
                      onClick={() =>
                        setDraft((d) => ({
                          ...d,
                          auditLog: d.auditLog.filter((_, i) => i !== idx),
                        }))
                      }
                      className="rounded p-1 text-zinc-400 hover:bg-red-50 hover:text-red-600"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <label className="block text-xs text-zinc-600">
                      Row ID
                      <input
                        type="text"
                        className={inputCls}
                        value={row.id}
                        onChange={(e) =>
                          setDraft((d) => {
                            const next = [...d.auditLog];
                            next[idx] = { ...next[idx], id: e.target.value };
                            return { ...d, auditLog: next };
                          })
                        }
                      />
                    </label>
                    <label className="block text-xs text-zinc-600">
                      Timestamp label
                      <input
                        type="text"
                        className={inputCls}
                        placeholder="e.g. Today 2:30 PM"
                        value={row.timestampLabel}
                        onChange={(e) =>
                          setDraft((d) => {
                            const next = [...d.auditLog];
                            next[idx] = {
                              ...next[idx],
                              timestampLabel: e.target.value,
                            };
                            return { ...d, auditLog: next };
                          })
                        }
                      />
                    </label>
                    <label className="block text-xs text-zinc-600">
                      Category (badge text)
                      <input
                        type="text"
                        className={inputCls}
                        placeholder="OVERTIME"
                        value={row.category}
                        onChange={(e) =>
                          setDraft((d) => {
                            const next = [...d.auditLog];
                            next[idx] = { ...next[idx], category: e.target.value };
                            return { ...d, auditLog: next };
                          })
                        }
                      />
                    </label>
                    <label className="block text-xs text-zinc-600">
                      Badge style
                      <select
                        className={inputCls}
                        value={row.categoryVariant}
                        onChange={(e) =>
                          setDraft((d) => {
                            const next = [...d.auditLog];
                            next[idx] = {
                              ...next[idx],
                              categoryVariant: e.target.value as HrCategoryVariant,
                            };
                            return { ...d, auditLog: next };
                          })
                        }
                      >
                        {CATEGORY_VARIANTS.map((v) => (
                          <option key={v} value={v}>
                            {v}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="block text-xs text-zinc-600 sm:col-span-2">
                      Incident summary
                      <textarea
                        rows={2}
                        className={inputCls}
                        value={row.summary}
                        onChange={(e) =>
                          setDraft((d) => {
                            const next = [...d.auditLog];
                            next[idx] = { ...next[idx], summary: e.target.value };
                            return { ...d, auditLog: next };
                          })
                        }
                      />
                    </label>
                    <label className="block text-xs text-zinc-600">
                      Confidence %
                      <input
                        type="number"
                        min={0}
                        max={100}
                        className={inputCls}
                        value={row.confidencePct}
                        onChange={(e) =>
                          setDraft((d) => {
                            const next = [...d.auditLog];
                            next[idx] = {
                              ...next[idx],
                              confidencePct: Math.min(
                                100,
                                Math.max(0, Number(e.target.value) || 0),
                              ),
                            };
                            return { ...d, auditLog: next };
                          })
                        }
                      />
                    </label>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h3 className="text-xs font-bold uppercase tracking-wide text-zinc-500">
              Regulatory update card
            </h3>
            <div className="mt-3 grid gap-3">
              <label className="block text-xs text-zinc-600">
                Title
                <input
                  type="text"
                  className={inputCls}
                  value={draft.regulatoryUpdate.title}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      regulatoryUpdate: {
                        ...d.regulatoryUpdate,
                        title: e.target.value,
                      },
                    }))
                  }
                />
              </label>
              <label className="block text-xs text-zinc-600">
                Body
                <textarea
                  rows={3}
                  className={inputCls}
                  value={draft.regulatoryUpdate.body}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      regulatoryUpdate: {
                        ...d.regulatoryUpdate,
                        body: e.target.value,
                      },
                    }))
                  }
                />
              </label>
              <label className="block text-xs text-zinc-600">
                Button label
                <input
                  type="text"
                  className={inputCls}
                  value={draft.regulatoryUpdate.ctaLabel}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      regulatoryUpdate: {
                        ...d.regulatoryUpdate,
                        ctaLabel: e.target.value,
                      },
                    }))
                  }
                />
              </label>
              <label className="block text-xs text-zinc-600">
                Question sent to RAG when button is clicked
                <textarea
                  rows={2}
                  className={inputCls}
                  value={draft.regulatoryUpdate.briefQuestion}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      regulatoryUpdate: {
                        ...d.regulatoryUpdate,
                        briefQuestion: e.target.value,
                      },
                    }))
                  }
                />
              </label>
            </div>
          </section>

          <section>
            <h3 className="text-xs font-bold uppercase tracking-wide text-zinc-500">
              Assistant panel
            </h3>
            <div className="mt-3 grid gap-3">
              <label className="block text-xs text-zinc-600">
                Welcome text
                <textarea
                  rows={3}
                  className={inputCls}
                  value={draft.assistant.welcome}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      assistant: { ...d.assistant, welcome: e.target.value },
                    }))
                  }
                />
              </label>
              <label className="block text-xs text-zinc-600">
                Suggested prompt (button)
                <input
                  type="text"
                  className={inputCls}
                  value={draft.assistant.suggestedPrompt}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      assistant: {
                        ...d.assistant,
                        suggestedPrompt: e.target.value,
                      },
                    }))
                  }
                />
              </label>
            </div>
          </section>

          {error ? (
            <p className="text-sm text-red-700" role="alert">
              {error}
            </p>
          ) : null}

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={saving}
              onClick={save}
              className="rounded-xl bg-[#004D40] px-4 py-2 text-sm font-semibold text-white shadow hover:bg-[#00695c] disabled:opacity-60"
            >
              {saving ? "Saving…" : "Save dashboard"}
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => setOpen(false)}
              className="rounded-xl border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
