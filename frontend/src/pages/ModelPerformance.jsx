import React, { useEffect, useState } from 'react';
import { BarChart3, CheckCircle2, Clock, Cpu, FileText, Info, Layers, RefreshCw, XCircle } from 'lucide-react';
import { fetchMetrics, fetchModelInfo } from '../services/api';

export default function ModelPerformance() {
  const [modelInfo, setModelInfo] = useState(null);
  const [metricsData, setMetricsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMetrics() {
      try {
        const [info, metrics] = await Promise.all([
          fetchModelInfo().catch(() => null),
          fetchMetrics().catch(() => null),
        ]);
        setModelInfo(info);
        setMetricsData(metrics);
      } catch (err) {
        console.error('Error fetching performance data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  const isAvailable = metricsData?.status === 'available';

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Model Evaluation & Benchmark</h1>
          <p className="text-sm text-slate-400">
            Empirical validation metrics across international RDD2022 baseline and local Pakistani transfer learning.
          </p>
        </div>
        <div>
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
              isAvailable
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            }`}
          >
            {isAvailable ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
            {isAvailable ? 'Metrics Computed' : 'Status: Unavailable (Phase 1 Ready)'}
          </span>
        </div>
      </div>

      {/* Model Spec Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <Cpu className="w-5 h-5 text-emerald-400" />
          Active Model Runtime Specification
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-2">
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-xs text-slate-500 block">Detector Architecture</span>
            <span className="text-sm font-bold text-white mt-0.5 block">
              {modelInfo?.model_name || 'YOLO26n / YOLO11n'}
            </span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-xs text-slate-500 block">Weights File Path</span>
            <span className="text-xs font-mono text-emerald-400 mt-1 block truncate">
              {modelInfo?.weights_path || 'artifacts/checkpoints/best_yolo.pt'}
            </span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-xs text-slate-500 block">Default Confidence</span>
            <span className="text-sm font-bold text-white mt-0.5 block">
              {modelInfo?.confidence_threshold ?? 0.25}
            </span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-xs text-slate-500 block">Weights Status</span>
            <span
              className={`text-sm font-semibold mt-0.5 block ${
                modelInfo?.weights_present ? 'text-emerald-400' : 'text-slate-400'
              }`}
            >
              {modelInfo?.weights_present ? 'Loaded & Active' : 'Pending Training (Phase 3)'}
            </span>
          </div>
        </div>
      </div>

      {/* Benchmark Matrix Status Notice */}
      {!isAvailable && (
        <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
            <BarChart3 className="w-6 h-6 text-slate-300" />
          </div>
          <h3 className="text-base font-bold text-white">Evaluation Metrics Not Yet Generated</h3>
          <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
            In accordance with the project specification, metrics are dynamically computed from training runs rather than fabricated with static placeholder numbers. After running Phases 2–5 training and evaluation scripts, this dashboard will visualize Precision, Recall, F1, mAP@0.5, and Domain Gap analyses.
          </p>
        </div>
      )}

      {/* Planned Experiment Structure */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-white">Planned Evaluation Experiments (Phases 3–5)</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <span className="text-xs font-mono text-emerald-400 uppercase">Experiment 1</span>
            <h4 className="text-sm font-bold text-white">International Baseline</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Multi-country training on Japan, India, Czech, Norway, and USA subsets of RDD2022 to establish global defect representation.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <span className="text-xs font-mono text-blue-400 uppercase">Experiment 2</span>
            <h4 className="text-sm font-bold text-white">Leave-One-Country-Out</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Cross-country generalization testing to quantify performance degradation due to geographical and asphalt variance.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <span className="text-xs font-mono text-amber-400 uppercase">Experiment 4</span>
            <h4 className="text-sm font-bold text-white">Pakistani Data Efficiency</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Transfer learning with 10%, 25%, 50%, and 100% Pakistani road data to determine the optimal annotation threshold.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
