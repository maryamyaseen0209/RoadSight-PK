import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  Clock,
  Database,
  Download,
  Eye,
  FileCode,
  FileSpreadsheet,
  RefreshCw,
  Search,
  Trash2,
  AlertTriangle,
} from 'lucide-react';
import { fetchHistory, deleteRun, fetchRunDetail } from '../services/api';

export default function History() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [deletingId, setDeletingId] = useState(null);

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

  const handleDelete = async (runId) => {
    if (!window.confirm(`Are you sure you want to delete inspection record ${runId}?`)) {
      return;
    }
    setDeletingId(runId);
    try {
      await deleteRun(runId);
      setRuns((prev) => prev.filter((r) => r.id !== runId));
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Failed to delete inspection run from database.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleExportJSON = async (runId) => {
    try {
      const detail = await fetchRunDetail(runId);
      const blob = new Blob([JSON.stringify(detail, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `detection_${runId}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export detection JSON.');
    }
  };

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
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Inspection History</h1>
          <p className="text-sm text-slate-400 mt-1">
            Chronological audit log of road damage inspection runs persisted in SQLite.
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
          placeholder="Filter by image name, model architecture, or run ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none w-full"
        />
      </div>

      {/* History Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
        {loading ? (
          <div className="p-16 text-center text-slate-400 text-sm">Loading historical inspection runs...</div>
        ) : filteredRuns.length === 0 ? (
          <div className="p-16 text-center space-y-3">
            <Database className="w-10 h-10 text-slate-600 mx-auto" />
            <p className="text-base font-semibold text-slate-300">No detection runs recorded yet</p>
            <p className="text-xs text-slate-500">
              Run an image inspection on the Analyze page to populate this SQLite audit table.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-950/70 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-5 py-4">Preview</th>
                  <th className="px-5 py-4">Image / Run ID</th>
                  <th className="px-5 py-4">Model</th>
                  <th className="px-5 py-4">Defects</th>
                  <th className="px-5 py-4">Latency</th>
                  <th className="px-5 py-4">Timestamp</th>
                  <th className="px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-slate-800/30 transition-colors">
                    {/* Thumbnail */}
                    <td className="px-5 py-3">
                      <div className="w-14 h-14 rounded-lg overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center">
                        <img
                          src={run.output_image_url || run.image_url}
                          alt={run.image_name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      </div>
                    </td>

                    {/* Image Name / ID */}
                    <td className="px-5 py-3">
                      <div className="font-semibold text-white truncate max-w-xs">{run.image_name}</div>
                      <div className="text-[11px] font-mono text-slate-500 truncate max-w-xs">{run.id}</div>
                    </td>

                    {/* Model */}
                    <td className="px-5 py-3">
                      <span className="text-xs font-medium px-2.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                        {run.model_name}
                      </span>
                    </td>

                    {/* Total Defects */}
                    <td className="px-5 py-3">
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

                    {/* Latency */}
                    <td className="px-5 py-3 font-mono text-xs text-blue-400">
                      {run.inference_time_ms} ms
                    </td>

                    {/* Timestamp */}
                    <td className="px-5 py-3 text-xs text-slate-400">
                      {new Date(run.created_at).toLocaleString()}
                    </td>

                    {/* Actions */}
                    <td className="px-5 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/results/${run.id}`}
                          title="View Details"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={() => handleExportJSON(run.id)}
                          title="Export JSON"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-blue-400 border border-slate-700 transition-colors"
                        >
                          <FileCode className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(run.id)}
                          disabled={deletingId === run.id}
                          title="Delete Record"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-500/20 text-red-400 border border-slate-700 hover:border-red-500/30 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
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
