"use client";

import type { ReactNode } from "react";
import { RequireRole } from "@/components/layout/RequireRole";

export default function AuditLayout({ children }: { children: ReactNode }) {
  return <RequireRole allow={["hr_staff", "compliance_officer"]}>{children}</RequireRole>;
}
