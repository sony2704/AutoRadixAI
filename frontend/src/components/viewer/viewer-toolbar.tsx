"use client";

import {
  ZoomIn, ZoomOut, Move, Sun, RotateCcw, Ruler,
  Crosshair, FlipHorizontal, Maximize, Layers, Download, Info
} from "lucide-react";
import clsx from "clsx";

interface Props {
  activeTool: string;
  onToolChange: (tool: string) => void;
  onToggleMetadata: () => void;
}

const TOOLS = [
  { id: "wwwc",    icon: Sun,             label: "Window/Level",   group: 1 },
  { id: "zoom",    icon: ZoomIn,          label: "Zoom",           group: 1 },
  { id: "pan",     icon: Move,            label: "Pan",            group: 1 },
  { id: "rotate",  icon: RotateCcw,       label: "Rotate",         group: 1 },
  { id: "length",  icon: Ruler,           label: "Length",         group: 2 },
  { id: "probe",   icon: Crosshair,       label: "Probe",          group: 2 },
  { id: "flip",    icon: FlipHorizontal,  label: "Flip H",         group: 3 },
  { id: "fit",     icon: Maximize,        label: "Fit to Window",  group: 3 },
  { id: "overlay", icon: Layers,          label: "Overlays",       group: 4 },
];

export function ViewerToolbar({ activeTool, onToolChange, onToggleMetadata }: Props) {
  return (
    <div className="h-12 bg-slate-900 border-b border-slate-800 flex items-center px-4 gap-1">
      {TOOLS.map((tool, idx) => {
        const showSep = idx > 0 && TOOLS[idx - 1].group !== tool.group;
        return (
          <div key={tool.id} className="flex items-center">
            {showSep && <div className="w-px h-6 bg-slate-700 mx-2" />}
            <button
              title={tool.label}
              onClick={() => onToolChange(tool.id)}
              className={clsx(
                "h-8 w-8 rounded-lg flex items-center justify-center transition-colors",
                activeTool === tool.id
                  ? "bg-brand-600 text-white"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              )}
            >
              <tool.icon className="h-4 w-4" />
            </button>
          </div>
        );
      })}
      <div className="flex-1" />
      <button
        title="Metadata"
        onClick={onToggleMetadata}
        className="h-8 w-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
      >
        <Info className="h-4 w-4" />
      </button>
      <button
        title="Download"
        className="h-8 w-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
      >
        <Download className="h-4 w-4" />
      </button>
    </div>
  );
}
