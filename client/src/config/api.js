// API Configuration
// Update this URL to your deployed backend URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const API_ENDPOINTS = {
  UPLOAD_FILE: `${API_BASE_URL}/upload`,
  GET_HEADERS: `${API_BASE_URL}/headers`,
  GENERATE_STAKEHOLDER_REPORT: `${API_BASE_URL}/api/generate-stakeholder-report`,
  GENERATE_REPORT: `${API_BASE_URL}/generate-report`,
  GENERATE_CHARTS: `${API_BASE_URL}/generate-charts`,
  GET_SUGGESTIONS: `${API_BASE_URL}/get-suggestions`,
  CLEAR_CACHE: `${API_BASE_URL}/clear-chart-cache`,
  HEALTH: `${API_BASE_URL}/health`,
};

export default API_BASE_URL;
