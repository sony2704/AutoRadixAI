import Link from "next/link";
import { Brain, ArrowRight, Upload, Eye, FileText, Zap } from "lucide-react";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-brand-950 to-slate-900">
      {/* Nav */}
      <nav className="border-b border-white/10 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-8 w-8 text-brand-400" />
          <span className="text-xl font-bold text-white">AutoRadixAI</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-slate-300 hover:text-white transition text-sm font-medium">
            Sign In
          </Link>
          <Link
            href="/register"
            className="bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 py-24 text-center max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-brand-900/50 border border-brand-700/50 rounded-full px-4 py-1 text-brand-300 text-sm mb-6">
          <Zap className="h-3.5 w-3.5" /> AI-Powered Medical Imaging Intelligence
        </div>
        <h1 className="text-5xl md:text-7xl font-extrabold text-white leading-tight mb-6">
          Auto
          <span className="text-brand-400">Radix</span>
          AI
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          The core radiology intelligence platform. Upload DICOM studies, run AI inference,
          generate explainable reports — all in one unified workflow.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white px-8 py-4 rounded-xl text-lg font-semibold transition shadow-lg shadow-brand-900/50"
          >
            Open Dashboard <ArrowRight className="h-5 w-5" />
          </Link>
          <Link
            href="/upload"
            className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-8 py-4 rounded-xl text-lg font-semibold transition border border-white/20"
          >
            <Upload className="h-5 w-5" /> Upload Study
          </Link>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="px-6 pb-24 max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition group"
            >
              <div className="h-10 w-10 rounded-xl bg-brand-600/20 flex items-center justify-center mb-4">
                <f.icon className="h-5 w-5 text-brand-400" />
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 px-6 py-6 text-center text-slate-500 text-sm">
        © 2026 AutoRadixAI. Built for medical AI research and clinical decision support.
      </footer>
    </main>
  );
}

const FEATURES = [
  {
    icon: Upload,
    title: "Smart DICOM Upload",
    description:
      "Drag-drop DICOM files, ZIPs, or folders. Auto-detects modality, organizes by Study/Series, handles corrupted files gracefully.",
  },
  {
    icon: Brain,
    title: "8 AI Agents",
    description:
      "File Identifier, Anonymizer, Feature Extractor, Model Matcher, Preprocessor, Inference, Explainability, and Report agents working in concert.",
  },
  {
    icon: Eye,
    title: "DICOM Viewer",
    description:
      "Built-in Cornerstone.js viewer with slice navigation, zoom, pan, windowing controls, and segmentation overlays.",
  },
  {
    icon: Zap,
    title: "Real-time Inference",
    description:
      "GPU-accelerated PyTorch/MONAI inference with WebSocket progress updates. CPU fallback for any hardware.",
  },
  {
    icon: FileText,
    title: "Structured Reports",
    description:
      "Generate AI radiology reports in JSON, HTML, and PDF with GradCAM heatmaps and clinical explanations.",
  },
  {
    icon: Brain,
    title: "HIPAA-Ready",
    description:
      "JWT authentication, role-based access, DICOM anonymization, full audit trails, and security headers.",
  },
];
