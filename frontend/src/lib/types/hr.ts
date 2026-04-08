export type HrCategoryVariant = "overtime" | "identity" | "wage" | "ppe";

export type HrOverview = {
  workforceTotal: number;
  workforceTrendLabel: string;
  activeViolations: number;
  pendingAudits: number;
  pendingAuditsHint: string;
};

export type HrAuditLogRow = {
  id: string;
  timestampLabel: string;
  category: string;
  categoryVariant: HrCategoryVariant;
  summary: string;
  confidencePct: number;
};

export type HrRegulatoryUpdate = {
  title: string;
  body: string;
  ctaLabel: string;
  briefQuestion: string;
};

export type HrAssistantCopy = {
  welcome: string;
  suggestedPrompt: string;
};

export type HrDashboardResponse = {
  overview: HrOverview;
  violationsNote: string;
  auditLog: HrAuditLogRow[];
  regulatoryUpdate: HrRegulatoryUpdate;
  assistant: HrAssistantCopy;
};
