/**
 * useUpload hook — handles file upload to backend with progress.
 */
"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import toast from "react-hot-toast";

export function useUpload() {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(async (files: File[]) => {
    setIsUploading(true);
    setProgress(0);
    setError(null);
    setResult(null);

    const formData = new FormData();

    if (files.length === 1) {
      formData.append("file", files[0]);
      formData.append("anonymize", "false");

      try {
        const response = await apiClient.post("/upload/dicom", formData, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (event) => {
            if (event.total) {
              setProgress(Math.round((event.loaded / event.total) * 80));
            }
          },
        });
        setProgress(100);
        setResult(response.data);
        toast.success("Upload successful!");
      } catch (err: any) {
        const msg =
          err.response?.data?.detail ?? err.message ?? "Upload failed.";
        setError(msg);
        toast.error(msg);
      } finally {
        setIsUploading(false);
      }
    } else {
      // Batch upload
      const batchForm = new FormData();
      files.forEach((f) => batchForm.append("files", f));
      try {
        const response = await apiClient.post("/upload/batch", batchForm, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (event) => {
            if (event.total) {
              setProgress(Math.round((event.loaded / event.total) * 80));
            }
          },
        });
        setProgress(100);
        setResult(response.data);
        toast.success(`${files.length} files queued for processing`);
      } catch (err: any) {
        const msg = err.response?.data?.detail ?? "Batch upload failed.";
        setError(msg);
        toast.error(msg);
      } finally {
        setIsUploading(false);
      }
    }
  }, []);

  const reset = useCallback(() => {
    setIsUploading(false);
    setProgress(0);
    setResult(null);
    setError(null);
  }, []);

  return { upload, isUploading, progress, result, error, reset };
}
