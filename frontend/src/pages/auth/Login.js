import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState(location.state?.error || '');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(formData.email, formData.password);

    if (result.success) {
      // Check if there's a redirect URL
      const redirectUrl = searchParams.get('redirect');
      if (redirectUrl) {
        navigate(redirectUrl);
      } else {
        navigate('/dashboard');
      }
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleGoogleLogin = () => {
    // Build the redirect URI using window.location.origin
    const redirectUri = window.location.origin + '/auth/google/callback';
    
    // Google OAuth URL with your own client ID
    const googleAuthUrl = 'https://accounts.google.com/o/oauth2/v2/auth';
    const clientId = '862797443597-4749mvg4a2480flu29hj5utj3jqm9oej.apps.googleusercontent.com';
    
    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: 'openid email profile',
      access_type: 'offline',
      prompt: 'consent'
    });
    
    window.location.href = `${googleAuthUrl}?${params.toString()}`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-cyan-600 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-2xl">
        <div>
          <h2 className="mt-2 text-center text-3xl font-extrabold text-gray-900">
            Connexion
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Accédez à votre espace MyDar
          </p>
        </div>

        {/* Google Login Button */}
        <div>
          <button
            type="button"
            onClick={handleGoogleLogin}
            data-testid="google-login-btn"
            className="w-full flex items-center justify-center gap-3 py-3 px-4 border-2 border-gray-200 rounded-xl text-gray-700 bg-white hover:bg-gray-50 hover:border-gray-300 transition-all font-medium"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continuer avec Google
          </button>
        </div>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-white text-gray-500">ou</span>
          </div>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg" data-testid="login-error">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                data-testid="login-email-input"
                className="appearance-none block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                placeholder="votre@email.com"
                value={formData.email}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Mot de passe
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                data-testid="login-password-input"
                className="appearance-none block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              data-testid="login-submit-button"
              className="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-gradient-to-r from-purple-600 to-cyan-500 hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </button>
          </div>

          <div className="text-center space-y-2">
            <p className="text-sm text-gray-600">
              Pas encore de compte ?{' '}
              <Link to="/register" className="font-medium text-purple-600 hover:text-purple-500">
                S'inscrire
              </Link>
            </p>
            <Link to="/forgot-password" className="inline-block text-sm text-purple-600 hover:text-purple-500" data-testid="forgot-password-link">
              Mot de passe oublié ?
            </Link>
            <br />
            <Link to="/" className="mt-2 inline-block text-sm text-gray-500 hover:text-gray-700">
              ← Retour à l'accueil
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
