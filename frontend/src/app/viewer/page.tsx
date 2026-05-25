"use client";

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { DicomViewer } from "@/components/viewer/dicom-viewer";
import { ViewerToolbar } from "@/components/viewer/viewer-toolbar";
import { SeriesPanel } from "@/components/viewer/series-panel";
import { MetadataPanel } from "@/components/viewer/metadata-panel";

export default function ViewerPage() {
  const searchParams = useSearchParams();
  const studyId = searchParams.get("study");
  const [selectedSeries, setSelectedSeries] = useState<string | null>(null);
  const [activeTool, setActiveTool] = useState<string>("wwwc");
  const [showMetadata, setShowMetadata] = useState(false);

  return (
    <div className="flex h-screen bg-slate-950">
      <Sidebar compact />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="DICOM Viewer" dark />
        <div className="flex-1 flex overflow-hidden">
          {/* Series Panel */}
          <SeriesPanel
            studyId={studyId}
            selectedSeries={selectedSeries}
            onSelectSeries={setSelectedSeries}
          />

          {/* Main Viewer Area */}
          <div className="flex-1 flex flex-col bg-black">
            <ViewerToolbar
              activeTool={activeTool}
              onToolChange={setActiveTool}
              onToggleMetadata={() => setShowMetadata((v) => !v)}
            />
            <div className="flex-1 relative">
              <DicomViewer studyId={studyId} seriesId={selectedSeries} activeTool={activeTool} />
            </div>
          </div>

          {/* Metadata Panel */}
          {showMetadata && <MetadataPanel studyId={studyId} seriesId={selectedSeries} />}
        </div>
      </div>
    </div>
  );
}
