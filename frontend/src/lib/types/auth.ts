/** Matches backend registration / JWT role claim. */
export type AppRole = "worker" | "hr_staff" | "compliance_officer";

export type AuthUser = {
  id: string;
  email: string;
  role: AppRole;
  verification_status: "pending" | "approved" | "rejected";
};
