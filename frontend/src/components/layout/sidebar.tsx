"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Brain,
  LayoutDashboard,
  Upload,
  MonitorPlay,
  FileText,
  Settings,
  Users,
  Activity,
  LogOut,
  ChevronLeft,
} from "lucide-react";
import clsx from "clsx";
import { useAuthStore } from "@/store/auth-store";

interface Props {
  compact?: boolean;
}

const NAV_ITEMS = [
  { href: "/dashboard",  icon: LayoutDashboard,  label: "Dashboard" },
  { href: "/upload",     icon: Upload,            label: "Upload" },
  { href: "/viewer",     icon: MonitorPlay,       label: "Viewer" },
  { href: "/studies",    icon: Activity,          label: "Studies" },
  { href: "/reports",    icon: FileText,          label: "Reports" },
  { href: "/users",      icon: Users,             label: "Users",    adminOnly: true },
  { href: "/settings",   icon: Settings,          label: "Settings" },
];

export function Sidebar({ compact }: Props) {
  const pathname = usePathname();
  const { logout, user } = useAuthStore();

  return (
    <aside
      className={clsx(
        "flex flex-col border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-all duration-200",
        compact ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className={clsx("flex items-center gap-3 px-4 py-5 border-b border-slate-200 dark:border-slate-800", compact && "justify-center px-2")}>
        <Brain className="h-8 w-8 text-brand-600 shrink-0" />
        {!compact && (
          <div>
            <span className="font-bold text-slate-900 dark:text-white text-lg leading-tight">AutoRadixAI</span>
            <p className="text-xs text-slate-400 leading-tight">Medical AI Platform</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              title={compact ? item.label : undefined}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm font-medium",
                isActive
                  ? "bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white",
                compact && "justify-center px-2"
              )}
            >
              <item.icon className="h-4.5 w-4.5 shrink-0" />
              {!compact && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User / Logout */}
      {!compact && (
        <div className="p-3 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="h-8 w-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
              {user?.username?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                {user?.username ?? "User"}
              </p>
              <p className="text-xs text-slate-400 truncate">{user?.role ?? "viewer"}</p>
            </div>
            <button
              onClick={logout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
