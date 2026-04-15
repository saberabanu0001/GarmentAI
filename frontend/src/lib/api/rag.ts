import { getStoredToken } from "@/lib/auth/storage";
import { apiBaseUrl, apiTimeoutMs } from "@/lib/config";
import type { RagErrorBody, RagResponse } from "@/lib/types/rag";

export type RagRequest = {
  question: string;
  role: "worker" | "hr_staff" | "compliance_officer";
  factory_id?: string;
  top_k?: number;
  backend?: "groq";
  response_language?: "auto" | "en" | "bn";
};

export async function postRag(body: RagRequest): Promise<RagResponse> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const token = getStoredToken();
    const res = await fetch(`${apiBaseUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    const json: unknown = await res.json();
    if (!res.ok) {
      const err = json as RagErrorBody & {
        detail?: unknown;
        message?: string;
        retry_after_seconds?: number;
      };
      const nested =
        typeof err.detail === "object" &&
        err.detail !== null &&
        "error" in err.detail
          ? String((err.detail as { error: string }).error)
          : null;
      const nestedMessage =
        typeof err.detail === "object" &&
        err.detail !== null &&
        "message" in err.detail
          ? String((err.detail as { message: string }).message)
          : null;
      const nestedRetry =
        typeof err.detail === "object" &&
        err.detail !== null &&
        "retry_after_seconds" in err.detail
          ? Number((err.detail as { retry_after_seconds: number }).retry_after_seconds)
          : null;
      if (res.status === 429 || err.error === "quota_exceeded" || nested === "quota_exceeded") {
        const retrySec =
          nestedRetry !== null && Number.isFinite(nestedRetry) ? Math.max(0, nestedRetry) : null;
        const retryHint =
          retrySec !== null ? ` Retry in about ${Math.ceil(retrySec / 60)} minute(s).` : "";
        throw new Error(
          (nestedMessage || err.message || "Daily AI quota reached for this tenant.") + retryHint,
        );
      }
      throw new Error(err.error || nested || `RAG failed (${res.status})`);
    }
    return json as RagResponse;
  } finally {
    clearTimeout(t);
  }
}

export async function getHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${apiBaseUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    return res.ok;
  } catch {
    return false;
  }
}
