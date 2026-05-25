"use client";

import clsx from "clsx";

interface Props {
  title: string;
  value: string;
  delta: string;
  icon: React.ReactNode;
  color: "blue" | "purple" | "green" | "amber";
}

const COLOR_MAP = {
  blue:   "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400",
  purple: "bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400",
  green:  "bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400",
  amber:  "bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400",
};

export function StatsCard({ title, value, delta, icon, color }: Props) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">{title}</p>
          <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">{value}</p>
        </div>
        <div className={clsx("p-2.5 rounded-xl", COLOR_MAP[color])}>{icon}</div>
      </div>
      <p className="text-xs text-slate-400">{delta}</p>
    </div>
  );
}
