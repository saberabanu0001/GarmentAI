import { apiBaseUrl } from "@/lib/config";
import type { AuthUser } from "@/lib/types/auth";
import { getStoredToken } from "@/lib/auth/storage";

export async function postLogin(email: string, password: string): Promise<{ access_token: string; user: AuthUser }> {
  const res = await fetch(`${apiBaseUrl}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
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
    throw new Error(err.error || nested || `Login failed (${res.status})`);
  }
  const o = json as { access_token?: string; user?: AuthUser };
  if (!o.access_token || !o.user) throw new Error("Invalid login response");
  return { access_token: o.access_token, user: o.user };
}

export async function postRegister(form: FormData): Promise<{ ok: boolean; message?: string; user?: AuthUser }> {
  const res = await fetch(`${apiBaseUrl}/api/auth/register`, {
    method: "POST",
    body: form,
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
    throw new Error(err.error || nested || `Registration failed (${res.status})`);
  }
  return json as { ok: boolean; message?: string; user?: AuthUser };
}

export async function getMe(): Promise<AuthUser> {
  const token = getStoredToken();
  if (!token) throw new Error("Not signed in");
  const res = await fetch(`${apiBaseUrl}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const json: unknown = await res.json();
  if (!res.ok) {
    const err = json as { error?: string };
    throw new Error(err.error || `Session check failed (${res.status})`);
  }
  return json as AuthUser;
}
