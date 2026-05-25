"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface Props {
  studyId: string | null;
  seriesId: string | null;
}

export function MetadataPanel({ studyId, seriesId }: Props) {
  const { data } = useQuery({
    queryKey: ["study-meta", studyId],
    queryFn: () =>
      studyId ? apiClient.get(`/studies/${studyId}`).then((r) => r.data) : null,
    enabled: !!studyId,
  });

  const meta = data ?? MOCK_META;

  return (
    <div className="w-64 bg-slate-900 border-l border-slate-800 overflow-y-auto">
      <div className="px-4 py-3 border-b border-slate-800">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Metadata</p>
      </div>
      <div className="p-4 space-y-3">
        {Object.entries(meta).map(([key, val]) => (
          <div key={key}>
            <p className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">{key.replace(/_/g, " ")}</p>
            <p className="text-xs text-slate-200 font-mono break-all">{String(val ?? "—")}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

const MOCK_META = {
  modality: "MR",
  study_description: "Brain MRI T1/T2/FLAIR",
  study_date: "2026-05-25",
  institution: "AutoRadixAI Test Hospital",
  num_series: 4,
  num_instances: 100,
  status: "analyzed",
};
