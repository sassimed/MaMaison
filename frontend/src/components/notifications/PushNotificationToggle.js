import React, { useState, useEffect } from 'react';
import { Bell, BellOff, Check, X, Loader2 } from 'lucide-react';
import { 
  isPushSupported, 
  getNotificationPermission,
  setupPushNotifications,
  unsubscribeFromPush,
  getCurrentSubscription
} from '../../services/pushService';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PushNotificationToggle = ({ className = '' }) => {
  const [isSupported, setIsSupported] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [permission, setPermission] = useState('default');
  const [loading, setLoading] = useState(false);
  const [showBanner, setShowBanner] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    const supported = isPushSupported();
    setIsSupported(supported);
    
    if (supported) {
      setPermission(getNotificationPermission());
      const subscription = await getCurrentSubscription();
      setIsSubscribed(!!subscription);
      
      // Show banner if not subscribed and not denied
      const perm = getNotificationPermission();
      if (!subscription && perm !== 'denied') {
        // Check if user dismissed banner before
        const dismissed = localStorage.getItem('pushBannerDismissed');
        if (!dismissed) {
          setShowBanner(true);
        }
      }
    }
  };

  const handleSubscribe = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await setupPushNotifications();
      
      if (result.success && result.subscription) {
        // Send subscription to backend
        const token = localStorage.getItem('token');
        await axios.post(
          `${API_URL}/api/notifications/subscribe-push`,
          result.subscription,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        setIsSubscribed(true);
        setPermission('granted');
        setShowBanner(false);
      } else {
        setError(result.error || 'Échec de l\'activation');
        if (result.permission === 'denied') {
          setPermission('denied');
        }
      }
    } catch (err) {
      console.error('Push subscription error:', err);
      setError('Erreur lors de l\'activation');
    } finally {
      setLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await unsubscribeFromPush();
      
      // Remove from backend
      const token = localStorage.getItem('token');
      await axios.delete(
        `${API_URL}/api/notifications/unsubscribe-push`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setIsSubscribed(false);
    } catch (err) {
      console.error('Push unsubscribe error:', err);
      setError('Erreur lors de la désactivation');
    } finally {
      setLoading(false);
    }
  };

  const dismissBanner = () => {
    setShowBanner(false);
    localStorage.setItem('pushBannerDismissed', 'true');
  };

  // Not supported
  if (!isSupported) {
    return null;
  }

  // Permission denied
  if (permission === 'denied') {
    return (
      <div className={`flex items-center gap-2 text-gray-500 text-sm ${className}`}>
        <BellOff className="w-4 h-4" />
        <span>Notifications bloquées</span>
      </div>
    );
  }

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={isSubscribed ? handleUnsubscribe : handleSubscribe}
        disabled={loading}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg transition-all
          ${isSubscribed 
            ? 'bg-green-100 text-green-700 hover:bg-green-200' 
            : 'bg-gray-100 text-gray-700 hover:bg-purple-100 hover:text-purple-700'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
          ${className}
        `}
        data-testid="push-notification-toggle"
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : isSubscribed ? (
          <Bell className="w-4 h-4" />
        ) : (
          <BellOff className="w-4 h-4" />
        )}
        <span className="text-sm font-medium">
          {loading 
            ? 'Chargement...' 
            : isSubscribed 
              ? 'Notifications activées' 
              : 'Activer les notifications'
          }
        </span>
      </button>

      {error && (
        <p className="text-red-500 text-xs mt-1">{error}</p>
      )}

      {/* Floating banner for first-time users */}
      {showBanner && (
        <div 
          className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 
                     bg-white rounded-xl shadow-2xl border border-gray-200 p-4 z-50
                     animate-in slide-in-from-bottom-5"
          data-testid="push-notification-banner"
        >
          <button 
            onClick={dismissBanner}
            className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
          
          <div className="flex items-start gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Bell className="w-6 h-6 text-purple-600" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900">
                Activez les notifications
              </h4>
              <p className="text-sm text-gray-600 mt-1">
                Recevez des alertes instantanées pour les nouvelles opportunités et messages.
              </p>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={handleSubscribe}
                  disabled={loading}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 
                           text-white text-sm font-medium rounded-lg
                           hover:from-purple-700 hover:to-cyan-600
                           disabled:opacity-50 flex items-center gap-2"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4" />
                  )}
                  Activer
                </button>
                <button
                  onClick={dismissBanner}
                  className="px-4 py-2 text-gray-600 text-sm hover:bg-gray-100 rounded-lg"
                >
                  Plus tard
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default PushNotificationToggle;
