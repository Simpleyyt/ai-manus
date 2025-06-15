// Backend API client configuration
import axios, { AxiosError } from 'axios';
import { fetchEventSource, EventSourceMessage } from '@microsoft/fetch-event-source';

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

// Request interceptor, can add authentication token etc.
apiClient.interceptors.request.use(
  (config) => {
    // Authentication token can be added here
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor, unified error handling
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
  (error: AxiosError) => {
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
  // Retry configuration
  retryCount?: number; // Maximum retry attempts, default is 3
  retryDelay?: number; // Retry delay in milliseconds, default is 1000
  shouldRetry?: (error: Error) => boolean; // Function to determine if should retry on error, default always returns true
}

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
    headers = {},
    retryCount = 3,
    retryDelay = 1000,
    shouldRetry = () => true
  } = options;
  
  // Create AbortController for cancellation
  const abortController = new AbortController();
  let currentAttempt = 0;
  
  const apiUrl = `${BASE_URL}${endpoint}`;
  
  // 创建重试函数
  const createConnection = async (): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (abortController.signal.aborted) {
        reject(new Error('Connection aborted'));
        return;
      }

      const ssePromise = fetchEventSource(apiUrl, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        openWhenHidden: true,
        body: body ? JSON.stringify(body) : undefined,
        signal: abortController.signal,
        async onopen() {
          currentAttempt = 0; // 连接成功，重置重试计数
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
          reject(error);
        },
      });

      ssePromise.catch(reject);
    });
  };

  // 带重试的连接函数
  const connectWithRetry = async (): Promise<void> => {
    try {
      await createConnection();
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      
      // 检查是否被取消
      if (abortController.signal.aborted) {
        return;
      }

      // 检查是否应该重试
      if (currentAttempt < retryCount && shouldRetry(err)) {
        currentAttempt++;
        console.log(`SSE connection failed, retrying (${currentAttempt}/${retryCount})...`);
        
        // 等待重试延迟
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        
        // 递归重试
        return connectWithRetry();
      } else {
        // 重试耗尽或不应该重试，触发错误回调
        if (onError) {
          onError(err);
        }
        throw err;
      }
    }
  };

  // 开始连接
  connectWithRetry().catch((error) => {
    // 只处理非取消错误
    if (!abortController.signal.aborted) {
      console.error('SSE connection failed after retries:', error);
    }
  });

  // 返回取消函数
  return () => {
    abortController.abort();
  };
}; 