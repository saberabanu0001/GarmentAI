"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { FileText, Filter, RefreshCw, Trash2, Upload } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  deleteHrDocument,
  getHrDocuments,
  queueHrDocumentIngest,
  updateHrDocumentCategory,
  uploadHrDocument,
} from "@/lib/api/hrDocuments";
import type {
  HrDocumentCategory,
  HrDocumentRow,
} from "@/lib/types/hrDocuments";

const CATEGORIES: Array<{ value: HrDocumentCategory; label: string }> = [
  { value: "employee", label: "Employee profiles" },
  { value: "recruitment", label: "Recruitment" },
  { value: "training", label: "Training materials" },
  { value: "compliance", label: "Compliance & legal" },
  { value: "performance", label: "Performance" },
  { value: "other", label: "General" },
];

type StatusFilter = "all" | "indexed" | "pending" | "failed";
type UiLanguage = "en" | "bn";

const UI_COPY = {
  en: {
    signInRequired: "Sign in required",
    signInHelp: "Document Library needs an authenticated session.",
    title: "Document library",
    subtitle:
      "Upload and organize HR documents by category. Files are indexed for AI retrieval after extraction, chunking, and E5 embedding.",
    uiLanguage: "UI language",
    category: "Category",
    uploadButton: "Upload document",
    uploading: "Uploading…",
    refresh: "Refresh",
    totalDocs: "Total docs",
    indexed: "Indexed",
    indexing: "Indexing",
    failed: "Failed",
    all: "All",
    searchPlaceholder: "Search by filename, uploader, category",
    status: "Status",
    noMatches: "No documents match this filter.",
    loadingDocs: "Loading documents…",
    indexedChunks: "Indexed",
    indexFailed: "Index failed",
    indexPending: "Indexing pending",
    uploadedBy: "Uploaded by",
    reindex: "Re-index",
    queuing: "Queuing…",
    moveTo: "Move to",
    save: "Save",
    saving: "Saving…",
    delete: "Delete",
    deleting: "Deleting…",
    confirmDelete: "Delete this document? This removes file + vectors and cannot be undone.",
    askAi: "Ask AI",
    english: "English",
    bangla: "Bangla",
  },
  bn: {
    signInRequired: "সাইন ইন প্রয়োজন",
    signInHelp: "ডকুমেন্ট লাইব্রেরি ব্যবহার করতে লগইন করতে হবে।",
    title: "ডকুমেন্ট লাইব্রেরি",
    subtitle:
      "ক্যাটাগরি অনুযায়ী HR ডকুমেন্ট আপলোড ও ম্যানেজ করুন। ফাইল এক্সট্র্যাক্ট, চাঙ্ক এবং E5 এমবেডিং হওয়ার পর AI রিট্রিভালের জন্য ইনডেক্স হয়।",
    uiLanguage: "ইউআই ভাষা",
    category: "ক্যাটাগরি",
    uploadButton: "ডকুমেন্ট আপলোড",
    uploading: "আপলোড হচ্ছে…",
    refresh: "রিফ্রেশ",
    totalDocs: "মোট ডকুমেন্ট",
    indexed: "ইনডেক্সড",
    indexing: "ইনডেক্সিং",
    failed: "ব্যর্থ",
    all: "সব",
    searchPlaceholder: "ফাইল নাম, আপলোডকারী, ক্যাটাগরি দিয়ে খুঁজুন",
    status: "স্ট্যাটাস",
    noMatches: "এই ফিল্টারে কোনো ডকুমেন্ট পাওয়া যায়নি।",
    loadingDocs: "ডকুমেন্ট লোড হচ্ছে…",
    indexedChunks: "ইনডেক্সড",
    indexFailed: "ইনডেক্স ব্যর্থ",
    indexPending: "ইনডেক্সিং চলছে",
    uploadedBy: "আপলোড করেছেন",
    reindex: "রি-ইনডেক্স",
    queuing: "কিউ হচ্ছে…",
    moveTo: "সেকশন বদলান",
    save: "সেভ",
    saving: "সেভ হচ্ছে…",
    delete: "ডিলিট",
    deleting: "ডিলিট হচ্ছে…",
    confirmDelete: "এই ডকুমেন্ট ডিলিট করবেন? ফাইল ও ভেক্টর মুছে যাবে, ফিরিয়ে আনা যাবে না।",
    askAi: "এআই জিজ্ঞাসা",
    english: "ইংরেজি",
    bangla: "বাংলা",
  },
} as const;

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(ts: string): string {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString();
}

