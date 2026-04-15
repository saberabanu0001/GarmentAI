"use client";

import type { ReactNode } from "react";
import { RequireRole } from "@/components/layout/RequireRole";

export default function AuditorLayout({ children }: { children: ReactNode }) {
  return <RequireRole allow={["compliance_officer"]}>{children}</RequireRole>;
}
