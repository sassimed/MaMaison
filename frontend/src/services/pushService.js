/**
 * Push Notification Service for MyDar
 * Handles service worker registration and push subscription
 */

const VAPID_PUBLIC_KEY = process.env.REACT_APP_VAPID_PUBLIC_KEY;

/**
 * Check if push notifications are supported
 */
export const isPushSupported = () => {
  return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
};

/**
 * Get current notification permission status
 */
export const getNotificationPermission = () => {
  if (!('Notification' in window)) return 'unsupported';
  return Notification.permission;
};

/**
 * Request notification permission from user
 */
export const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    return { status: 'unsupported', message: 'Les notifications ne sont pas supportées par ce navigateur' };
  }
  
  const permission = await Notification.requestPermission();
  return { status: permission, message: getPermissionMessage(permission) };
};

const getPermissionMessage = (permission) => {
  switch (permission) {
    case 'granted':
      return 'Notifications activées !';
    case 'denied':
      return 'Notifications refusées. Vous pouvez les activer dans les paramètres du navigateur.';
    case 'default':
      return 'Permission en attente';
    default:
      return 'Statut inconnu';
  }
};

/**
 * Register service worker
 */
export const registerServiceWorker = async () => {
  if (!('serviceWorker' in navigator)) {
    throw new Error('Service Worker non supporté');
  }
  
  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/'
    });
    
    console.log('[Push] Service Worker registered:', registration.scope);
    return registration;
  } catch (error) {
    console.error('[Push] Service Worker registration failed:', error);
    throw error;
  }
};

/**
 * Convert VAPID key from base64 to Uint8Array
 */
const urlBase64ToUint8Array = (base64String) => {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');
  
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  
  return outputArray;
};

/**
 * Subscribe to push notifications
 */
export const subscribeToPush = async (registration) => {
  if (!VAPID_PUBLIC_KEY) {
    throw new Error('VAPID public key not configured');
  }
  
  try {
    // Check for existing subscription
    let subscription = await registration.pushManager.getSubscription();
    
    if (subscription) {
      console.log('[Push] Already subscribed');
      return subscription;
    }
    
    // Create new subscription
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
    });
    
    console.log('[Push] New subscription created');
    return subscription;
  } catch (error) {
    console.error('[Push] Subscription failed:', error);
    throw error;
  }
};

/**
 * Unsubscribe from push notifications
 */
export const unsubscribeFromPush = async () => {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    
    if (subscription) {
      await subscription.unsubscribe();
      console.log('[Push] Unsubscribed successfully');
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('[Push] Unsubscribe failed:', error);
    throw error;
  }
};

/**
 * Get current push subscription
 */
export const getCurrentSubscription = async () => {
  try {
    const registration = await navigator.serviceWorker.ready;
    return await registration.pushManager.getSubscription();
  } catch (error) {
    console.error('[Push] Error getting subscription:', error);
    return null;
  }
};

/**
 * Full setup flow for push notifications
 */
export const setupPushNotifications = async () => {
  // Check support
  if (!isPushSupported()) {
    return { 
      success: false, 
      error: 'Push notifications not supported',
      subscription: null 
    };
  }
  
  // Request permission
  const { status } = await requestNotificationPermission();
  if (status !== 'granted') {
    return { 
      success: false, 
      error: 'Permission denied',
      permission: status,
      subscription: null 
    };
  }
  
  // Register service worker
  const registration = await registerServiceWorker();
  
  // Wait for service worker to be ready
  await navigator.serviceWorker.ready;
  
  // Subscribe to push
  const subscription = await subscribeToPush(registration);
  
  return {
    success: true,
    permission: 'granted',
    subscription: subscription.toJSON()
  };
};
