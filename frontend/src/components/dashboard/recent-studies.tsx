"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Eye, Loader2 } from "lucide-react";

export function RecentStudies() {
  const { data, isLoading } = useQuery({
    queryKey: ["studies", "recent"],
    queryFn: () => apiClient.get("/studies?limit=5").then((r) => r.data),
  });

  return (
    <div className="card">
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800">
        <h3 className="font-semibold text-slate-900 dark:text-white">Recent Studies</h3>
        <Link href="/studies" className="text-sm text-brand-600 hover:text-brand-700 font-medium">
          View all
        </Link>
      </div>
      <div className="divide-y divide-slate-100 dark:divide-slate-800">
        {isLoading && (
          <div className="flex justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
          </div>
        )}
        {!isLoading && (!data || data.length === 0) && (
          <div className="py-8 text-center text-sm text-slate-400">No studies yet. Upload your first DICOM study.</div>
        )}
        {(data ?? MOCK_STUDIES).map((study: any) => (
          <div key={study.id} className="flex items-center gap-4 px-5 py-3.5">
            <div className="h-9 w-9 rounded-lg bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400 font-bold text-xs shrink-0">
              {study.modality}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                {study.study_description || "Unnamed Study"}
              </p>
              <p className="text-xs text-slate-400">{study.study_date} · {study.num_instances} instances</p>
            </div>
            <span className={`badge badge-${STATUS_COLOR[study.status] ?? "blue"}`}>
              {study.status}
            </span>
            <Link href={`/viewer?study=${study.id}`} className="p-1.5 rounded-lg text-slate-400 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition">
              <Eye className="h-4 w-4" />
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}

const STATUS_COLOR: Record<string, string> = {
  uploaded: "blue",
  processing: "amber",
  analyzed: "green",
  failed: "red",
};

const MOCK_STUDIES = [
  { id: "1", modality: "CT",  study_description: "Chest CT — Lung Nodule", study_date: "2026-05-20", num_instances: 412, status: "analyzed" },
  { id: "2", modality: "MR",  study_description: "Brain MRI — T1/T2/FLAIR", study_date: "2026-05-21", num_instances: 180, status: "analyzed" },
  { id: "3", modality: "CR",  study_description: "Chest X-Ray PA/Lateral",  study_date: "2026-05-22", num_instances: 2,   status: "uploaded" },
  { id: "4", modality: "US",  study_description: "Abdominal Ultrasound",     study_date: "2026-05-23", num_instances: 48,  status: "processing" },
  { id: "5", modality: "MR",  study_description: "Spine MRI — L-Spine",      study_date: "2026-05-24", num_instances: 96,  status: "analyzed" },
];
