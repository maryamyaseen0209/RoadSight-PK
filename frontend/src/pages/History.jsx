import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Clock, Database, Eye, FileText, RefreshCw, Search } from 'lucide-react';
import { fetchHistory } from '../services/api';

export default function History() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await fetchHistory(50, 0);
      setRuns(data || []);
    } catch (err) {
      console.error('Failed to load detection history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const filteredRuns = runs.filter(
    (r) =>
      r.image_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.model_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Inspection History</h1>
          <p className="text-sm text-slate-400">
            Chronological audit log of all defect detection runs stored in SQLite.
          </p>
        </div>
        <button
          onClick={loadHistory}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors w-fit"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh History
        </button>
      </div>

      {/* Filter / Search Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 flex items-center gap-3">
        <Search className="w-4 h-4 text-slate-400 ml-2" />
        <input
          type="text"
          placeholder="Filter by image name, model, or run ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none w-full"
        />
      </div>

      {/* History Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">Loading historical inspection runs...</div>
        ) : filteredRuns.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Database className="w-8 h-8 text-slate-500 mx-auto" />
            <p className="text-sm font-semibold text-slate-300">No detection runs recorded yet</p>
            <p className="text-xs text-slate-500">
              Run an image inspection on the Analyze page to populate this SQLite audit table.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-950/70 text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Image / Run ID</th>
                  <th scope="col" className="px-6 py-3.5">Model</th>
                  <th scope="col" className="px-6 py-3.5">Defects</th>
                  <th scope="col" className="px-6 py-3.5">Latency</th>
                  <th scope="col" className="px-6 py-3.5">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-white truncate max-w-xs">{run.image_name}</div>
                      <div className="text-[11px] font-mono text-slate-500 truncate max-w-xs">{run.id}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-xs font-medium px-2.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                        {run.model_name}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                          run.total_detections > 0
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {run.total_detections} defects
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-blue-400">
                      {run.inference_time_ms} ms
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {new Date(run.created_at).toLocaleString()}
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
