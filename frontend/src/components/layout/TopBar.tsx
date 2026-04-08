"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Search, UserCircle2 } from "lucide-react";
import { roleTabs } from "@/data/navigation";

export function TopBar() {
  const pathname = usePathname();

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
      <nav
        className="flex flex-1 items-center justify-center gap-6 text-sm font-medium"
        aria-label="Role switcher"
      >
        {roleTabs.map((tab) => {
          const active = pathname === tab.href;
          return (
            <Link
              key={tab.key}
              href={tab.href}
              className={`relative pb-1 transition-colors ${
                active
                  ? "text-[#004D40]"
                  : "text-zinc-500 hover:text-zinc-800"
              }`}
            >
              {tab.label}
              {active ? (
                <span className="absolute inset-x-0 -bottom-0.5 h-0.5 rounded-full bg-[#004D40]" />
              ) : null}
            </Link>
          );
        })}
      </nav>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="rounded-full p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800"
          aria-label="Notifications (placeholder)"
        >
          <Bell className="size-5" />
        </button>
        <button
          type="button"
          className="rounded-full p-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800"
          aria-label="Profile (placeholder)"
        >
          <UserCircle2 className="size-6" />
        </button>
      </div>
    </header>
  );
}
