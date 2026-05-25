"use client";

import { CheckCircle2, ArrowRight, Brain, RotateCcw } from "lucide-react";
import Link from "next/link";

interface Props {
  result: any;
  onReset: () => void;
}

export function UploadResult({ result, onReset }: Props) {
  const summary = result?.summary ?? {};
  const match = result?.model_match;
  const prep = result?.preprocessing_config;

  return (
    <div className="mt-6 space-y-4 animate-slide-up">
      {/* Success banner */}
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 flex items-start gap-3">
        <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-green-700 dark:text-green-300">{result?.message ?? "Upload successful"}</p>
          <p className="text-sm text-green-600 dark:text-green-400 mt-0.5">
            Upload ID: <code className="font-mono">{result?.upload_id}</code>
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className="card p-5">
        <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Study Summary</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Studies",         value: Object.keys(summary.studies ?? {}).length },
            { label: "Valid DICOMs",    value: summary.valid_dicoms ?? 0 },
            { label: "Corrupted Files", value: summary.corrupted_files ?? 0 },
            { label: "Other Files",     value: summary.non_dicom_files ?? 0 },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{s.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Model match */}
      {match && match.model_name && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="h-5 w-5 text-brand-600" />
            <h3 className="font-semibold text-slate-900 dark:text-white">AI Model Matched</h3>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-slate-500">Model:</span> <span className="font-medium text-slate-900 dark:text-white">{match.model_name.replace(/_/g, " ")}</span></div>
            <div><span className="text-slate-500">Task:</span> <span className="font-medium text-slate-900 dark:text-white">{match.task?.replace(/_/g, " ")}</span></div>
            <div><span className="text-slate-500">Confidence:</span> <span className="badge badge-green">{match.confidence}</span></div>
            <div><span className="text-slate-500">Score:</span> <span className="font-medium">{match.score?.toFixed(1)}</span></div>
          </div>
          <p className="text-xs text-slate-400 mt-3 italic">{match.reasoning}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        {result?.study_ids?.[0] && (
          <Link
            href={`/viewer?study=${result.study_ids[0]}`}
            className="btn-primary flex items-center gap-2"
          >
            Open in Viewer <ArrowRight className="h-4 w-4" />
          </Link>
        )}
        {result?.study_ids?.[0] && (
          <Link
            href={`/inference?study=${result.study_ids[0]}`}
            className="btn-secondary flex items-center gap-2"
          >
            <Brain className="h-4 w-4" /> Run AI Inference
          </Link>
        )}
        <button onClick={onReset} className="btn-secondary flex items-center gap-2">
          <RotateCcw className="h-4 w-4" /> Upload Another
        </button>
      </div>
    </div>
  );
}
