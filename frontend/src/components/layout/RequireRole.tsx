"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { roleHomePath, useAuth } from "@/contexts/AuthContext";
import type { AppRole } from "@/lib/types/auth";

export function RequireRole({
  allow,
  children,
}: {
  allow: AppRole[];
  children: ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading || !user) return;
    if (!allow.includes(user.role)) router.replace(roleHomePath(user.role));
  }, [user, loading, allow, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-zinc-500">
        Loading…
      </div>
    );
  }

  if (!allow.includes(user.role)) {
    return (
      <div className="mx-auto max-w-lg rounded-xl border border-amber-200 bg-amber-50 p-6 text-center text-sm text-amber-950">
        <p className="font-semibold">This area is restricted to another role.</p>
        <p className="mt-2 text-amber-900/90">You are signed in as {user.role.replace("_", " ")}.</p>
        <Link
          href={roleHomePath(user.role)}
          className="mt-4 inline-block rounded-lg bg-[#004D40] px-4 py-2 text-sm font-semibold text-white"
        >
          Go to your home
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
