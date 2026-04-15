"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";
import { roleHomePath, useAuth } from "@/contexts/AuthContext";

export function LoginForm() {
  const router = useRouter();
  const { login, user, loading } = useAuth();

  useEffect(() => {
    if (!loading && user) router.replace(roleHomePath(user.role));
  }, [user, loading, router]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      const loggedIn = await login(email, password);
      router.replace(roleHomePath(loggedIn.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-md space-y-4 rounded-2xl border border-zinc-200 bg-white p-8 shadow-md">
      <div>
        <h1 className="text-xl font-bold text-zinc-900">Sign in</h1>
        <p className="mt-1 text-sm text-zinc-500">Use the account you registered for your role.</p>
      </div>
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
        <span>Password</span>
        <div className="relative mt-1">
          <input
            type={showPassword ? "text" : "password"}
            required
            maxLength={72}
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-zinc-200 py-2 pl-3 pr-11 text-sm outline-none ring-[#004D40] focus:ring-2"
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
      </div>
      {error ? (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-xl bg-[#004D40] py-2.5 text-sm font-semibold text-white hover:bg-[#00695c] disabled:opacity-60"
      >
        {pending ? "Signing in…" : "Sign in"}
      </button>
      <p className="text-center text-sm text-zinc-600">
        No account?{" "}
        <Link href="/register" className="font-semibold text-[#004D40] hover:underline">
          Register
        </Link>
      </p>
    </form>
  );
}
