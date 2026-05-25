"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { UploadProgress } from "@/components/upload/upload-progress";
import { UploadResult } from "@/components/upload/upload-result";
import { useUpload } from "@/hooks/use-upload";
import { CloudUpload, FileImage, FolderOpen, Archive, Image as ImageIcon, File } from "lucide-react";
import clsx from "clsx";

export default function UploadPage() {
  const { upload, isUploading, progress, result, error, reset } = useUpload();

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        upload(acceptedFiles);
      }
    },
    [upload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/dicom": [".dcm"],
      "application/zip": [".zip"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "application/pdf": [".pdf"],
    },
    maxSize: 500 * 1024 * 1024,
    multiple: true,
  });

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="Upload Study" />
        <main className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
              Upload Medical Images
            </h2>
            <p className="text-slate-500 text-sm">
              Supports DICOM (.dcm), ZIP archives, folders, PNG/JPG, and PDF files.
            </p>
          </div>

          {/* Drop Zone */}
          {!result && (
            <div
              {...getRootProps()}
              className={clsx(
                "border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200",
                isDragActive
                  ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20 scale-[1.01]"
                  : "border-slate-300 dark:border-slate-700 hover:border-brand-400 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              )}
            >
              <input {...getInputProps()} />
              <CloudUpload
                className={clsx(
                  "h-16 w-16 mx-auto mb-4 transition-colors",
                  isDragActive ? "text-brand-500" : "text-slate-400"
                )}
              />
              {isDragActive ? (
                <p className="text-brand-600 font-semibold text-lg">Drop files here...</p>
              ) : (
                <>
                  <p className="text-slate-700 dark:text-slate-300 font-semibold text-lg mb-2">
                    Drag & drop files or click to browse
                  </p>
                  <p className="text-slate-400 text-sm mb-6">
                    Maximum file size: 500 MB per file
                  </p>
                </>
              )}

              {/* Supported formats */}
              <div className="flex flex-wrap justify-center gap-3 mt-4">
                {[
                  { label: "DICOM", icon: <FileImage className="h-3.5 w-3.5" />, color: "blue" },
                  { label: "ZIP", icon: <Archive className="h-3.5 w-3.5" />, color: "amber" },
                  { label: "PNG/JPG", icon: <ImageIcon className="h-3.5 w-3.5" />, color: "green" },
                  { label: "PDF", icon: <File className="h-3.5 w-3.5" />, color: "purple" },
                ].map((f) => (
                  <span
                    key={f.label}
                    className={`badge badge-${f.color} flex items-center gap-1`}
                  >
                    {f.icon} {f.label}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Progress */}
          {isUploading && <UploadProgress progress={progress} />}

          {/* Error */}
          {error && (
            <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          {/* Result */}
          {result && <UploadResult result={result} onReset={reset} />}
        </main>
      </div>
    </div>
  );
}
