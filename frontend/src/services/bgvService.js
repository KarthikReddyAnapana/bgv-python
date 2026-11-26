import axios from 'axios';

// Vite substitutes this at startup/build time; the fallback is the local development API.
export const API_ORIGIN = import.meta.env.VITE_API_BASE || 'http://localhost:8080';
export const API_BASE_URL = `${API_ORIGIN}/api/bgv-requests`;

const DEMO_PASSWORD = 'Password123!';
const ROLE_EMAIL = {
  PM: 'hr@demo.com',
  PMO_ADMIN: 'hr@demo.com',
  SUPER_ADMIN: 'admin@demo.com',
};

const api = axios.create();

api.interceptors.request.use((config) => {
  // Read per request so a newly obtained login token applies without recreating the Axios client.
  const token = localStorage.getItem('bgv_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/** Silently obtain JWT for legacy PS-number login (maps role → demo account). */
export async function ensureAuthToken(role) {
  const email = ROLE_EMAIL[role] || ROLE_EMAIL.PM;
  const res = await axios.post(`${API_ORIGIN}/api/auth/login`, {
    email,
    password: DEMO_PASSWORD,
  });
  const token = res.data?.data?.token;
  if (token) {
    localStorage.setItem('bgv_token', token);
  }
  return token;
}

export const bgvService = {
  ensureAuthToken,

  createRequest: (data) => api.post(API_BASE_URL, data),

  // PUT validates a complete request, so callers merge their edits with the existing record.
  updateRequest: (id, data) => api.put(`${API_BASE_URL}/${id}`, data),

  getRequest: (id) => api.get(`${API_BASE_URL}/${id}`),

  getAllRequests: () => api.get(API_BASE_URL),

  getRequestsByPsNumber: (psNumber) => api.get(`${API_BASE_URL}/ps/${psNumber}`),

  getHistoryByPsNumber: (psNumber) => api.get(`${API_BASE_URL}/history/ps/${psNumber}`),

  getHistoryByResourcePsNo: (resourcePsNo) => api.get(`${API_BASE_URL}/history/resource-ps/${resourcePsNo}`),

  getHistoryByCandidateId: (candidateId) => api.get(`${API_BASE_URL}/history/candidate/${candidateId}`),

  searchHistory: (searchTerm) => api.get(`${API_BASE_URL}/history/search/${searchTerm}`),

  getCountryGeoRegionMapping: () => api.get(`${API_BASE_URL}/config/country-georegion-mapping`),
};
