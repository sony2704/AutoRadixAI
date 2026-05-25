"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { StatsCard } from "@/components/dashboard/stats-card";
import { RecentStudies } from "@/components/dashboard/recent-studies";
import { InferenceQueue } from "@/components/dashboard/inference-queue";
import { ActivityChart } from "@/components/dashboard/activity-chart";
import { useAuthStore } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Brain, FileImage, FlaskConical, FileText, Activity } from "lucide-react";

export default function DashboardPage() {
  const { token } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!token) router.replace("/login");
  }, [token, router]);

  if (!token) return null;

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="Dashboard" />
        <main className="flex-1 overflow-y-auto p-6">
          {/* Stats Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatsCard
              title="Total Studies"
              value="248"
              delta="+12 this week"
              icon={<FileImage className="h-5 w-5" />}
              color="blue"
            />
            <StatsCard
              title="AI Inferences"
              value="1,842"
              delta="+94 today"
              icon={<Brain className="h-5 w-5" />}
              color="purple"
            />
            <StatsCard
              title="Reports Generated"
              value="631"
              delta="+8 today"
              icon={<FileText className="h-5 w-5" />}
              color="green"
            />
            <StatsCard
              title="Accuracy (avg)"
              value="94.2%"
              delta="↑ 0.3% vs last month"
              icon={<Activity className="h-5 w-5" />}
              color="amber"
            />
          </div>

          {/* Main Content */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <ActivityChart />
              <RecentStudies />
            </div>
            <div>
              <InferenceQueue />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
