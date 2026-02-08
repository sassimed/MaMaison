import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone: '',
    role: 'PARTICULIER',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [registrationComplete, setRegistrationComplete] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      return;
    }

    if (formData.password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères');
      return;
    }

    setLoading(true);

    const userData = {
      email: formData.email,
      password: formData.password,
      full_name: formData.full_name,
      phone: formData.phone,
      role: formData.role,
    };

    try {
      const response = await api.post('/auth/register', userData);
      setRegisteredEmail(response.data.email);
      setRegistrationComplete(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'inscription');
    }

    setLoading(false);
  };

  const handleResendVerification = async () => {
    setLoading(true);
    try {
      await api.post('/auth/resend-verification', { email: registeredEmail });
      setError('');
      alert('Un nouveau lien de vérification a été envoyé !');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du renvoi');
    }
    setLoading(false);
  };

  if (registrationComplete) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-2xl text-center">
          <div>
            <svg className="w-20 h-20 mx-auto mb-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <h2 className="text-2xl font-bold text-gray-900 mb-2" data-testid="registration-success">
              Inscription réussie !
            </h2>
            <p className="text-gray-600 mb-2">
              Un email de confirmation a été envoyé à :
            </p>
            <p className="font-medium text-cyan-600 mb-6">{registeredEmail}</p>
            <p className="text-sm text-gray-500 mb-6">
              Vérifiez votre boîte de réception et cliquez sur le lien pour activer votre compte.
            </p>
          </div>

          <div className="space-y-4">
            <Link
              to="/login"
              className="inline-block w-full px-6 py-3 text-white bg-gradient-to-r from-purple-600 to-cyan-500 rounded-lg hover:opacity-90 transition-opacity"
            >
              Aller à la connexion
            </Link>
            
            <div className="pt-4 border-t">
              <p className="text-sm text-gray-500 mb-2">Vous n'avez pas reçu l'email ?</p>
              <button
                onClick={handleResendVerification}
                disabled={loading}
                className="text-cyan-600 hover:text-cyan-500 text-sm font-medium disabled:opacity-50"
              >
                {loading ? 'Envoi en cours...' : 'Renvoyer le lien de vérification'}
              </button>
            </div>

            <Link to="/" className="inline-block text-sm text-gray-500 hover:text-gray-700">
              ← Retour à l'accueil
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-2xl">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Créer un compte
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Rejoignez MyDar
          </p>
        </div>

        {/* Google Login Button */}
        <div>
          <button
            type="button"
            onClick={handleGoogleLogin}
            data-testid="google-register-btn"
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

        <form className="mt-4 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" data-testid="register-error">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
                Nom complet
              </label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                required
                data-testid="register-name-input"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm"
                placeholder="Jean Dupont"
                value={formData.full_name}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                data-testid="register-email-input"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm"
                placeholder="votre@email.com"
                value={formData.email}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                Téléphone
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                data-testid="register-phone-input"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm"
                placeholder="0123456789"
                value={formData.phone}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
                Type de compte
              </label>
              <select
                id="role"
                name="role"
                data-testid="register-role-select"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm"
                value={formData.role}
                onChange={handleChange}
              >
                <option value="PARTICULIER">Particulier</option>
                <option value="PROFESSIONNEL">Professionnel</option>
              </select>
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
                data-testid="register-password-input"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                Confirmer le mot de passe
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                data-testid="register-confirm-password-input"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm"
                placeholder="••••••••"
                value={formData.confirmPassword}
                onChange={handleChange}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              data-testid="register-submit-button"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-cyan-500 hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
            >
              {loading ? 'Inscription...' : "S'inscrire"}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              Déjà un compte ?{' '}
              <Link to="/login" className="font-medium text-cyan-600 hover:text-cyan-500">
                Se connecter
              </Link>
            </p>
            <Link to="/" className="mt-3 inline-block text-sm text-gray-500 hover:text-gray-700">
              ← Retour à l'accueil
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;
