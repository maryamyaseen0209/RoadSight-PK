import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, Sliders, Image as ImageIcon, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import { runPrediction } from '../services/api';

export default function Analyze() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [confidence, setConfidence] = useState(0.25);
  const [iou, setIou] = useState(0.45);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('Please select a valid image file (JPG or PNG)');
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
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
      const result = await runPrediction(selectedFile, confidence, iou);
      // Navigate to results page with result state
      navigate('/results', { state: { result } });
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Inference execution failed. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Pavement Defect Analysis</h1>
        <p className="text-sm text-slate-400">
          Upload an asphalt or concrete roadway image to run automated defect localization and classification.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Upload Area */}
          <div className="md:col-span-2">
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center transition-all min-h-[340px] relative ${
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
                    className="max-h-64 rounded-xl object-contain shadow-md"
                  />
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 font-mono">{selectedFile?.name}</span>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedFile(null);
                        setPreviewUrl(null);
                      }}
                      className="text-xs text-red-400 hover:text-red-300 underline"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-emerald-400 shadow-inner">
                    <UploadCloud className="w-7 h-7" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">
                      Drag and drop your road image here, or{' '}
                      <label className="text-emerald-400 hover:text-emerald-300 cursor-pointer underline">
                        browse
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          onChange={handleFileChange}
                        />
                      </label>
                    </p>
                    <p className="text-xs text-slate-500 mt-1">Supports JPG, PNG up to 25MB</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Hyperparameter Settings */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
            <div className="flex items-center gap-2 text-white font-semibold text-sm border-b border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <span>Inference Parameters</span>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">Confidence Threshold</span>
                <span className="text-emerald-400 font-mono font-medium">{confidence}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.95"
                step="0.05"
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                className="w-full accent-emerald-500 bg-slate-800 rounded-lg cursor-pointer"
              />
              <p className="text-[11px] text-slate-500">Filter out low-certainty predictions</p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">NMS IoU Threshold</span>
                <span className="text-emerald-400 font-mono font-medium">{iou}</span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.90"
                step="0.05"
                value={iou}
                onChange={(e) => setIou(parseFloat(e.target.value))}
                className="w-full accent-emerald-500 bg-slate-800 rounded-lg cursor-pointer"
              />
              <p className="text-[11px] text-slate-500">Non-Maximum Suppression overlap threshold</p>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={!selectedFile || loading}
                className={`w-full py-3 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-lg ${
                  selectedFile && !loading
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                }`}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing Inference...</span>
                  </>
                ) : (
                  <>
                    <span>Detect Road Defects</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
