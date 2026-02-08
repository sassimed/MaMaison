/* eslint-disable no-restricted-globals */

// MyDar Service Worker for Push Notifications

const CACHE_NAME = 'mydar-v1';

// Install event
self.addEventListener('install', (event) => {
  console.log('[SW] Service Worker installing...');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('[SW] Service Worker activated');
  event.waitUntil(self.clients.claim());
});

// Push event - Handle incoming push notifications
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  let data = {
    title: 'MyDar',
    body: 'Nouvelle notification',
    icon: '/mydar-logo.png',
    badge: '/mydar-logo.png',
    tag: 'mydar-notification',
    data: { url: '/dashboard' }
  };
  
  // Parse push data if available
  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      console.error('[SW] Error parsing push data:', e);
    }
  }
  
  const options = {
    body: data.body,
    icon: data.icon || '/mydar-logo.png',
    badge: data.badge || '/mydar-logo.png',
    tag: data.tag,
    data: data.data,
    requireInteraction: data.requireInteraction !== false,
    vibrate: data.vibrate || [200, 100, 200],
    actions: [
      { action: 'open', title: 'Voir' },
      { action: 'close', title: 'Fermer' }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action);
  
  event.notification.close();
  
  // Handle action buttons
  if (event.action === 'close') {
    return;
  }
  
  // Get the URL to open
  const urlToOpen = event.notification.data?.url || '/dashboard';
  
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already an open window
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.focus();
            client.navigate(urlToOpen);
            return;
          }
        }
        // Open new window if none exists
        if (self.clients.openWindow) {
          return self.clients.openWindow(urlToOpen);
        }
      })
  );
});

// Notification close event
self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification closed');
});
