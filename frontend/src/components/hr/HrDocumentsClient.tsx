"use client";

import { useCallback, useEffect, useState } from "react";
import { Upload } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  getHrDocuments,
  queueHrDocumentIngest,
  uploadHrDocument,
} from "@/lib/api/hrDocuments";
import type { HrDocumentCategory, HrDocumentRow } from "@/lib/types/hrDocuments";

const CATEGORIES: { value: HrDocumentCategory; label: string }[] = [
  { value: "employee", label: "Employee" },
  { value: "recruitment", label: "Recruitment" },
  { value: "training", label: "Training" },
  { value: "compliance", label: "Compliance & legal" },
  { value: "performance", label: "Performance" },
  { value: "other", label: "Other" },
];

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export function HrDocumentsClient() {
  const { token, loading: authLoading } = useAuth();
  const [docs, setDocs] = useState<HrDocumentRow[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<HrDocumentCategory>("compliance");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [reindexId, setReindexId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!token) {
      setDocs([]);
      setLoading(false);
      return;
    }
    setLoadError(null);
    setLoading(true);
    try {
      const list = await getHrDocuments(token);
      setDocs(list);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Could not load documents");
      setDocs([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (authLoading) return;
    void refresh();
  }, [authLoading, refresh]);

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !token) return;
    setUploadError(null);
    setUploading(true);
    try {
      await uploadHrDocument(token, file, category);
      await refresh();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="mx-auto max-w-4xl animate-pulse rounded-xl bg-zinc-200 p-12" />
    );
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-4xl rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-950">
        <p className="font-semibold">Sign in required</p>
        <p className="mt-2 text-amber-900/90">
          HR document upload and listing require an authenticated HR session.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">HR document library</h1>
        <p className="mt-1 text-sm text-zinc-600">
          Upload PDFs (or plain text). Each file is saved under{" "}
          <code className="rounded bg-zinc-100 px-1 text-xs">data/hr_uploads/</code>, then
          <strong className="font-semibold"> text is extracted, chunked, embedded with E5</strong>
          , and stored in the Chroma collection{" "}
          <code className="rounded bg-zinc-100 px-1 text-xs">hr_uploads</code> so{" "}
          <strong className="font-semibold">HR chat</strong> can retrieve it (after indexing
          finishes — refresh the list to see status).
        </p>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-md">
        <h2 className="text-sm font-semibold text-zinc-900">Upload</h2>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="block flex-1 text-xs font-medium text-zinc-600">
            Category
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as HrDocumentCategory)}
              className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
          <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl bg-[#004D40] px-4 py-2.5 text-sm font-semibold text-white shadow hover:bg-[#00695c] disabled:opacity-50">
            <Upload className="size-4" />
            {uploading ? "Uploading…" : "Choose file"}
            <input
              type="file"
              className="hidden"
              disabled={uploading}
              onChange={onFile}
            />
          </label>
        </div>
        {uploadError ? (
          <p className="mt-2 text-xs text-red-700" role="alert">
            {uploadError}
          </p>
        ) : null}
        <p className="mt-2 text-xs text-zinc-500">Max size 20 MB per file.</p>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white shadow-md">
        <div className="border-b border-zinc-100 px-5 py-3">
          <h2 className="text-sm font-semibold text-zinc-900">Uploaded files</h2>
        </div>
        {loading ? (
          <div className="p-8 text-center text-sm text-zinc-500">Loading…</div>
        ) : loadError ? (
          <div className="p-6 text-sm text-red-700">{loadError}</div>
        ) : docs.length === 0 ? (
          <div className="p-8 text-center text-sm text-zinc-500">
            No documents yet. Upload a PDF or spreadsheet above.
          </div>
        ) : (
          <ul className="divide-y divide-zinc-100">
            {docs.map((d) => (
              <li
                key={d.id}
                className="flex flex-col gap-2 px-5 py-3 text-sm sm:flex-row sm:items-start sm:justify-between"
              >
                <div>
                  <span className="font-medium text-zinc-900">
                    {d.original_filename}
                  </span>
                  <span className="ml-2 rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
                    {d.category}
                  </span>
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {formatBytes(d.size_bytes)} · {d.uploaded_at.slice(0, 19)} ·{" "}
                    {d.uploaded_by}
                  </p>
                  <p className="mt-1 text-xs">
                    {d.chroma_indexed ? (
                      <span className="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-800 ring-1 ring-emerald-100">
                        Indexed · {d.chroma_chunks ?? 0} chunks
                      </span>
                    ) : d.chroma_error ? (
                      <span className="text-red-700" title={d.chroma_error}>
                        Index failed — hover for detail
                      </span>
                    ) : (
                      <span className="text-amber-700">Indexing pending…</span>
                    )}
                  </p>
                  {d.chroma_error ? (
                    <p className="mt-1 max-w-xl text-xs text-red-600">{d.chroma_error}</p>
                  ) : null}
                </div>
                <button
                  type="button"
                  disabled={!token || reindexId === d.id}
                  onClick={async () => {
                    if (!token) return;
                    setReindexId(d.id);
                    try {
                      await queueHrDocumentIngest(token, d.id);
                      await refresh();
                    } catch (e) {
                      setLoadError(e instanceof Error ? e.message : "Re-index failed");
                    } finally {
                      setReindexId(null);
                    }
                  }}
                  className="shrink-0 rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
                >
                  {reindexId === d.id ? "Queuing…" : "Re-index"}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
