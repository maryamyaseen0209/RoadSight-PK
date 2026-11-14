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

export const fetchRunDetail = async (runId) => {
  const res = await api.get(`/history/${runId}`);
  return res.data;
};

export const deleteRun = async (runId) => {
  const res = await api.delete(`/history/${runId}`);
  return res.data;
};

export default api;
