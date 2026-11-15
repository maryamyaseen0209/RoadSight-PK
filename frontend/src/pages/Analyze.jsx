import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  UploadCloud,
  Sliders,
  ArrowRight,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Download,
  Eye,
  RefreshCw,
  Layers,
} from 'lucide-react';
import { runPrediction, resolveImageUrl } from '../services/api';

const CLASS_BADGES = {
  0: { name: 'Longitudinal Crack [D00]', color: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
  1: { name: 'Transverse Crack [D10]', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
  2: { name: 'Alligator Crack [D20]', color: 'bg-amber-500/10 text-amber-400 border-amber-500/30' },
  3: { name: 'Pothole [D40]', color: 'bg-red-500/10 text-red-400 border-red-500/30' },
};

const getUnifiedLabel = (defect, allDetections = []) => {
  if (
    defect.confidence < 0.40 &&
    (defect.class_name === 'Alligator Crack' || defect.class_name?.includes('Alligator') || defect.class_id === 2)
  ) {
    return 'Severe Surface Deterioration';
  }

  // Override whenever multiple defect types overlap within 0.40 IOU
  if (allDetections && allDetections.length > 1) {
    const boxA = [
      defect.bbox_xmin ?? defect.x1 ?? 0,
      defect.bbox_ymin ?? defect.y1 ?? 0,
      defect.bbox_xmax ?? defect.x2 ?? 0,
      defect.bbox_ymax ?? defect.y2 ?? 0,
    ];
    for (const other of allDetections) {
      if (other !== defect && (other.class_id !== defect.class_id || other.class_name !== defect.class_name)) {
        const boxB = [
          other.bbox_xmin ?? other.x1 ?? 0,
          other.bbox_ymin ?? other.y1 ?? 0,
          other.bbox_xmax ?? other.x2 ?? 0,
          other.bbox_ymax ?? other.y2 ?? 0,
        ];
        const xA = Math.max(boxA[0], boxB[0]);
        const yA = Math.max(boxA[1], boxB[1]);
        const xB = Math.min(boxA[2], boxB[2]);
        const yB = Math.min(boxA[3], boxB[3]);
        const inter = Math.max(0, xB - xA) * Math.max(0, yB - yA);
        const areaA = Math.max(1, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]));
        const areaB = Math.max(1, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]));
        const iou = inter / Math.max(1, areaA + areaB - inter);
        if (iou >= 0.35) {
          return 'Severe Structural Damage';
        }
      }
    }
  }

  return defect.class_name;
};

const getBadgeProps = (defect, allDetections) => {
  const label = getUnifiedLabel(defect, allDetections);
  if (label === 'Severe Surface Deterioration') {
    return { name: label, color: 'bg-amber-500/10 text-amber-400 border-amber-500/30 font-semibold' };
  }
  if (label === 'Severe Structural Damage') {
    return { name: label, color: 'bg-rose-500/10 text-rose-400 border-rose-500/30 font-bold' };
  }
  const badge = CLASS_BADGES[defect.class_id] || {
    name: label,
    color: 'bg-slate-800 text-slate-300 border-slate-700',
  };
  return { ...badge, name: label };
};

