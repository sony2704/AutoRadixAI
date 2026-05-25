"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Layers, Loader2 } from "lucide-react";
import clsx from "clsx";

interface Props {
  studyId: string | null;
  selectedSeries: string | null;
  onSelectSeries: (id: string) => void;
}

export function SeriesPanel({ studyId, selectedSeries, onSelectSeries }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["study-series", studyId],
    queryFn: () =>
      studyId
        ? apiClient.get(`/studies/${studyId}/series`).then((r) => r.data)
        : Promise.resolve([]),
    enabled: !!studyId,
  });

  return (
    <div className="w-48 bg-slate-900 border-r border-slate-800 flex flex-col">
      <div className="px-3 py-3 border-b border-slate-800">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Series</p>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading && (
          <div className="flex justify-center py-4">
            <Loader2 className="h-4 w-4 animate-spin text-slate-500" />
          </div>
        )}
        {!studyId && (
          <p className="text-xs text-slate-600 text-center mt-4">No study selected</p>
        )}
        {(data ?? MOCK_SERIES).map((s: any) => (
          <button
            key={s.id}
            onClick={() => onSelectSeries(s.id)}
            className={clsx(
              "w-full text-left p-2 rounded-lg transition-colors",
              selectedSeries === s.id
                ? "bg-brand-600 text-white"
                : "text-slate-400 hover:bg-slate-800 hover:text-white"
            )}
          >
            <div className="flex items-center gap-2">
              <Layers className="h-3.5 w-3.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-xs font-medium truncate">
                  {s.description || `Series ${s.series_number ?? "?"}`}
                </p>
                <p className="text-xs opacity-60">{s.num_instances} inst.</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

const MOCK_SERIES = [
  { id: "s1", description: "AX T1 POST",    series_number: 1, num_instances: 30 },
  { id: "s2", description: "AX T2 FLAIR",   series_number: 2, num_instances: 30 },
  { id: "s3", description: "SAG T2",         series_number: 3, num_instances: 20 },
  { id: "s4", description: "COR T1",         series_number: 4, num_instances: 20 },
];
