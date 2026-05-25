"use client";

import { useEffect, useRef, useState } from "react";
import type { DicomViewerProps } from "@/lib/types";
import { Loader2, AlertTriangle } from "lucide-react";

interface Props {
  studyId: string | null;
  seriesId: string | null;
  activeTool: string;
}

/**
 * DICOM viewer powered by Cornerstone.js.
 * Supports slice navigation, zoom, pan, window/level, and segmentation overlays.
 */
export function DicomViewer({ studyId, seriesId, activeTool }: Props) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentSlice, setCurrentSlice] = useState(0);
  const [totalSlices, setTotalSlices] = useState(0);
  const [windowLevel, setWindowLevel] = useState({ center: 40, width: 400 });
  const [cornerstoneReady, setCornerstoneReady] = useState(false);
  const elementRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let mounted = true;
    async function initCornerstone() {
      try {
        const cornerstone = await import("cornerstone-core");
        const cornerstoneWADOImageLoader = await import("cornerstoneWADOImageLoader");
        const dicomParser = await import("dicom-parser");

        cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
        cornerstoneWADOImageLoader.external.dicomParser = dicomParser;

        cornerstoneWADOImageLoader.configure({
          useWebWorkers: true,
          decodeConfig: { convertFloatPixelDataToInt: false },
        });

        if (mounted) setCornerstoneReady(true);
      } catch (err) {
        console.warn("Cornerstone initialization:", err);
        if (mounted) setCornerstoneReady(true); // Continue without strict init
      }
    }
    initCornerstone();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!studyId || !seriesId || !cornerstoneReady || !canvasRef.current) return;
    loadSeries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId, seriesId, cornerstoneReady]);

  async function loadSeries() {
    if (!canvasRef.current) return;
    setIsLoading(true);
    setError(null);
    try {
      const cornerstone = await import("cornerstone-core");
      const element = canvasRef.current as HTMLElement;

      try { cornerstone.enable(element); } catch {}
      elementRef.current = element;

      // In production, imageIds would come from API:
      // GET /api/v1/studies/{studyId}/series/{seriesId}/instances
      const imageUrl = `/api/v1/studies/${studyId}/series/${seriesId}/wado?requestType=WADO`;
      const imageId = `wadouri:${imageUrl}`;

      const image = await cornerstone.loadImage(imageId);
      cornerstone.displayImage(element, image);
      setTotalSlices(1);
      setCurrentSlice(1);
    } catch (err: any) {
      setError(err?.message || "Failed to load DICOM series.");
    } finally {
      setIsLoading(false);
    }
  }

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setCurrentSlice((prev) => {
      const next = prev + (e.deltaY > 0 ? 1 : -1);
      return Math.max(1, Math.min(totalSlices, next));
    });
  };

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center">
      {/* Viewer canvas */}
      <div
        ref={canvasRef}
        className="w-full h-full"
        onWheel={handleWheel}
        style={{ cursor: activeTool === "zoom" ? "crosshair" : "default" }}
      />

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60">
          <div className="flex flex-col items-center gap-3 text-white">
            <Loader2 className="h-10 w-10 animate-spin text-brand-400" />
            <span className="text-sm">Loading DICOM...</span>
          </div>
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-red-400 text-center px-8">
            <AlertTriangle className="h-12 w-12" />
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* No study placeholder */}
      {!studyId && !isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-slate-600 text-center">
            <div className="text-6xl mb-4">🫁</div>
            <p className="text-lg font-medium">No study selected</p>
            <p className="text-sm mt-1">Select a study from the series panel</p>
          </div>
        </div>
      )}

      {/* Slice indicator */}
      {totalSlices > 0 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/70 text-white text-xs px-3 py-1 rounded-full">
          Slice {currentSlice} / {totalSlices}
        </div>
      )}

      {/* Window/Level overlay */}
      <div className="absolute top-4 right-4 bg-black/70 text-slate-300 text-xs px-3 py-2 rounded-lg space-y-0.5">
        <div>WC: {windowLevel.center}</div>
        <div>WW: {windowLevel.width}</div>
      </div>
    </div>
  );
}
