"use client";

import { Bell, Search, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

interface Props {
  title: string;
  dark?: boolean;
}

export function Header({ title, dark }: Props) {
  const { theme, setTheme } = useTheme();

  return (
    <header
      className={`h-14 flex items-center justify-between px-6 border-b ${
        dark
          ? "bg-slate-900 border-slate-800"
          : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
      }`}
    >
      <h1 className={`font-semibold text-lg ${dark ? "text-white" : "text-slate-900 dark:text-white"}`}>
        {title}
      </h1>
      <div className="flex items-center gap-2">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search studies..."
            className="pl-9 pr-4 py-1.5 text-sm bg-slate-100 dark:bg-slate-800 rounded-lg border-0 focus:ring-2 focus:ring-brand-500 outline-none w-52 text-slate-700 dark:text-slate-300 placeholder-slate-400"
          />
        </div>

        {/* Theme toggle */}
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className={`p-2 rounded-lg transition-colors ${
            dark
              ? "text-slate-400 hover:text-white hover:bg-slate-800"
              : "text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"
          }`}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        {/* Notifications */}
        <button
          className={`relative p-2 rounded-lg transition-colors ${
            dark
              ? "text-slate-400 hover:text-white hover:bg-slate-800"
              : "text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"
          }`}
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 bg-red-500 rounded-full" />
        </button>
      </div>
    </header>
  );
}
