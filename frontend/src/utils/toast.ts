/**
 * Toast service
 * Provide global Toast message notification functionality
 */
import { eventBus } from './eventBus'

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
  
  eventBus.emit('ui:toast', {
    message: config.message,
    type: config.type || 'info',
    duration: config.duration === undefined ? 3000 : config.duration,
  });
}

// Convenient methods
export function showErrorToast(message: string, duration?: number): void {
  showToast({ message, type: 'error', duration });
}

export function showInfoToast(message: string, duration?: number): void {
  showToast({ message, type: 'info', duration });
}

export function showSuccessToast(message: string, duration?: number): void {
  showToast({ message, type: 'success', duration });
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
