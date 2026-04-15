import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center bg-zinc-100 px-4 py-12"
      style={{
        backgroundImage:
          "radial-gradient(circle, rgb(212 212 216) 1px, transparent 1px)",
        backgroundSize: "14px 14px",
      }}
    >
      <div className="mb-6 text-center">
        <div className="text-2xl font-bold text-[#004D40]">GarmentAI</div>
        <div className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Role-based access
        </div>
      </div>
      {children}
    </div>
  );
}
