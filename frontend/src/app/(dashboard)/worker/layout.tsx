"use client";

import type { ReactNode } from "react";
import { RequireRole } from "@/components/layout/RequireRole";

export default function WorkerLayout({ children }: { children: ReactNode }) {
  return <RequireRole allow={["worker"]}>{children}</RequireRole>;
}
