import { apiBaseUrl, apiTimeoutMs } from "@/lib/config";
import type { RagErrorBody, RagResponse } from "@/lib/types/rag";

export type RagRequest = {
  question: string;
  role: string;
  factory_id?: string;
  top_k?: number;
  backend?: "ollama" | "groq" | "gemini";
};

export async function postRag(body: RagRequest): Promise<RagResponse> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const res = await fetch(`${apiBaseUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    const json: unknown = await res.json();
    if (!res.ok) {
      const err = json as RagErrorBody & { detail?: unknown };
      const nested =
        typeof err.detail === "object" &&
        err.detail !== null &&
        "error" in err.detail
          ? String((err.detail as { error: string }).error)
          : null;
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
