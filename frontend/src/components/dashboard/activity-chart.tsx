"use client";

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const DATA = [
  { date: "May 19", studies: 18, inferences: 42 },
  { date: "May 20", studies: 24, inferences: 65 },
  { date: "May 21", studies: 31, inferences: 88 },
  { date: "May 22", studies: 19, inferences: 57 },
  { date: "May 23", studies: 27, inferences: 73 },
  { date: "May 24", studies: 35, inferences: 94 },
  { date: "May 25", studies: 42, inferences: 112 },
];

export function ActivityChart() {
  return (
    <div className="card p-5">
      <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Activity (7 days)</h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={DATA} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="studiesGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="infGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:stroke-slate-700" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "0.5rem",
              color: "#f8fafc",
              fontSize: "12px",
            }}
          />
          <Area type="monotone" dataKey="studies" name="Studies" stroke="#3b82f6" fill="url(#studiesGrad)" strokeWidth={2} dot={false} />
          <Area type="monotone" dataKey="inferences" name="Inferences" stroke="#8b5cf6" fill="url(#infGrad)" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
