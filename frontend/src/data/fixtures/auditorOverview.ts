/** Auditor heatmap + logs — placeholders until sensor/API integration. */

export type ZoneTile = {
  id: string;
  label: string;
  pct: number;
  variant: "ok" | "warn" | "bad";
  subtitle?: string;
};

export const auditorZonesFixture: ZoneTile[] = [
  { id: "a", label: "Zone A: Cutting", pct: 98, variant: "ok" },
  {
    id: "b",
    label: "Zone B: Chemical Storage",
    pct: 64,
    variant: "bad",
    subtitle: "Ventilation sensors offline (sample)",
  },
];

export type PrecisionLogRow = {
  id: string;
  ts: string;
  zone: string;
  category: string;
  deltaPct: number;
  status: "VERIFIED" | "RE-AUDIT";
};

export const precisionLogFixture: PrecisionLogRow[] = [
  {
    id: "1",
    ts: "2023-10-24 14:22",
    zone: "Zone A (Cutting)",
    category: "Machine Guarding",
    deltaPct: 2.4,
    status: "VERIFIED",
  },
  {
    id: "2",
    ts: "2023-10-24 13:05",
    zone: "Zone B (Chemical)",
    category: "PPE Compliance",
    deltaPct: -15.2,
    status: "RE-AUDIT",
  },
];
