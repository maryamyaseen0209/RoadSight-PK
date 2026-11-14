import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Cpu,
  Layers,
  TrendingUp,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';
import { fetchSummary, fetchModelInfo, fetchMetrics } from '../services/api';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [sumData, mInfo, mMetrics] = await Promise.all([
          fetchSummary().catch(() => null),
          fetchModelInfo().catch(() => null),
          fetchMetrics().catch(() => null),
        ]);
        setSummary(sumData);
        setModelInfo(mInfo);
        setMetrics(mMetrics);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  // Compute live mAP50 from real metrics
  const latestMap50 =
    metrics?.master_summary?.YOLO26n_Baseline?.mAP50 ??
    metrics?.exp1_baseline?.yolo?.mAP50 ??
    (metrics?.recorded_experiments?.[0]?.map50 ?? null);

  const chartData = summary?.defect_counts_by_class
    ? Object.entries(summary.defect_counts_by_class).map(([name, count]) => ({
        name: name.split(' ')[0],
        fullName: name,
        count: count,
      }))
    : [
        { name: 'Longitudinal', fullName: 'Longitudinal Crack [D00]', count: 0 },
        { name: 'Transverse', fullName: 'Transverse Crack [D10]', count: 0 },
        { name: 'Alligator', fullName: 'Alligator Crack [D20]', count: 0 },
        { name: 'Pothole', fullName: 'Pothole [D40]', count: 0 },
      ];

  const recentRuns = summary?.recent_runs || [];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-slate-900 border border-emerald-900/50 p-6 md:p-8">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
            Pakistan Road Intelligence System • Live Backend Connected
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
            Automated Pavement Defect Assessment
          </h1>
          <p className="text-slate-300 text-sm md:text-base leading-relaxed">
            Real-time defect detection benchmarked on international RDD2022 data and adapted for Pakistani road conditions. Powered by FastAPI, SQLite, and Ultralytics YOLO.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-lg shadow-emerald-600/30 transition-all text-sm"
            >
              Analyze Road Image
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/performance"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold border border-slate-700 transition-all text-sm"
            >
              Research Metrics Dashboard
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Total Images Analyzed</span>
            <Layers className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : summary?.total_images_analyzed ?? 0}
          </div>
          <p className="text-xs text-slate-500">Persisted in SQLite database</p>
        </div>

        {/* KPI 2 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Total Detections</span>
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : summary?.total_damage_detections ?? 0}
          </div>
          <p className="text-xs text-slate-500">Confirmed road distress features</p>
        </div>

        {/* KPI 3 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Active Model</span>
            <Cpu className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-xl font-bold text-white truncate">
            {loading ? '...' : modelInfo?.model_name || 'YOLO26n'}
          </div>
          <p className="text-xs text-slate-500 truncate">
            {modelInfo?.weights_present ? 'Weights Loaded & Active' : 'Fallback Pretrained'}
          </p>
        </div>

        {/* KPI 4 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Benchmark mAP@0.5</span>
            <TrendingUp className="w-5 h-5 text-teal-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading
              ? '...'
              : latestMap50 !== null
              ? `${(latestMap50 * 100).toFixed(1)}%`
              : 'Computed in Colab'}
          </div>
          <p className="text-xs text-slate-500">Colab Experiment 1 & 4 Benchmark</p>
        </div>
      </div>

      {/* Analytics Charts & Class Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-6">
          <h2 className="text-base font-semibold text-white mb-4 flex items-center justify-between">
            <span>Detections by Pavement Defect Category</span>
            <span className="text-xs text-slate-400 font-normal">Official 4-Class Taxonomy</span>
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#cbd5e1' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-white mb-2">Defect Taxonomy (RDD2022)</h2>
            <p className="text-xs text-slate-400 mb-4">Official 4 damage codes evaluated across phases</p>
            <div className="space-y-3">
              {[
                { code: 'D00', name: 'Longitudinal Crack', color: 'bg-blue-500' },
                { code: 'D10', name: 'Transverse Crack', color: 'bg-emerald-500' },
                { code: 'D20', name: 'Alligator Crack', color: 'bg-amber-500' },
                { code: 'D40', name: 'Pothole', color: 'bg-red-500' },
              ].map((item) => (
                <div key={item.code} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/50 border border-slate-800">
                  <div className="flex items-center gap-2.5">
                    <span className={`w-3 h-3 rounded-full ${item.color}`}></span>
                    <span className="text-xs font-medium text-slate-200">{item.name}</span>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-700/60 text-slate-300">
                    {item.code}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-800 text-xs text-slate-500">
            Real metrics loaded from <code className="text-slate-400">experiments/metrics/</code>
          </div>
        </div>
      </div>

      {/* Recent Inspection Runs Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Recently Analyzed Road Images</h2>
            <p className="text-xs text-slate-400">Inspection executions recorded in SQLite</p>
          </div>
          <Link
            to="/history"
            className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
          >
            View Full History
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentRuns.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            No inspection runs recorded yet. Upload an image in the Analyze page.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-950/70 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Image Name</th>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3">Defects Detected</th>
                  <th className="px-4 py-3">Latency</th>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recentRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 font-semibold text-white max-w-xs truncate">
                      {run.image_name}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-medium px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                        {run.model_name}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                          run.total_detections > 0
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {run.total_detections} defects
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-blue-400">
                      {run.inference_time_ms} ms
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        to={`/results/${run.id}`}
                        className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium"
                      >
                        View Details
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
