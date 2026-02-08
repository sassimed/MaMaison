import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await api.post('/auth/forgot-password', { email });
      setMessage(response.data.message);
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Une erreur est survenue');
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-2xl">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Mot de passe oublié
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Entrez votre email pour recevoir un lien de réinitialisation
          </p>
        </div>

        {!sent ? (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" data-testid="forgot-password-error">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Adresse email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                data-testid="forgot-password-email-input"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 sm:text-sm"
                placeholder="votre@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                data-testid="forgot-password-submit-button"
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-cyan-500 hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
              >
                {loading ? 'Envoi en cours...' : 'Envoyer le lien'}
              </button>
            </div>

            <div className="text-center">
              <Link to="/login" className="text-sm text-cyan-600 hover:text-cyan-500">
                ← Retour à la connexion
              </Link>
            </div>
          </form>
        ) : (
          <div className="mt-8 space-y-6">
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-4 rounded-lg text-center" data-testid="forgot-password-success">
              <svg className="w-12 h-12 mx-auto mb-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <p className="font-medium">{message}</p>
              <p className="text-sm mt-2">Vérifiez votre boîte de réception et vos spams.</p>
            </div>

            <div className="text-center space-y-3">
              <button
                onClick={() => { setSent(false); setEmail(''); }}
                className="text-sm text-cyan-600 hover:text-cyan-500"
              >
                Utiliser une autre adresse email
              </button>
              <br />
              <Link to="/login" className="text-sm text-gray-500 hover:text-gray-700">
                ← Retour à la connexion
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;
