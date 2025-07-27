// Backend API client configuration
import axios, { AxiosError } from 'axios';
import { fetchEventSource, EventSourceMessage } from '@microsoft/fetch-event-source';
import { router } from '@/main';
import { clearStoredTokens, getStoredToken, getStoredRefreshToken, storeToken } from './auth';

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
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor, add authentication token
apiClient.interceptors.request.use(
  (config) => {
    // Add authentication token if available
    const token = getStoredToken();
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
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
 * Redirect to login page using Vue Router
 */
const redirectToLogin = () => {
  // Check if we're already on the login page
  if (window.location.pathname === LOGIN_ROUTE || 
      router.currentRoute.value.path === LOGIN_ROUTE) {
    return; // Already on login page, no need to redirect
  }

  // Use Vue Router to navigate to login page
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
  
  if (!refreshToken) {
    // No refresh token available, clear auth and redirect to login
    clearStoredTokens();
    delete apiClient.defaults.headers.Authorization;
    window.dispatchEvent(new CustomEvent('auth:logout'));
    redirectToLogin();
    isRefreshing = false;
    throw new Error('No refresh token available');
  }

  try {
    // Attempt to refresh token
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken
    }, {
      // Add special marker to prevent interceptor from retrying this request
      __isRefreshRequest: true
    } as any);
    
    if (response.data && response.data.data) {
      const newAccessToken = response.data.data.access_token;
      storeToken(newAccessToken);
      
      // Update default headers
      apiClient.defaults.headers.Authorization = `Bearer ${newAccessToken}`;
      
      // Process queued requests
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

export interface SSECallbacks<T = any> {
  onOpen?: () => void;
  onMessage?: (event: { event: string; data: T }) => void;
  onClose?: () => void;
  onError?: (error: Error) => void;
}

export interface SSEOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: any;
  headers?: Record<string, string>;
}

/**
 * Handle SSE authentication errors and attempt token refresh
 */
const handleSSEAuthError = async <T = any>(
  _error: Error,
  _endpoint: string,
  _options: SSEOptions,
  callbacks: SSECallbacks<T>
): Promise<boolean> => {
  try {
    const newAccessToken = await refreshAuthToken();
    if (newAccessToken) {
      // Emit event for token refresh success
      window.dispatchEvent(new CustomEvent('auth:token-refreshed'));
      console.log('Token refreshed for SSE connection, will retry connection');
      return true; // Indicate successful refresh
    }
    return false; // No new token obtained
  } catch (refreshError) {
    // Token refresh failed, error already handled in refreshAuthToken
    console.error('SSE token refresh failed:', refreshError);
    if (callbacks.onError) {
      callbacks.onError(refreshError as Error);
    }
    return false; // Indicate failed refresh
  }
};

/**
 * Generic SSE connection function
 * @param endpoint - API endpoint (relative to BASE_URL)
 * @param options - Request options
 * @param callbacks - Event callbacks
 * @returns Function to cancel the SSE connection
 */
export const createSSEConnection = async <T = any>(
  endpoint: string,
  options: SSEOptions = {},
  callbacks: SSECallbacks<T> = {}
): Promise<() => void> => {
  const { onOpen, onMessage, onClose, onError } = callbacks;
  const { 
    method = 'GET', 
    body, 
    headers = {}
  } = options;
  
  // Create AbortController for cancellation
  const abortController = new AbortController();
  
  const apiUrl = `${BASE_URL}${endpoint}`;
  
  // Add authentication headers
  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };
  
  // Add authentication token if available
  const token = getStoredToken();
  if (token && !requestHeaders.Authorization) {
    requestHeaders.Authorization = `Bearer ${token}`;
  }
  
  // 创建SSE连接
  const createConnection = async (): Promise<void> => {
    return new Promise((_resolve, reject) => {
      if (abortController.signal.aborted) {
        reject(new Error('Connection aborted'));
        return;
      }

      const ssePromise = fetchEventSource(apiUrl, {
        method,
        headers: requestHeaders,
        openWhenHidden: true,
        body: body ? JSON.stringify(body) : undefined,
        signal: abortController.signal,
        async onopen(response) {
          // Check for authentication errors in the initial response
          if (response.status === 401) {
            const authError = new Error('Unauthorized');
            const refreshSuccess = await handleSSEAuthError(authError, endpoint, options, callbacks);
            
            if (refreshSuccess) {
              // Update authorization header with new token
              const newToken = getStoredToken();
              if (newToken) {
                requestHeaders.Authorization = `Bearer ${newToken}`;
                // Retry connection with new token
                setTimeout(() => createConnection().catch(console.error), 1000);
              }
            }
            return;
          }
          
          // Check for other error status codes
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          
          if (onOpen) {
            onOpen();
          }
        },
        onmessage(event: EventSourceMessage) {
          if (event.event && event.event.trim() !== '') {
            if (onMessage) {
              onMessage({
                event: event.event,
                data: JSON.parse(event.data) as T
              });
            }
          }
        },
        onclose() {
          if (onClose) {
            onClose();
          }
        },
        onerror(err: any) {
          const error = err instanceof Error ? err : new Error(String(err));
          console.error('EventSource error:', error);
          
          if (onError) {
            onError(error);
          }
          reject(error);
        },
      });

      ssePromise.catch(reject);
    });
  };

  createConnection().catch((error) => {
    if (!abortController.signal.aborted) {
      console.error('SSE connection failed:', error);
    }
  });

  return () => {
    abortController.abort();
  };
}; 