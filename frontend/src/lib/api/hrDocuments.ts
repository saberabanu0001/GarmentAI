import { apiBaseUrl, apiTimeoutMs } from "@/lib/config";
import type {
  HrDocumentCategory,
  HrDocumentLanguage,
  HrDocumentRow,
} from "@/lib/types/hrDocuments";

export async function getHrDocuments(
  accessToken: string,
): Promise<HrDocumentRow[]> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const res = await fetch(`${apiBaseUrl}/api/hr/documents`, {
      cache: "no-store",
      headers: { Authorization: `Bearer ${accessToken}` },
      signal: ctrl.signal,
    });
    const json: unknown = await res.json();
    if (!res.ok) {
      const err = json as { error?: string };
      throw new Error(err.error || `List failed (${res.status})`);
    }
    const docs = (json as { documents?: HrDocumentRow[] }).documents;
    return Array.isArray(docs) ? docs : [];
  } finally {
    clearTimeout(t);
  }
}

export async function uploadHrDocument(
  accessToken: string,
  file: File,
  category: HrDocumentCategory,
  language: HrDocumentLanguage = "en",
): Promise<HrDocumentRow> {
  const form = new FormData();
  form.set("category", category);
  form.set("language", language);
  form.set("file", file);
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const res = await fetch(`${apiBaseUrl}/api/hr/documents`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body: form,
      signal: ctrl.signal,
    });
    const json: unknown = await res.json();
    if (!res.ok) {
      const err = json as { error?: string };
      throw new Error(err.error || `Upload failed (${res.status})`);
    }
    const doc = (json as { document?: HrDocumentRow }).document;
    if (!doc) throw new Error("Invalid upload response");
    return doc;
  } finally {
    clearTimeout(t);
  }
}

export async function queueHrDocumentIngest(
  accessToken: string,
  docId: string,
): Promise<void> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const res = await fetch(
      `${apiBaseUrl}/api/hr/documents/${encodeURIComponent(docId)}/ingest`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
        signal: ctrl.signal,
      },
    );
    const json: unknown = await res.json();
    if (!res.ok) {
      const err = json as { error?: string };
      throw new Error(err.error || `Re-index failed (${res.status})`);
    }
  } finally {
    clearTimeout(t);
  }
}

export async function updateHrDocumentCategory(
  accessToken: string,
  docId: string,
  category: HrDocumentCategory,
): Promise<HrDocumentRow> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const res = await fetch(`${apiBaseUrl}/api/hr/documents/${encodeURIComponent(docId)}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ category }),
      signal: ctrl.signal,
    });
    const json: unknown = await res.json();
    if (!res.ok) {
      const err = json as { error?: string };
      throw new Error(err.error || `Update failed (${res.status})`);
    }
    const doc = (json as { document?: HrDocumentRow }).document;
    if (!doc) throw new Error("Invalid update response");
    return doc;
  } finally {
    clearTimeout(t);
  }
}

export async function deleteHrDocument(accessToken: string, docId: string): Promise<void> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const res = await fetch(`${apiBaseUrl}/api/hr/documents/${encodeURIComponent(docId)}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${accessToken}` },
      signal: ctrl.signal,
    });
    const json: unknown = await res.json();
    if (!res.ok) {
      const err = json as { error?: string };
      throw new Error(err.error || `Delete failed (${res.status})`);
    }
  } finally {
    clearTimeout(t);
  }
}
