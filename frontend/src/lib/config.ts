/**
 * Runtime config — no hardcoded URLs in fetch helpers.
 */

function requiredPublicUrl(raw: string | undefined, fallback: string): string {
  const v = (raw ?? fallback).trim().replace(/\/$/, "");
  return v;
}

export const apiBaseUrl = requiredPublicUrl(
  process.env.NEXT_PUBLIC_API_URL,
  "http://127.0.0.1:5050",
);

export const apiTimeoutMs = Number(
  process.env.NEXT_PUBLIC_API_TIMEOUT_MS ?? "180000",
);
