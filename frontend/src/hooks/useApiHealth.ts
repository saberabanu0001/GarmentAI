"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api/rag";

/** Polls GET /health once on mount (optional UX hook). */
export function useApiHealth() {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    getHealth().then(setOk);
  }, []);
  return ok;
}
