import {
  ClipboardCheck,
  LayoutDashboard,
  MessageSquareText,
  ScrollText,
  Settings,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { AppRole } from "@/lib/types/auth";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

/** Sidebar links depend on signed-in role (no cross-role URLs in the menu). */
export function sidebarNavForRole(role: AppRole): NavItem[] {
  if (role === "worker") {
    return [
      { href: "/worker", label: "AI Chat", icon: MessageSquareText },
      { href: "/library", label: "Document Library", icon: ScrollText },
      { href: "/settings", label: "Settings", icon: Settings },
    ];
  }
  if (role === "hr_staff") {
    return [
      { href: "/hr", label: "Dashboard", icon: LayoutDashboard },
      { href: "/hr/chat", label: "AI Chat (HR)", icon: MessageSquareText },
      { href: "/library", label: "Document Library", icon: ScrollText },
      { href: "/audit", label: "Factory Audit", icon: ClipboardCheck },
      { href: "/settings", label: "Settings", icon: Settings },
    ];
  }
  return [
    { href: "/auditor", label: "Dashboard", icon: LayoutDashboard },
    { href: "/auditor/chat", label: "AI Chat (Compliance)", icon: MessageSquareText },
    { href: "/library", label: "Document Library", icon: ScrollText },
    { href: "/audit", label: "Factory Audit", icon: ClipboardCheck },
    { href: "/settings", label: "Settings", icon: Settings },
  ];
}

export function roleTabLabel(role: AppRole): string {
  if (role === "worker") return "Worker";
  if (role === "hr_staff") return "HR Manager";
  return "Compliance";
}
