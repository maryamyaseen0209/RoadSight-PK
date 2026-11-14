import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { AlertCircle, ArrowLeft, CheckCircle2, Clock, Cpu, Download, Eye, Layers } from 'lucide-react';

const CLASS_BADGES = {
  0: { name: 'Longitudinal Crack [D00]', color: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
  1: { name: 'Transverse Crack [D10]', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
  2: { name: 'Alligator Crack [D20]', color: 'bg-amber-500/10 text-amber-400 border-amber-500/30' },
  3: { name: 'Pothole [D40]', color: 'bg-red-500/10 text-red-400 border-red-500/30' },
};

export default function Results() {
  const location = useLocation();
  const result = location.state?.result;

  if (!result) {
    return (
      <div className="max-w-xl mx-auto text-center py-16 space-y-4">
        <div className="w-16 h-16 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white">No Detection Results Found</h2>
        <p className="text-sm text-slate-400">
          Upload and run inference on a pavement image to view detections and bounding box overlays.
        </p>
        <Link
          to="/analyze"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Go to Analyze Page
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
            <span>RUN ID:</span>
            <span className="text-emerald-400">{result.run_id}</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <span>Inspection Results</span>
            <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full font-medium border border-slate-700">
              {result.image_name}
            </span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/analyze"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            New Inspection
          </Link>
        </div>
      </div>

      {/* Metric Highlights */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-400 block mb-1">Detections Found</span>
          <span className="text-2xl font-bold text-emerald-400">{result.total_detections}</span>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-400 block mb-1">Inference Latency</span>
          <span className="text-2xl font-bold text-blue-400">{result.inference_time_ms} ms</span>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-400 block mb-1">Active Model</span>
          <span className="text-xl font-bold text-white truncate block">{result.model_name}</span>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-400 block mb-1">Database Sync</span>
          <span className="text-sm font-semibold text-teal-400 flex items-center gap-1.5 mt-1">
            <CheckCircle2 className="w-4 h-4" />
            Persisted in SQLite
          </span>
        </div>
      </div>

      {/* Main Visual & Detections Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rendered Pavement View */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col items-center justify-center">
          <div className="w-full relative rounded-xl overflow-hidden bg-slate-950 flex items-center justify-center border border-slate-800">
            <img
              src={result.output_image_url || result.image_url}
              alt="Road Defect Detection View"
              className="max-h-[500px] w-auto object-contain"
            />
          </div>
          <div className="w-full flex items-center justify-between text-xs text-slate-500 mt-3 px-1">
            <span>Pavement Image Inspection Layer</span>
            <span className="font-mono">Output Artifact: {result.output_image_url}</span>
          </div>
        </div>

        {/* Detected Defects List */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-3">
              Identified Defect Boxes ({result.detections?.length || 0})
            </h2>

            {result.detections?.length === 0 ? (
              <div className="text-center py-12 px-4 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                <p className="text-sm font-semibold text-slate-200">No Defects Exceeding Threshold</p>
                <p className="text-xs text-slate-500">
                  The road surface either lacks severe defects or the confidence threshold filtered low-certainty candidates.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
                {result.detections.map((det, idx) => {
                  const badge = CLASS_BADGES[det.class_id] || {
                    name: det.class_name,
                    color: 'bg-slate-700 text-slate-300 border-slate-600',
                  };
                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${badge.color}`}
                        >
                          {badge.name}
                        </span>
                        <span className="text-xs font-mono font-medium text-emerald-400">
                          {(det.confidence * 100).toFixed(1)}% Conf
                        </span>
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 flex justify-between pt-1">
                        <span>
                          [{det.bbox_xmin.toFixed(0)}, {det.bbox_ymin.toFixed(0)}]
                        </span>
                        <span>
                          [{det.bbox_xmax.toFixed(0)}, {det.bbox_ymax.toFixed(0)}]
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800 text-xs text-slate-500">
            Coordinates normalized to source input dimensions.
          </div>
        </div>
      </div>
    </div>
  );
}
