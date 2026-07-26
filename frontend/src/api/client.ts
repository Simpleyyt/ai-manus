// Backend API client configuration
import axios, { AxiosError } from 'axios';
import { clearStoredTokens, getStoredToken, getStoredRefreshToken, storeToken, storeRefreshToken } from './auth';

// API configuration
export const API_CONFIG = {
  host: import.meta.env.VITE_API_URL || '',
  version: 'v1',
  timeout: 30000, // Request timeout in milliseconds
};

// Complete API base URL
export const BASE_URL = API_CONFIG.host 
  ? `${API_CONFIG.host}/api/${API_CONFIG.version}` 
  : `/api/${API_CONFIG.version}`;

// Login page route name/path
const LOGIN_ROUTE = '/login';

// Unified response format
export interface ApiResponse<T> {
  code: number;
  msg: string;
  data: T;
}

// Error format
export interface ApiError {
  code: number;
  message: string;
  details?: unknown;
}

// Create axios instance
export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: API_CONFIG.timeout,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
});

// Request interceptor, add authentication token
apiClient.interceptors.request.use(
  (config) => {
    const token = getStoredToken();
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (!config.headers['X-Requested-With']) {
      config.headers['X-Requested-With'] = 'XMLHttpRequest';
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Track if we're currently refreshing token to prevent multiple concurrent requests
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  
  failedQueue = [];
};

/**
 * Redirect to the login page with a full page load.
 * Intentionally avoids importing the router to keep the API layer
 * free of dependencies on the app entry point.
 */
const redirectToLogin = () => {
  if (window.location.pathname === LOGIN_ROUTE) {
    return; // Already on login page, no need to redirect
  }

  setTimeout(() => {
    window.location.href = LOGIN_ROUTE;
  }, 100);
};

/**
 * Common token refresh logic used by both axios interceptor and SSE connections
 */
const refreshAuthToken = async (): Promise<string | null> => {
  if (isRefreshing) {
    // If already refreshing, queue this request
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject });
    });
  }

  isRefreshing = true;
  const refreshToken = getStoredRefreshToken();

  try {
    // Cookie and/or body refresh_token (session id)
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken || undefined,
    }, {
      __isRefreshRequest: true
    } as any);
    
    if (response.data && response.data.data) {
      const newAccessToken = response.data.data.access_token;
      storeToken(newAccessToken);
      const newRefresh = response.data.data.refresh_token;
      if (newRefresh) {
        storeRefreshToken(newRefresh);
      }
      
      apiClient.defaults.headers.Authorization = `Bearer ${newAccessToken}`;
      processQueue(null, newAccessToken);
      return newAccessToken;
    } else {
      throw new Error('Invalid refresh response');
    }
  } catch (refreshError) {
    // Refresh token failed, clear tokens and redirect to login
    clearStoredTokens();
    delete apiClient.defaults.headers.Authorization;
    
    processQueue(refreshError, null);
    
    // Emit logout event
    window.dispatchEvent(new CustomEvent('auth:logout'));
    
    // Redirect to login page
    redirectToLogin();
    
    throw refreshError;
  } finally {
    isRefreshing = false;
  }
};

// Response interceptor, unified error handling and token refresh
apiClient.interceptors.response.use(
  (response) => {
    // Check backend response format
    if (response.data && typeof response.data.code === 'number') {
      // If it's a business logic error (code not 0), convert to error handling
      if (response.data.code !== 0) {
        const apiError: ApiError = {
          code: response.data.code,
          message: response.data.msg || 'Unknown error',
          details: response.data
        };
        return Promise.reject(apiError);
      }
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    
    // Skip retry logic for refresh requests to prevent infinite loops
    if (originalRequest.__isRefreshRequest) {
      const apiError: ApiError = {
        code: error.response?.status || 500,
        message: 'Token refresh failed',
        details: error.response?.data
      };
      console.error('Refresh token request failed:', apiError);
      return Promise.reject(apiError);
    }
    
    // Handle 401 Unauthorized errors with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const newAccessToken = await refreshAuthToken();
        if (newAccessToken) {
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Token refresh failed, error already handled in refreshAuthToken
        console.error('Token refresh failed:', refreshError);
      }
    }

    const apiError: ApiError = {
      code: 500,
      message: 'Request failed',
    };

    if (error.response) {
      const status = error.response.status;
      apiError.code = status;
      
      // Try to extract detailed error information from response content
      if (error.response.data && typeof error.response.data === 'object') {
        const data = error.response.data as any;
        if (data.code && data.msg) {
          apiError.code = data.code;
          apiError.message = data.msg;
        } else {
          apiError.message = data.message || error.response.statusText || 'Request failed';
        }
        apiError.details = data;
      } else {
        apiError.message = error.response.statusText || 'Request failed';
      }
    } else if (error.request) {
      apiError.code = 503;
      apiError.message = 'Network error, please check your connection';
    }

    console.error('API Error:', apiError);
    return Promise.reject(apiError);
  }
);
 