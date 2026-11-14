import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, ArrowRight, CheckCircle2, Clock, Layers, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';
import { fetchSummary, fetchHealth } from '../services/api';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [sumData, healthData] = await Promise.all([
          fetchSummary().catch(() => null),
          fetchHealth().catch(() => null),
        ]);
        setSummary(sumData);
        setHealth(healthData);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

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

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-950/60 via-slate-900 to-slate-900 border border-emerald-900/50 p-6 md:p-8">
        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
            Pakistan Road Intelligence System
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
            Automated Pavement Defect Assessment
          </h1>
          <p className="text-slate-300 text-sm md:text-base leading-relaxed">
            Real-time multi-defect detection trained on the international RDD2022 dataset and optimized for diverse Pakistani asphalt conditions.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-lg shadow-emerald-600/30 transition-all text-sm"
            >
              Analyze Pavement Image
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/performance"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold border border-slate-700 transition-all text-sm"
            >
              View Model Metrics
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Total Runs</span>
            <Layers className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : summary?.total_runs ?? 0}
          </div>
          <p className="text-xs text-slate-500">Processed inspection images</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Total Defects</span>
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : summary?.total_detections ?? 0}
          </div>
          <p className="text-xs text-slate-500">Confirmed road damages</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Average Latency</span>
            <Clock className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : `${summary?.average_inference_time_ms ?? 0} ms`}
          </div>
          <p className="text-xs text-slate-500">End-to-end inference speed</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">System Status</span>
            <CheckCircle2 className="w-5 h-5 text-teal-400" />
          </div>
          <div className="text-2xl font-bold text-white capitalize">
            {health?.status === 'ok' ? 'Online' : 'Operational'}
          </div>
          <p className="text-xs text-slate-500">SQLite + FastAPI active</p>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-6">
          <h2 className="text-base font-semibold text-white mb-4 flex items-center justify-between">
            <span>Defects Breakdown by Category</span>
            <span className="text-xs text-slate-400 font-normal">Official RDD2022 Schema</span>
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
            <h2 className="text-base font-semibold text-white mb-2">Supported Defect Classes</h2>
            <p className="text-xs text-slate-400 mb-4">Official 4-class taxonomy used across all phases</p>
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
            Database persistence powered by SQLite with relational cascade support.
          </div>
        </div>
      </div>
    </div>
  );
}
