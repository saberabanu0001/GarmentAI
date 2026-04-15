"use client";

import type { ReactNode } from "react";
import { RequireRole } from "@/components/layout/RequireRole";

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <RequireRole allow={["worker", "hr_staff", "compliance_officer"]}>{children}</RequireRole>
  );
}