export default function Analyze() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [confidence, setConfidence] = useState(0.15);
  const [selectedModel, setSelectedModel] = useState('YOLO');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = (file) => {
    const allowed = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type)) {
      setError('Please select a valid image file (JPEG, PNG, or WebP).');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10 MB limit.');
      return;
    }
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
    setResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a pavement image to analyze.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await runPrediction(selectedFile, confidence, selectedModel);
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Inference execution failed. Ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result?.output_image_url) return;
    const link = document.createElement('a');
    link.href = resolveImageUrl(result.output_image_url);
    link.download = `annotated_${result.image_name || 'road'}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Pavement Defect Analysis</h1>
        <p className="text-sm text-slate-400 mt-1">
          Upload an asphalt or concrete roadway image to run automated bounding-box localization and damage classification.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Upload & Parameter Form */}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Upload Dropzone */}
        <div className="md:col-span-2">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center transition-all min-h-[360px] relative ${
              previewUrl
                ? 'border-emerald-500/50 bg-slate-900/50'
                : 'border-slate-700 hover:border-slate-500 bg-slate-900/80'
            }`}
          >
            {previewUrl ? (
              <div className="space-y-4 w-full flex flex-col items-center">
                <img
                  src={previewUrl}
                  alt="Pavement preview"
                  className="max-h-72 rounded-xl object-contain shadow-md"
                />
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400 font-mono">{selectedFile?.name}</span>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewUrl(null);
                      setResult(null);
                    }}
                    className="text-xs text-red-400 hover:text-red-300 underline"
                  >
                    Change Image
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-emerald-400 shadow-inner">
                  <UploadCloud className="w-8 h-8" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    Drag & drop your road pavement image here, or{' '}
                    <label className="text-emerald-400 hover:text-emerald-300 cursor-pointer underline">
                      browse
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        className="hidden"
                        onChange={handleFileChange}
                      />
                    </label>
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Supports JPEG, PNG, WebP up to 10 MB</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Hyperparameter Settings */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6 flex flex-col justify-between">
          <div className="space-y-5">
            <div className="flex items-center gap-2 text-white font-semibold text-sm border-b border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <span>Inference Parameters</span>
            </div>

            {/* Model Architecture Selector */}
            <div className="space-y-2">
              <label className="text-xs text-slate-300 font-medium block">Detector Architecture</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-white text-xs rounded-xl px-3 py-2.5 focus:border-emerald-500 focus:outline-none"
              >
                <option value="YOLO">YOLO26n (International Baseline • Recommended)</option>
                <option value="YOLO (Pakistani)">YOLO26n (Pakistani Fine-Tuned)</option>
                <option value="Faster R-CNN">Faster R-CNN ResNet-50 FPN V2 (High Precision)</option>
              </select>
            </div>

            {/* Confidence Threshold */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">Confidence Threshold</span>
                <span className="text-emerald-400 font-mono font-medium">{confidence}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.90"
                step="0.05"
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                className="w-full accent-emerald-500 bg-slate-800 rounded-lg cursor-pointer"
              />
              <p className="text-[11px] text-slate-500">Tip: For subtle road cracks, use 0.10 – 0.20</p>
            </div>
          </div>

          <button
            type="submit"
            disabled={!selectedFile || loading}
            className={`w-full py-3.5 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-lg ${
              selectedFile && !loading
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Inference...</span>
              </>
            ) : (
              <>
                <span>Analyze Road Defects</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Inference Results Section */}
      {result && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6 animate-fade-in">
          {/* Header & Meta */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider block">
                Detection Complete • {result.model_name}
              </span>
              <h2 className="text-xl font-bold text-white flex items-center gap-2 mt-0.5">
                <span>{result.image_name}</span>
                <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-0.5 rounded-full border border-slate-700 font-mono">
                  {result.inference_time_ms} ms
                </span>
              </h2>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleDownload}
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                Download Annotated Image
              </button>
              <Link
                to={`/results/${result.run_id}`}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-colors"
              >
                Full Inspection Details
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Side-by-Side Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <span className="text-xs font-medium text-slate-400 block uppercase tracking-wider">
                Original Input
              </span>
              <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center min-h-[300px]">
                <img
                  src={resolveImageUrl(result.image_url)}
                  alt="Original road"
                  className="max-h-80 w-auto object-contain"
                />
              </div>
            </div>
            <div className="space-y-2">
              <span className="text-xs font-medium text-slate-400 block uppercase tracking-wider">
                Annotated Defect Localization
              </span>
              <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center min-h-[300px]">
                <img
                  src={resolveImageUrl(result.output_image_url)}
                  alt="Annotated defects"
                  className="max-h-80 w-auto object-contain"
                />
              </div>
            </div>
          </div>

          {/* Detections Breakdown */}
          <div className="space-y-3 pt-2">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Identified Defect Boxes ({result.total_detections})
            </h3>

            {result.total_detections === 0 ? (
              <div className="text-center py-8 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                <p className="text-sm font-semibold text-slate-200">No Structural Defects Detected</p>
                <p className="text-xs text-slate-500">
                  The road surface appears defect-free or distress features are below confidence threshold {confidence}.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {result.detections.map((det, idx) => {
                  const badge = getBadgeProps(det, result.detections);
                  return (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${badge.color}`}>
                          {badge.name}
                        </span>
                        <span className="text-xs font-mono font-bold text-emerald-400">
                          {(det.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-emerald-500 h-full rounded-full"
                          style={{ width: `${Math.round(det.confidence * 100)}%` }}
                        ></div>
                      </div>
                      <div className="text-[11px] font-mono text-slate-500 flex justify-between">
                        <span>Box: [{Math.round(det.bbox_xmin)}, {Math.round(det.bbox_ymin)}]</span>
                        <span>[{Math.round(det.bbox_xmax)}, {Math.round(det.bbox_ymax)}]</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
