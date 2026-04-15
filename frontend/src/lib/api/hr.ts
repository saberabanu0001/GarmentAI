import { apiBaseUrl, apiTimeoutMs } from "@/lib/config";
import type { HrDashboardResponse } from "@/lib/types/hr";

export async function getHrDashboard(): Promise<HrDashboardResponse> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const res = await fetch(`${apiBaseUrl}/api/hr/dashboard`, {
      cache: "no-store",
      signal: ctrl.signal,
    });
    const json: unknown = await res.json();
    if (!res.ok) {
      const err = json as { error?: string };
      throw new Error(err.error || `HR dashboard failed (${res.status})`);
    }
    return json as HrDashboardResponse;
  } finally {
    clearTimeout(t);
  }
}

export async function putHrDashboard(
  body: HrDashboardResponse,
  accessToken: string,
): Promise<HrDashboardResponse> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), apiTimeoutMs);
  try {
    const res = await fetch(`${apiBaseUrl}/api/hr/dashboard`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(body),
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
      throw new Error(err.error || nested || `Save failed (${res.status})`);
    }
    return json as HrDashboardResponse;
  } finally {
    clearTimeout(t);
  }
}
