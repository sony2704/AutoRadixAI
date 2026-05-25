// Shared TypeScript types for AutoRadixAI frontend

export interface User {
  id: string;
  email: string;
  username: string;
  role: "admin" | "radiologist" | "clinician" | "researcher" | "viewer";
}

export interface Study {
  id: string;
  patient_id: string;
  study_instance_uid: string;
  study_description?: string;
  modality: string;
  status: "pending" | "processing" | "analyzed" | "failed";
  num_series: number;
  num_instances: number;
  uploaded_at: string;
  owner_id: string;
}

export interface Series {
  id: string;
  study_id: string;
  series_instance_uid: string;
  description?: string;
  series_number?: number;
  num_instances: number;
}

export interface Prediction {
  id: string;
  study_id: string;
  model_name: string;
  status: "pending" | "running" | "completed" | "failed";
  top_prediction?: string;
  top_confidence?: number;
  confidence_scores?: Record<string, number>;
  labels?: string[];
  heatmap_path?: string;
  created_at: string;
  completed_at?: string;
}

export interface AIReport {
  study_id: string;
  patient_id: string;
  modality: string;
  body_part: string;
  study_description: string;
  top_prediction: string;
  top_confidence: number;
  labels: string[];
  confidence_scores: Record<string, number>;
  model_name: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  findings: string;
  recommendations: string;
  disclaimer: string;
}

export interface UploadResult {
  upload_id: string;
  summary: {
    valid_dicoms: number;
    corrupted_files: number;
    non_dicom_files: number;
    studies: Record<string, { description: string }>;
  };
  model_match?: {
    model: { name: string; task: string } | null;
    confidence: string;
  };
}

// Props for DICOM viewer component
export interface DicomViewerProps {
  studyId: string | null;
  seriesId: string | null;
  className?: string;
}
