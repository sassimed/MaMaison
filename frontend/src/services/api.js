import axios from 'axios';
import apiCache, { CacheTTL } from './cache';
import errorLogger from './errorLogger';

// Use relative URL in production, REACT_APP_BACKEND_URL in development
// This allows the API to work with any domain (custom or Emergent)
const getApiUrl = () => {
  // If we're in production (no localhost), use relative URL
  if (typeof window !== 'undefined' && !window.location.hostname.includes('localhost')) {
    return '/api';
  }
  // In development, use the environment variable or fallback to relative
  return process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';
};

const API_URL = getApiUrl();

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh and error logging
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Log API errors (except 401 which are handled separately)
    if (error.response?.status !== 401) {
      errorLogger.logApiError(error, originalRequest);
    }

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`/api/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Cached GET request - for read-only endpoints
 * @param {string} url - API endpoint
 * @param {object} params - Query parameters
 * @param {number} ttl - Cache TTL in milliseconds (default 5 minutes)
 */
api.getCached = async (url, params = {}, ttl = CacheTTL.MEDIUM) => {
  const cacheKey = apiCache.generateKey(url, params);
  
  // Check cache first
  const cached = apiCache.get(cacheKey);
  if (cached) {
    return { data: cached, fromCache: true };
  }
  
  // Fetch from API
  const response = await api.get(url, { params });
  
  // Cache the response
  apiCache.set(cacheKey, response.data, ttl);
  
  return { ...response, fromCache: false };
};

/**
 * Clear cache for specific patterns
 */
api.clearCache = (pattern) => {
  if (pattern) {
    apiCache.clearPattern(pattern);
  } else {
    apiCache.clearAll();
  }
};

/**
 * Get cache statistics
 */
api.getCacheStats = () => apiCache.getStats();

// Export cache utilities
export { apiCache, CacheTTL };

export default api;
