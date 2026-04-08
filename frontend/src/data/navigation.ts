import {
  ClipboardCheck,
  LayoutDashboard,
  MessageSquareText,
  ScrollText,
  Settings,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

/** Single source for sidebar — adjust routes here only. */
export const sidebarNav: NavItem[] = [
  { href: "/hr", label: "Dashboard", icon: LayoutDashboard },
  { href: "/worker", label: "AI Chat", icon: MessageSquareText },
  { href: "/library", label: "Document Library", icon: ScrollText },
  { href: "/audit", label: "Factory Audit", icon: ClipboardCheck },
  { href: "/settings", label: "Settings", icon: Settings },
];

export type RoleTab = {
  href: string;
  label: string;
  /** Which sidebar “section” this role maps to for highlight heuristics */
  key: "worker" | "hr" | "auditor";
};

export const roleTabs: RoleTab[] = [
  { href: "/worker", label: "Worker", key: "worker" },
  { href: "/hr", label: "HR Manager", key: "hr" },
  { href: "/auditor", label: "Compliance Auditor", key: "auditor" },
];