function statusOf(doc: HrDocumentRow): StatusFilter {
  if (doc.chroma_error) return "failed";
  if (doc.chroma_indexed) return "indexed";
  return "pending";
}

export default function DocumentLibraryPage() {
  const { user, token, loading: authLoading } = useAuth();
  const [docs, setDocs] = useState<HrDocumentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState<"all" | HrDocumentCategory>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [uploadCategory, setUploadCategory] = useState<HrDocumentCategory>("compliance");
  const [uiLanguage, setUiLanguage] = useState<UiLanguage>("en");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [reindexId, setReindexId] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [categoryDraft, setCategoryDraft] = useState<Record<string, HrDocumentCategory>>({});

  const canUpload = user?.role === "hr_staff";
  const t = UI_COPY[uiLanguage];

  const refresh = useCallback(async () => {
    if (!token || !canUpload) {
      setDocs([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const rows = await getHrDocuments(token);
      setDocs(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load documents");
      setDocs([]);
    } finally {
      setLoading(false);
    }
  }, [token, canUpload]);

  useEffect(() => {
    if (authLoading) return;
    void refresh();
  }, [authLoading, refresh]);

  useEffect(() => {
    setCategoryDraft((prev) => {
      const next = { ...prev };
      for (const d of docs) {
        if (!next[d.id] && CATEGORIES.some((c) => c.value === d.category)) {
          next[d.id] = d.category as HrDocumentCategory;
        }
      }
      return next;
    });
  }, [docs]);

  const categoryCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const c of CATEGORIES) counts.set(c.value, 0);
    for (const d of docs) {
      const key = String(d.category);
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return counts;
  }, [docs]);

  const stats = useMemo(() => {
    let indexed = 0;
    let pending = 0;
    let failed = 0;
    for (const d of docs) {
      const st = statusOf(d);
      if (st === "indexed") indexed += 1;
      else if (st === "failed") failed += 1;
      else pending += 1;
    }
    return { total: docs.length, indexed, pending, failed };
  }, [docs]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return docs.filter((d) => {
      if (tab !== "all" && d.category !== tab) return false;
      const st = statusOf(d);
      if (statusFilter !== "all" && st !== statusFilter) return false;
      if (!q) return true;
      const hay = `${d.original_filename} ${d.uploaded_by} ${d.category}`.toLowerCase();
      return hay.includes(q);
    });
  }, [docs, query, statusFilter, tab]);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !token || !canUpload) return;
    setUploading(true);
    setUploadError(null);
    try {
      await uploadHrDocument(token, file, uploadCategory);
      await refresh();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const onSaveCategory = async (docId: string) => {
    if (!token) return;
    const nextCategory = categoryDraft[docId];
    if (!nextCategory) return;
    setSavingId(docId);
    try {
      await updateHrDocumentCategory(token, docId, nextCategory);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update document category");
    } finally {
      setSavingId(null);
    }
  };

  const onDeleteDocument = async (docId: string) => {
    if (!token) return;
    if (!window.confirm(t.confirmDelete)) return;
    setDeletingId(docId);
    try {
      await deleteHrDocument(token, docId);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete document");
    } finally {
      setDeletingId(null);
    }
  };

  if (authLoading) {
    return <div className="mx-auto max-w-6xl animate-pulse rounded-xl bg-zinc-200 p-12" />;
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-4xl rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-950">
        <p className="font-semibold">Sign in required</p>
        <p className="mt-2 text-amber-900/90">
          {t.signInHelp}
        </p>
      </div>
    );
  }

  if (!canUpload) {
    return (
      <div className="mx-auto max-w-4xl rounded-xl border border-zinc-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-bold text-zinc-900">Document library</h1>
        <p className="mt-2 text-sm text-zinc-600">
          Library management is currently enabled for HR Manager in this MVP. You can still
          use AI Chat to query indexed policies and manuals.
        </p>
        <Link
          href={user?.role === "worker" ? "/worker" : "/auditor/chat"}
          className="mt-4 inline-flex rounded-lg bg-[#004D40] px-4 py-2 text-sm font-semibold text-white hover:bg-[#00695c]"
        >
          Open AI chat
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900">{t.title}</h1>
            <p className="mt-1 max-w-3xl text-sm text-zinc-600">
              {t.subtitle}
            </p>
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <label className="text-xs font-medium text-zinc-600">
              {t.uiLanguage}
              <select
                value={uiLanguage}
                onChange={(e) => setUiLanguage(e.target.value as UiLanguage)}
                className="ml-2 rounded-lg border border-zinc-200 bg-white px-2 py-1.5 text-sm text-zinc-900"
              >
                <option value="en">{t.english}</option>
                <option value="bn">{t.bangla}</option>
              </select>
            </label>
            <label className="text-xs font-medium text-zinc-600">
              {t.category}
              <select
                value={uploadCategory}
                onChange={(e) => setUploadCategory(e.target.value as HrDocumentCategory)}
                className="ml-2 rounded-lg border border-zinc-200 bg-white px-2 py-1.5 text-sm text-zinc-900"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-[#004D40] px-3 py-2 text-sm font-semibold text-white hover:bg-[#00695c]">
              <Upload className="size-4" />
              {uploading ? t.uploading : t.uploadButton}
              <input
                type="file"
                className="hidden"
                disabled={uploading}
                onChange={onUpload}
              />
            </label>
            <button
              type="button"
              onClick={() => void refresh()}
              className="inline-flex items-center gap-1 rounded-lg border border-zinc-200 px-3 py-2 text-sm font-semibold text-zinc-700 hover:bg-zinc-50"
            >
              <RefreshCw className="size-4" />
              {t.refresh}
            </button>
          </div>
        </div>
        {uploadError ? <p className="mt-2 text-xs text-red-700">{uploadError}</p> : null}
        {error ? <p className="mt-2 text-xs text-red-700">{error}</p> : null}
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
          <p className="text-xs text-zinc-500">{t.totalDocs}</p>
          <p className="mt-1 text-2xl font-bold text-zinc-900">{stats.total}</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-white p-4 shadow-sm">
          <p className="text-xs text-zinc-500">{t.indexed}</p>
          <p className="mt-1 text-2xl font-bold text-emerald-700">{stats.indexed}</p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-white p-4 shadow-sm">
          <p className="text-xs text-zinc-500">{t.indexing}</p>
          <p className="mt-1 text-2xl font-bold text-amber-700">{stats.pending}</p>
        </div>
        <div className="rounded-xl border border-red-200 bg-white p-4 shadow-sm">
          <p className="text-xs text-zinc-500">{t.failed}</p>
          <p className="mt-1 text-2xl font-bold text-red-700">{stats.failed}</p>
        </div>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-100 px-4 py-3">
          <div className="mb-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setTab("all")}
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                tab === "all"
                  ? "bg-zinc-900 text-white"
                  : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
              }`}
            >
              {t.all} ({docs.length})
            </button>
            {CATEGORIES.map((c) => (
              <button
                key={c.value}
                type="button"
                onClick={() => setTab(c.value)}
                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  tab === c.value
                    ? "bg-[#004D40] text-white"
                    : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
                }`}
              >
                {c.label} ({categoryCounts.get(c.value) ?? 0})
              </button>
            ))}
          </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <FileText className="pointer-events-none absolute left-2 top-2.5 size-4 text-zinc-400" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t.searchPlaceholder}
                className="w-full rounded-lg border border-zinc-200 py-2 pl-8 pr-3 text-sm text-zinc-900"
              />
            </div>
            <label className="inline-flex items-center gap-1 text-xs text-zinc-600">
              <Filter className="size-3.5" />
              {t.status}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-900"
              >
                <option value="all">{t.all}</option>
                <option value="indexed">{t.indexed}</option>
                <option value="pending">{t.indexing}</option>
                <option value="failed">{t.failed}</option>
              </select>
            </label>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-zinc-500">{t.loadingDocs}</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-sm text-zinc-500">{t.noMatches}</div>
        ) : (
          <ul className="divide-y divide-zinc-100">
            {filtered.map((d) => {
              const st = statusOf(d);
              const currentCategory = CATEGORIES.some((c) => c.value === d.category)
                ? (d.category as HrDocumentCategory)
                : "other";
              return (
                <li key={d.id} className="flex flex-col gap-3 px-4 py-3 lg:flex-row lg:items-start">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="truncate text-sm font-semibold text-zinc-900">
                        {d.original_filename}
                      </p>
                      <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[11px] text-zinc-700">
                        {CATEGORIES.find((c) => c.value === d.category)?.label ?? d.category}
                      </span>
                      {st === "indexed" ? (
                        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 ring-1 ring-emerald-100">
                          {t.indexedChunks} · {d.chroma_chunks ?? 0} chunks
                        </span>
                      ) : st === "failed" ? (
                        <span className="rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-semibold text-red-700 ring-1 ring-red-100">
                          {t.indexFailed}
                        </span>
                      ) : (
                        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-700 ring-1 ring-amber-100">
                          {t.indexPending}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-zinc-500">
                      {t.uploadedBy} {d.uploaded_by} · {formatDate(d.uploaded_at)} ·{" "}
                      {formatBytes(d.size_bytes)}
                    </p>
                    {d.chroma_error ? (
                      <p className="mt-1 text-xs text-red-600">{d.chroma_error}</p>
                    ) : null}
                  </div>

                  <div className="flex shrink-0 flex-wrap items-center gap-2">
                    <label className="inline-flex items-center gap-1 text-[11px] text-zinc-600">
                      {t.moveTo}
                      <select
                        value={categoryDraft[d.id] ?? currentCategory}
                        onChange={(e) =>
                          setCategoryDraft((prev) => ({
                            ...prev,
                            [d.id]: e.target.value as HrDocumentCategory,
                          }))
                        }
                        className="rounded border border-zinc-200 bg-white px-2 py-1 text-[11px] text-zinc-900"
                      >
                        {CATEGORIES.map((c) => (
                          <option key={c.value} value={c.value}>
                            {c.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      type="button"
                      onClick={() => void onSaveCategory(d.id)}
                      disabled={
                        savingId === d.id ||
                        deletingId === d.id ||
                        reindexId === d.id ||
                        (categoryDraft[d.id] ?? currentCategory) === currentCategory
                      }
                      className="rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
                    >
                      {savingId === d.id ? t.saving : t.save}
                    </button>
                    <button
                      type="button"
                      onClick={async () => {
                        if (!token) return;
                        setReindexId(d.id);
                        try {
                          await queueHrDocumentIngest(token, d.id);
                          await refresh();
                        } catch (e) {
                          setError(e instanceof Error ? e.message : "Re-index failed");
                        } finally {
                          setReindexId(null);
                        }
                      }}
                      disabled={reindexId === d.id || savingId === d.id || deletingId === d.id}
                      className="rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
                    >
                      {reindexId === d.id ? t.queuing : t.reindex}
                    </button>
                    <button
                      type="button"
                      onClick={() => void onDeleteDocument(d.id)}
                      disabled={deletingId === d.id || savingId === d.id || reindexId === d.id}
                      className="inline-flex items-center gap-1 rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50"
                    >
                      <Trash2 className="size-3.5" />
                      {deletingId === d.id ? t.deleting : t.delete}
                    </button>
                    <Link
                      href="/hr/chat"
                      className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-zinc-800"
                    >
                      {t.askAi}
                    </Link>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
