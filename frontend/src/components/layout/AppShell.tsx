import type { ReactNode } from "react";
import { SidebarNav } from "@/components/layout/SidebarNav";
import { TopBar } from "@/components/layout/TopBar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div
      className="flex min-h-screen bg-zinc-200 text-zinc-900"
      style={{
        backgroundImage:
          "radial-gradient(circle, rgb(212 212 216) 1px, transparent 1px)",
        backgroundSize: "14px 14px",
      }}
    >
      <SidebarNav />
      <div className="flex min-h-screen min-w-0 flex-1 flex-col bg-transparent">
        <TopBar />
        <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
