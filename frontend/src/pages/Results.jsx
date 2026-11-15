import React, { useEffect, useState } from 'react';
import { useParams, useLocation, Link } from 'react-router-dom';
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Download,
  FileCode,
  FileSpreadsheet,
  Layers,
  Loader2,
} from 'lucide-react';
import { fetchRunDetail, resolveImageUrl } from '../services/api';

const CLASS_BADGES = {
  0: { code: 'D00', name: 'Longitudinal Crack', color: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
  1: { code: 'D10', name: 'Transverse Crack', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
  2: { code: 'D20', name: 'Alligator Crack', color: 'bg-amber-500/10 text-amber-400 border-amber-500/30' },
  3: { code: 'D40', name: 'Pothole', color: 'bg-red-500/10 text-red-400 border-red-500/30' },
};

export default function Results() {
  const { runId } = useParams();
  const location = useLocation();
  const [result, setResult] = useState(location.state?.result || null);
  const [loading, setLoading] = useState(!location.state?.result && !!runId);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (runId && (!result || result.run_id !== runId)) {
      setLoading(true);
      fetchRunDetail(runId)
        .then((data) => {
          setResult(data);
          setError(null);
        })
        .catch((err) => {
          console.error(err);
          setError(err.response?.data?.detail || 'Failed to fetch detection run details.');
        })
        .finally(() => setLoading(false));
    }
  }, [runId]);

  const exportJSON = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `detection_${result.run_id || 'run'}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportCSV = () => {
    if (!result || !result.detections) return;
    const headers = ['id', 'class_id', 'class_name', 'confidence', 'x1', 'y1', 'x2', 'y2'];
    const rows = result.detections.map((d, idx) => [
      idx + 1,
      d.class_id,
      `"${d.class_name}"`,
      d.confidence,
      d.bbox_xmin ?? d.x1,
      d.bbox_ymin ?? d.y1,
      d.bbox_xmax ?? d.x2,
      d.bbox_ymax ?? d.y2,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `detections_${result.run_id || 'run'}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="text-center py-24 space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400 mx-auto" />
        <p className="text-sm text-slate-400">Loading detection inspection record...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-xl mx-auto text-center py-20 space-y-4">
        <div className="w-16 h-16 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white">Detection Run Not Found</h2>
        <p className="text-sm text-slate-400">
          {error || 'No inspection result data exists for the specified identifier.'}
        </p>
        <Link
          to="/analyze"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Run New Analysis
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
            <span>RUN IDENTIFIER:</span>
            <span className="text-emerald-400 font-bold">{result.run_id || result.id}</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <span>Inspection Summary</span>
            <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full font-medium border border-slate-700">
              {result.image_name}
            </span>
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={exportCSV}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            Export CSV
          </button>
          <button
            onClick={exportJSON}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
          >
            <FileCode className="w-4 h-4 text-blue-400" />
            Export JSON
          </button>
          <Link
            to="/analyze"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            New Inspection
          </Link>
        </div>
      </div>

      {/* Meta KPI Badges */}
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
          <span className="text-xs text-slate-400 block mb-1">Model Architecture</span>
          <span className="text-lg font-bold text-white truncate block">{result.model_name}</span>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-400 block mb-1">Confidence Filter</span>
          <span className="text-lg font-bold text-amber-400 block">
            {result.confidence_threshold ?? 0.25}
          </span>
        </div>
      </div>

      {/* Side-by-side Images */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Original Input Image
          </span>
          <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center min-h-[300px]">
            <img
              src={resolveImageUrl(result.image_url)}
              alt="Original Road"
              className="max-h-96 w-auto object-contain"
            />
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Localized Bounding Box Overlay
          </span>
          <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center min-h-[300px]">
            <img
              src={resolveImageUrl(result.output_image_url)}
              alt="Annotated Defects"
              className="max-h-96 w-auto object-contain"
            />
          </div>
        </div>
      </div>

      {/* Bounding Box Coordinate Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h2 className="text-base font-bold text-white flex items-center justify-between">
          <span>Detailed Defect Coordinates ({result.detections?.length || 0})</span>
          <span className="text-xs text-slate-400 font-normal">Pixel coordinates [x1, y1, x2, y2]</span>
        </h2>

        {!result.detections || result.detections.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            No defect bounding boxes recorded for this image.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-950/70 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Code</th>
                  <th className="px-4 py-3">Damage Category</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-4 py-3 font-mono">x1 (xmin)</th>
                  <th className="px-4 py-3 font-mono">y1 (ymin)</th>
                  <th className="px-4 py-3 font-mono">x2 (xmax)</th>
                  <th className="px-4 py-3 font-mono">y2 (ymax)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {result.detections.map((det, idx) => {
                  const badge = CLASS_BADGES[det.class_id] || {
                    code: `D0${det.class_id}`,
                    name: det.class_name,
                    color: 'bg-slate-800 text-slate-300 border-slate-700',
                  };
                  return (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 text-slate-500">{idx + 1}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded border font-semibold ${badge.color}`}>
                          {badge.code}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-sans font-medium text-white">{det.class_name}</td>
                      <td className="px-4 py-3 text-emerald-400 font-bold">
                        {(det.confidence * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-3 text-slate-400">{Math.round(det.bbox_xmin ?? det.x1)}</td>
                      <td className="px-4 py-3 text-slate-400">{Math.round(det.bbox_ymin ?? det.y1)}</td>
                      <td className="px-4 py-3 text-slate-400">{Math.round(det.bbox_xmax ?? det.x2)}</td>
                      <td className="px-4 py-3 text-slate-400">{Math.round(det.bbox_ymax ?? det.y2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
