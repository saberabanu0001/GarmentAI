"use client";

import type { ReactNode } from "react";
import { RequireRole } from "@/components/layout/RequireRole";

export default function HrLayout({ children }: { children: ReactNode }) {
  return <RequireRole allow={["hr_staff"]}>{children}</RequireRole>;
}
