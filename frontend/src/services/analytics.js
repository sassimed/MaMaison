/**
 * Analytics Tracking Service
 * Tracks user events and sends them to the backend
 */

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Session management
let sessionId = sessionStorage.getItem('analytics_session_id');
let visitorId = localStorage.getItem('analytics_visitor_id');

// Initialize session if not exists
if (!sessionId) {
  sessionId = 'sess_' + Math.random().toString(36).substr(2, 16);
  sessionStorage.setItem('analytics_session_id', sessionId);
}

// Track queue for offline support
let trackQueue = [];
let isTracking = false;

/**
 * Send tracking event to backend
 */
const sendEvent = async (eventData) => {
  try {
    const response = await fetch(`${API_URL}/api/analytics/track`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...eventData,
        session_id: sessionId,
        visitor_id: visitorId,
        referrer: document.referrer || null,
        utm_source: new URLSearchParams(window.location.search).get('utm_source'),
        utm_medium: new URLSearchParams(window.location.search).get('utm_medium'),
        utm_campaign: new URLSearchParams(window.location.search).get('utm_campaign'),
      }),
    });
    
    if (response.ok) {
      const data = await response.json();
      // Update visitor ID if returned by server
      if (data.visitor_id && !visitorId) {
        visitorId = data.visitor_id;
        localStorage.setItem('analytics_visitor_id', visitorId);
      }
      return data;
    }
  } catch (error) {
    console.warn('[Analytics] Failed to track event:', error);
    // Queue for retry
    trackQueue.push(eventData);
  }
  return null;
};

/**
 * Process queued events
 */
const processQueue = async () => {
  if (isTracking || trackQueue.length === 0) return;
  
  isTracking = true;
  while (trackQueue.length > 0) {
    const event = trackQueue.shift();
    await sendEvent(event);
  }
  isTracking = false;
};

// Process queue periodically
setInterval(processQueue, 30000);

/**
 * Analytics API
 */
const analytics = {
  /**
   * Track page view
   */
  pageView: (pageTitle) => {
    sendEvent({
      event_type: 'page_view',
      page_url: window.location.href,
      page_title: pageTitle || document.title,
    });
  },

  /**
   * Track product view
   */
  productView: (productId, productName) => {
    sendEvent({
      event_type: 'product_view',
      page_url: window.location.href,
      product_id: productId,
      product_name: productName,
    });
  },

  /**
   * Track search
   */
  search: (query) => {
    sendEvent({
      event_type: 'search',
      page_url: window.location.href,
      search_query: query,
    });
  },

  /**
   * Track add to cart
   */
  addToCart: (productId, productName, quantity = 1) => {
    sendEvent({
      event_type: 'add_to_cart',
      page_url: window.location.href,
      product_id: productId,
      product_name: productName,
      metadata: { quantity },
    });
  },

  /**
   * Track remove from cart
   */
  removeFromCart: (productId, productName) => {
    sendEvent({
      event_type: 'remove_from_cart',
      page_url: window.location.href,
      product_id: productId,
      product_name: productName,
    });
  },

  /**
   * Track checkout start
   */
  checkoutStart: (cartTotal, itemCount) => {
    sendEvent({
      event_type: 'checkout_start',
      page_url: window.location.href,
      metadata: { cart_total: cartTotal, item_count: itemCount },
    });
  },

  /**
   * Track checkout complete
   */
  checkoutComplete: (orderId, orderTotal) => {
    sendEvent({
      event_type: 'checkout_complete',
      page_url: window.location.href,
      metadata: { order_id: orderId, order_total: orderTotal },
    });
  },

  /**
   * Track click event
   */
  click: (elementName, metadata = {}) => {
    sendEvent({
      event_type: 'click',
      page_url: window.location.href,
      metadata: { element: elementName, ...metadata },
    });
  },

  /**
   * Track error
   */
  error: (errorMessage, errorStack = null) => {
    sendEvent({
      event_type: 'error',
      page_url: window.location.href,
      metadata: { error: errorMessage, stack: errorStack },
    });
  },

  /**
   * Track login
   */
  login: (userId, method = 'email') => {
    sendEvent({
      event_type: 'login',
      page_url: window.location.href,
      user_id: userId,
      metadata: { method },
    });
  },

  /**
   * Track logout
   */
  logout: (userId) => {
    sendEvent({
      event_type: 'logout',
      page_url: window.location.href,
      user_id: userId,
    });
  },

  /**
   * Track signup
   */
  signup: (userId, method = 'email') => {
    sendEvent({
      event_type: 'signup',
      page_url: window.location.href,
      user_id: userId,
      metadata: { method },
    });
  },

  /**
   * Track chat start
   */
  chatStart: (userId = null) => {
    sendEvent({
      event_type: 'chat_start',
      page_url: window.location.href,
      user_id: userId,
    });
  },

  /**
   * Track chat message
   */
  chatMessage: (userId = null, messageType = 'user') => {
    sendEvent({
      event_type: 'chat_message',
      page_url: window.location.href,
      user_id: userId,
      metadata: { message_type: messageType },
    });
  },

  /**
   * Set user ID (call after login)
   */
  setUser: (userId) => {
    // Update future events with user ID
    localStorage.setItem('analytics_user_id', userId);
  },

  /**
   * Clear user (call after logout)
   */
  clearUser: () => {
    localStorage.removeItem('analytics_user_id');
  },

  /**
   * Send heartbeat (for online user tracking)
   */
  heartbeat: () => {
    const userId = localStorage.getItem('analytics_user_id');
    fetch(`${API_URL}/api/analytics/heartbeat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        visitor_id: visitorId,
        user_id: userId,
        current_page: window.location.pathname,
      }),
    }).catch(() => {});
  },

  /**
   * Get current session ID
   */
  getSessionId: () => sessionId,

  /**
   * Get current visitor ID
   */
  getVisitorId: () => visitorId,
};

// Start heartbeat (every 60 seconds)
setInterval(() => analytics.heartbeat(), 60000);

// Send initial heartbeat
setTimeout(() => analytics.heartbeat(), 1000);

// Track errors globally
window.addEventListener('error', (event) => {
  analytics.error(event.message, event.error?.stack);
});

window.addEventListener('unhandledrejection', (event) => {
  analytics.error(`Unhandled Promise Rejection: ${event.reason}`);
});

export default analytics;
