/**
 * Error Logging Service
 * Captures and sends errors to backend for monitoring
 */

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Get session info
const getSessionId = () => sessionStorage.getItem('analytics_session_id') || 'unknown';
const getUserId = () => localStorage.getItem('analytics_user_id') || null;

/**
 * Log an error to the backend
 */
const logError = async (errorData) => {
  try {
    await fetch(`${API_URL}/api/logs/error`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...errorData,
        session_id: getSessionId(),
        user_id: getUserId(),
        user_agent: navigator.userAgent,
        url: window.location.href
      })
    });
  } catch (e) {
    // Silently fail - don't create infinite loops
    console.warn('[ErrorLogger] Failed to log error:', e);
  }
};

/**
 * Initialize global error handlers
 */
const initErrorHandlers = () => {
  // Handle uncaught JavaScript errors
  window.addEventListener('error', (event) => {
    logError({
      error_type: 'js_error',
      message: event.message || 'Unknown error',
      stack_trace: event.error?.stack || null,
      metadata: {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      }
    });
  });

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    const message = event.reason?.message || event.reason || 'Unhandled Promise Rejection';
    logError({
      error_type: 'promise_rejection',
      message: String(message),
      stack_trace: event.reason?.stack || null
    });
  });

  // Override console.error to capture logged errors
  const originalConsoleError = console.error;
  console.error = (...args) => {
    originalConsoleError.apply(console, args);
    
    // Don't log our own error logging failures
    const message = args.map(a => String(a)).join(' ');
    if (!message.includes('[ErrorLogger]')) {
      logError({
        error_type: 'console_error',
        message: message.slice(0, 1000)
      });
    }
  };
};

/**
 * Log API errors (call from axios interceptor)
 */
const logApiError = (error, config) => {
  const status = error.response?.status || 0;
  const message = error.response?.data?.detail || error.message || 'API Error';
  
  logError({
    error_type: 'api_error',
    message: `${status} - ${message}`,
    metadata: {
      status_code: status,
      endpoint: config?.url,
      method: config?.method?.toUpperCase(),
      response_data: error.response?.data
    }
  });
};

/**
 * Log custom errors
 */
const logCustomError = (type, message, metadata = {}) => {
  logError({
    error_type: type,
    message,
    metadata
  });
};

/**
 * Log component errors (for React Error Boundaries)
 */
const logComponentError = (error, errorInfo) => {
  logError({
    error_type: 'react_error',
    message: error.message || 'React Component Error',
    stack_trace: error.stack,
    metadata: {
      componentStack: errorInfo?.componentStack
    }
  });
};

const errorLogger = {
  init: initErrorHandlers,
  logError,
  logApiError,
  logCustomError,
  logComponentError
};

export default errorLogger;
