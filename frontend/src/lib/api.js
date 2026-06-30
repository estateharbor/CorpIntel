import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;
export const V1 = `${BACKEND_URL}/api/v1`;

const api = axios.create({ baseURL: V1, withCredentials: true });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ci_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;

// Raw client for /api (non-v1) endpoints like health
const metaClient = axios.create({ baseURL: API_BASE, withCredentials: true });

// ---------------- Endpoint helpers ----------------
export const getHealth = () => metaClient.get("/health").then((r) => r.data);

export const getCompanies = (params) =>
  api.get("/companies", { params }).then((r) => r.data);
export const getCompany = (cin) => api.get(`/companies/${cin}`).then((r) => r.data);
export const getDirectors = (cin) => api.get(`/companies/${cin}/directors`).then((r) => r.data);
export const getCharges = (cin) => api.get(`/companies/${cin}/charges`).then((r) => r.data);
export const getFilings = (cin) => api.get(`/companies/${cin}/filings`).then((r) => r.data);
export const getContact = (cin) => api.get(`/companies/${cin}/contact`).then((r) => r.data);
export const getSimilar = (cin, limit = 6) =>
  api.get(`/companies/${cin}/similar`, { params: { limit } }).then((r) => r.data);

export const getSummary = (city) => api.get("/analytics/summary", { params: { city } }).then((r) => r.data);
export const getTrends = (city, months = 24) =>
  api.get("/analytics/trends", { params: { city, months } }).then((r) => r.data);
export const getSectors = (city, limit = 20) =>
  api.get("/analytics/sectors", { params: { city, limit } }).then((r) => r.data);
export const getCapital = (city) => api.get("/analytics/capital", { params: { city } }).then((r) => r.data);
export const getHeatmap = (city) => api.get("/analytics/heatmap", { params: { city } }).then((r) => r.data);

export const quickSearch = (q, limit = 8) =>
  api.get("/search", { params: { q, limit } }).then((r) => r.data);
export const advancedSearch = (body) => api.post("/search/advanced", body).then((r) => r.data);
export const saveSearch = (body) => api.post("/search/save", body).then((r) => r.data);
export const listSaved = () => api.get("/search/saved").then((r) => r.data);
export const deleteSaved = (id) => api.delete(`/search/saved/${id}`).then((r) => r.data);

export const createAlert = (body) => api.post("/alerts", body).then((r) => r.data);
export const listAlerts = () => api.get("/alerts").then((r) => r.data);
export const toggleAlert = (id) => api.patch(`/alerts/${id}/toggle`).then((r) => r.data);
export const deleteAlert = (id) => api.delete(`/alerts/${id}`).then((r) => r.data);
export const alertLog = () => api.get("/alerts/log").then((r) => r.data);

export const getAdminStats = () => api.get("/admin/stats").then((r) => r.data);
export const getEnrichmentProgress = () =>
  api.get("/admin/enrichment-progress").then((r) => r.data);
export const triggerSeed = () => api.post("/admin/ingest/seed").then((r) => r.data);

export const getPlans = () => api.get("/payments/plans").then((r) => r.data);
export const createCheckout = (plan_id) =>
  api.post("/payments/checkout", { plan_id, origin_url: window.location.origin }).then((r) => r.data);
export const checkoutStatus = (sessionId) =>
  api.get(`/payments/status/${sessionId}`).then((r) => r.data);

export const regenerateApiKey = () => api.post("/auth/api-key").then((r) => r.data);

export async function downloadExport(format, body) {
  const res = await api.post(`/export/${format}`, body, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const a = document.createElement("a");
  a.href = url;
  const ext = format === "excel" ? "xlsx" : format;
  a.download = `corpintel_export.${ext}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
