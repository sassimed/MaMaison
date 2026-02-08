import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH

const GoogleCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('Connexion avec Google en cours...');

  useEffect(() => {
    // Prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processGoogleAuth = async () => {
      // Get authorization code from URL query params
      const code = searchParams.get('code');
      const errorParam = searchParams.get('error');

      if (errorParam) {
        console.error('Google auth error:', errorParam);
        setError('Authentification Google annulée');
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      if (!code) {
        console.error('No authorization code found');
        setError('Code d\'autorisation manquant');
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      setStatus('Vérification de votre compte...');

      try {
        // Exchange code for user data
        // REMINDER: DO NOT HARDCODE THE URL
        const redirectUri = window.location.origin + '/auth/google/callback';
        
        const response = await api.post('/auth/google/callback', {
          code: code,
          redirect_uri: redirectUri
        }, {
          withCredentials: true
        });

        const data = response.data;

        if (data.needs_role_selection) {
          // New user - redirect to role selection
          setStatus('Nouveau compte détecté...');
          navigate('/select-role', { 
            state: { 
              user: data.user,
              tempToken: data.temp_token
            },
            replace: true
          });
        } else {
          // Existing user - store tokens and update context
          setStatus('Connexion réussie !');
          
          // Store tokens
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          localStorage.setItem('user', JSON.stringify(data.user));
          
          // Update auth context directly
          setUser(data.user);
          
          // Small delay to ensure state is updated, then navigate
          setTimeout(() => {
            navigate('/dashboard', { replace: true });
          }, 100);
        }
      } catch (error) {
        console.error('Google auth error:', error);
        const errorMessage = error.response?.data?.detail || 'Erreur d\'authentification';
        setError(errorMessage);
        setTimeout(() => {
          navigate('/login', { state: { error: errorMessage } });
        }, 2000);
      }
    };

    processGoogleAuth();
  }, [navigate, searchParams, setUser]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-cyan-600">
        <div className="bg-white p-8 rounded-2xl shadow-xl text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Erreur de connexion</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <p className="text-gray-500 text-sm">Redirection vers la page de connexion...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-cyan-600">
      <div className="bg-white p-8 rounded-2xl shadow-xl text-center max-w-md">
        <div className="animate-spin w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full mx-auto mb-6"></div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Connexion Google</h2>
        <p className="text-gray-600">{status}</p>
      </div>
    </div>
  );
};

export default GoogleCallback;
