import { useToast } from 'vue-toastification';

const toast = useToast();

/**
 * Toast service
 * Provide global Toast message notification functionality
 */

type ToastType = 'error' | 'info' | 'success';

interface ToastOptions {
  message: string;
  type?: ToastType;
  duration?: number;
}

/**
 * Show Toast message
 * @param options - Toast configuration or message string
 */
export function showToast(options: ToastOptions | string): void {
  let config: ToastOptions;
  
  if (typeof options === 'string') {
    config = { message: options };
  } else {
    config = options;
  }
  
  // Default configuration
  const detail = {
    message: config.message,
    type: config.type || 'info',
    duration: config.duration === undefined ? 3000 : config.duration
  };
  
  // Create custom event
  const event = new CustomEvent('toast', { detail });
  
  // Trigger event
  window.dispatchEvent(event);
}

// Convenient methods
export function showErrorToast(message: string) {
  toast.error(message);
}

export function showSuccessToast(message: string) {
  toast.success(message);
}

export function showInfoToast(message: string) {
  toast.info(message);
}

export function showWarningToast(message: string) {
  toast.warning(message);
}

// To support non-Vue page calls, add to global window object
declare global {
  interface Window {
    toast: {
      show: typeof showToast;
      error: typeof showErrorToast;
      info: typeof showInfoToast;
      success: typeof showSuccessToast;
    };
  }
}

// Mount to window object
if (typeof window !== 'undefined') {
  window.toast = {
    show: showToast,
    error: showErrorToast,
    info: showInfoToast,
    success: showSuccessToast
  };
} 