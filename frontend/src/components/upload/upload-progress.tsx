"use client";

import { Loader2 } from "lucide-react";

interface Props {
  progress: number;
}

export function UploadProgress({ progress }: Props) {
  return (
    <div className="mt-6 card p-5">
      <div className="flex items-center gap-3 mb-3">
        <Loader2 className="h-5 w-5 animate-spin text-brand-600 shrink-0" />
        <span className="font-medium text-slate-900 dark:text-white">Processing upload...</span>
        <span className="ml-auto text-sm font-mono text-brand-600">{progress}%</span>
      </div>
      <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-brand-600 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="text-xs text-slate-400 mt-2">
        Identifying files, extracting metadata, routing to AI pipeline...
      </p>
    </div>
  );
}
