"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";
import { roleHomePath, useAuth } from "@/contexts/AuthContext";
import { postRegister } from "@/lib/api/auth";
import type { AppRole } from "@/lib/types/auth";

const ROLES: { value: AppRole; label: string }[] = [
  { value: "worker", label: "Worker" },
  { value: "hr_staff", label: "HR Manager" },
  { value: "compliance_officer", label: "Compliance / Supervisor" },
];

export function RegisterForm() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && user) router.replace(roleHomePath(user.role));
  }, [user, loading, router]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState<AppRole>("worker");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [doneMsg, setDoneMsg] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setDoneMsg(null);
    if (!file) {
      setError("Please upload a verification document (ID, appointment letter, or similar).");
      return;
    }
    setPending(true);
    try {
      const fd = new FormData();
      fd.append("email", email);
      fd.append("password", password);
      fd.append("role", role);
      fd.append("verification_doc", file);
      const res = await postRegister(fd);
      setDoneMsg(res.message ?? "Registration submitted.");
      if (res.user?.verification_status === "approved") {
        router.push("/login");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="mx-auto max-w-md space-y-4 rounded-2xl border border-zinc-200 bg-white p-8 shadow-md"
    >
      <div>
        <h1 className="text-xl font-bold text-zinc-900">Register</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Choose your role and upload proof (PDF or image). An administrator can approve pending accounts
          (or enable auto-approve in backend <code className="text-xs">.env</code> for demos).
        </p>
      </div>
      <label className="block text-sm font-medium text-zinc-700">
        Role
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as AppRole)}
          className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm outline-none ring-[#004D40] focus:ring-2"
        >
          {ROLES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm font-medium text-zinc-700">
        Email
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm outline-none ring-[#004D40] focus:ring-2"
        />
      </label>
      <div className="block text-sm font-medium text-zinc-700">
        <span>Password (6–72 characters)</span>
        <div className="relative mt-1">
          <input
            type={showPassword ? "text" : "password"}
            required
            minLength={6}
            maxLength={72}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-zinc-200 py-2 pl-3 pr-11 text-sm outline-none ring-[#004D40] focus:ring-2"
            aria-describedby="register-password-hint"
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800"
            aria-label={showPassword ? "Hide password" : "Show password"}
            aria-pressed={showPassword}
          >
            {showPassword ? <EyeOff className="size-4" aria-hidden /> : <Eye className="size-4" aria-hidden />}
          </button>
        </div>
        <p id="register-password-hint" className="mt-1 text-xs font-normal text-zinc-500">
          Bcrypt accepts up to 72 bytes; longer passwords are blocked here.
        </p>
      </div>
      <label className="block text-sm font-medium text-zinc-700">
        Verification document
        <input
          type="file"
          required
          accept=".pdf,.png,.jpg,.jpeg,.webp"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="mt-1 w-full text-sm text-zinc-600"
        />
      </label>
      {error ? (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
      {doneMsg ? (
        <div className="text-sm text-emerald-800" role="status">
          <p>{doneMsg}</p>
          <p className="mt-2">
            <Link href="/login" className="font-semibold text-[#004D40] hover:underline">
              Go to sign in
            </Link>
          </p>
        </div>
      ) : null}
      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-xl bg-[#004D40] py-2.5 text-sm font-semibold text-white hover:bg-[#00695c] disabled:opacity-60"
      >
        {pending ? "Submitting…" : "Create account"}
      </button>
      <p className="text-center text-sm text-zinc-600">
        Already registered?{" "}
        <Link href="/login" className="font-semibold text-[#004D40] hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
