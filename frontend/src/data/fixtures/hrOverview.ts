/**
 * Legacy seed data — the HR page uses GET /api/hr/dashboard instead.
 * Kept for tests or Storybook; mirror changes in `backend/services/hr_data.py`.
 */

export type HrOverviewFixture = {
  workforceTotal: number;
  workforceTrendLabel: string;
  activeViolations: number;
  pendingAudits: number;
  pendingAuditsHint: string;
};

export const hrOverviewFixture: HrOverviewFixture = {
  workforceTotal: 500,
  workforceTrendLabel: "+4% vs last month",
  activeViolations: 12,
  pendingAudits: 3,
  pendingAuditsHint: "Next scheduled: Floor 3, Line 4.",
};

export type AuditLogRow = {
  id: string;
  timestampLabel: string;
  category: string;
  categoryVariant: "overtime" | "identity" | "wage" | "ppe";
  summary: string;
  confidencePct: number;
};

/** Table seed data — swap for `/api/hr/audit-log` when ready. */
export const hrAuditLogFixture: AuditLogRow[] = [
  {
    id: "1",
    timestampLabel: "11:42 AM",
    category: "OVERTIME",
    categoryVariant: "overtime",
    summary: "ID #204: Overtime violation flagged by rules engine (sample).",
    confidencePct: 98,
  },
  {
    id: "2",
    timestampLabel: "Yesterday",
    category: "PPE",
    categoryVariant: "ppe",
    summary: "Floor A: PPE checklist item pending verification (sample).",
    confidencePct: 84,
  },
];
