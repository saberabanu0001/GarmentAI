"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bell, LogOut, Search, UserCircle2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { roleTabLabel } from "@/data/navigation";

export function TopBar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  return (
    <header className="flex h-14 items-center gap-4 border-b border-zinc-200 bg-white/95 px-4 backdrop-blur">
      <div className="relative hidden min-w-[200px] flex-1 md:block">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-zinc-400" />
        <input
          type="search"
          placeholder="Search…"
          className="h-10 w-full max-w-xl rounded-full border border-zinc-200 bg-zinc-50 pl-10 pr-4 text-sm outline-none ring-[#004D40] placeholder:text-zinc-400 focus:border-[#004D40]/40 focus:ring-2"
          readOnly
          aria-readonly
        />
      </div>
      <div
        className="flex flex-1 items-center justify-center gap-4 text-sm font-medium text-zinc-700"
        aria-label="Your role"
      >
        {user ? (
          <>
            <span className="rounded-full bg-[#004D40]/10 px-3 py-1 text-[#004D40]">
              {roleTabLabel(user.role)}
            </span>
            <span className="hidden text-xs text-zinc-500 sm:inline">{user.email}</span>
          </>
        ) : (
          <span className="text-zinc-500">Not signed in</span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="rounded-full p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800"
          aria-label="Notifications (placeholder)"
        >
          <Bell className="size-5" />
        </button>
        {user ? (
          <button
            type="button"
            onClick={() => {
              logout();
              router.replace("/login");
            }}
            className="inline-flex items-center gap-1 rounded-full p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800"
            aria-label="Log out"
          >
            <LogOut className="size-5" />
          </button>
        ) : (
          <Link
            href="/login"
            className="rounded-full p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800"
            aria-label="Sign in"
          >
            <UserCircle2 className="size-6" />
          </Link>
        )}
      </div>
    </header>
  );
}
