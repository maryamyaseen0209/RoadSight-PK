import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 45000,
});

export const fetchHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const fetchModelInfo = async () => {
  const res = await api.get('/model');
  return res.data;
};

export const fetchSummary = async () => {
  const res = await api.get('/summary');
  return res.data;
};

export const fetchMetrics = async () => {
  const res = await api.get('/metrics');
  return res.data;
};

export const runPrediction = async (file, confidenceThreshold = 0.25, modelName = 'YOLO') => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post(
    `/predict?confidence_threshold=${confidenceThreshold}&model_name=${encodeURIComponent(modelName)}`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  );
  return res.data;
};

export const fetchHistory = async (limit = 20, offset = 0) => {
  const res = await api.get(`/history?limit=${limit}&offset=${offset}`);
  return res.data;
};

export const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

export const resolveImageUrl = (pathOrObj) => {
  if (!pathOrObj) return '';
  const raw = typeof pathOrObj === 'string'
    ? pathOrObj
    : (pathOrObj.output_image_url || pathOrObj.annotated_image_path || pathOrObj.image_url || pathOrObj.image_path || pathOrObj.filename || '');
  if (!raw) return '';
  if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('data:') || raw.startsWith('blob:')) {
    return raw;
  }
  const clean = raw.replace(/\\/g, '/').replace(/^\/+/, '');
  return `${API_BASE}/${clean}`;
};

export const fetchRunDetail = async (runId) => {
  const res = await api.get(`/history/${runId}`);
  return res.data;
};

export const deleteRun = async (runId) => {
  const res = await api.delete(`/history/${runId}`);
  return res.data;
};

export default api;
