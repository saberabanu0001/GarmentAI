"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { sidebarNav } from "@/data/navigation";

const brandGreen = "text-[#004D40]";

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 flex-col border-r border-zinc-200 bg-zinc-50/90 backdrop-blur">
      <div className="border-b border-zinc-200 px-5 py-6">
        <div className={`text-lg font-bold tracking-tight ${brandGreen}`}>
          GarmentAI
        </div>
        <div className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Industrial precision
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {sidebarNav.map((item) => {
          const active =
            pathname === item.href || pathname?.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? `border-l-4 border-[#004D40] bg-white text-[#004D40] shadow-sm`
                  : "border-l-4 border-transparent text-zinc-600 hover:bg-white/70 hover:text-zinc-900"
              }`}
            >
              <Icon className="size-4 shrink-0 opacity-90" strokeWidth={1.75} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
