"use client";

import { Loader2, Brain, CheckCircle2, XCircle, Clock } from "lucide-react";
import clsx from "clsx";

const MOCK_QUEUE = [
  { id: "p1", model: "chest_xray_pneumonia",        status: "completed", confidence: 0.94, elapsed: "2.1s" },
  { id: "p2", model: "ct_lung_nodule_detection",    status: "running",   confidence: null, elapsed: "—" },
  { id: "p3", model: "brain_tumor_segmentation",    status: "pending",   confidence: null, elapsed: "—" },
  { id: "p4", model: "ct_liver_segmentation",       status: "completed", confidence: 0.87, elapsed: "3.4s" },
  { id: "p5", model: "generic_classification",      status: "failed",    confidence: null, elapsed: "—" },
];

export function InferenceQueue() {
  return (
    <div className="card h-full">
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800">
        <h3 className="font-semibold text-slate-900 dark:text-white">Inference Queue</h3>
        <span className="text-xs text-slate-400">Live</span>
      </div>
      <div className="divide-y divide-slate-100 dark:divide-slate-800">
        {MOCK_QUEUE.map((job) => (
          <div key={job.id} className="flex items-start gap-3 px-5 py-3.5">
            <StatusIcon status={job.status} />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">
                {job.model.replace(/_/g, " ")}
              </p>
              {job.confidence != null && (
                <div className="flex items-center gap-1.5 mt-1">
                  <div className="flex-1 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full">
                    <div
                      className="h-1.5 bg-brand-500 rounded-full"
                      style={{ width: `${job.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400">{(job.confidence * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>
            <span className="text-xs text-slate-400 shrink-0">{job.elapsed}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "running")
    return <Loader2 className="h-4 w-4 text-brand-500 animate-spin mt-0.5 shrink-0" />;
  if (status === "completed")
    return <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />;
  if (status === "failed")
    return <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />;
  return <Clock className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />;
}
