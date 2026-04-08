import { apiBaseUrl, apiTimeoutMs } from "@/lib/config";

export async function postVoiceTranscribe(
  audioBlob: Blob,
  language: "auto" | "en" | "bn",
): Promise<string> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const form = new FormData();
    form.append("file", audioBlob, "worker-voice.webm");
    form.append("language", language);

    const res = await fetch(`${apiBaseUrl}/api/voice/transcribe`, {
      method: "POST",
      body: form,
      signal: ctrl.signal,
    });
    const json: unknown = await res.json();
    if (!res.ok) {
      const err = json as { error?: string; detail?: unknown };
      const nested =
        typeof err.detail === "object" &&
        err.detail !== null &&
        "error" in err.detail
          ? String((err.detail as { error: string }).error)
          : null;
      throw new Error(err.error || nested || `Transcription failed (${res.status})`);
    }
    return String((json as { text?: string }).text ?? "").trim();
  } finally {
    clearTimeout(t);
  }
}
