import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (token) {
      verifyEmail();
    } else {
      setLoading(false);
      setError('Token de vérification manquant');
    }
  }, [token]);

  const verifyEmail = async () => {
    try {
      const response = await api.post('/auth/verify-email', { token });
      setMessage(response.data.message);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la vérification');
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
        <div className="max-w-md w-full bg-white p-10 rounded-xl shadow-2xl text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-cyan-500 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Vérification en cours...</h2>
          <p className="text-gray-600">Veuillez patienter</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-md w-full bg-white p-10 rounded-xl shadow-2xl text-center">
        {success ? (
          <>
            <svg className="w-20 h-20 mx-auto mb-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-2xl font-bold text-gray-900 mb-2" data-testid="verify-email-success">Email vérifié !</h2>
            <p className="text-gray-600 mb-6">{message}</p>
            <p className="text-sm text-gray-500">Redirection vers la page de connexion...</p>
          </>
        ) : (
          <>
            <svg className="w-20 h-20 mx-auto mb-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h2 className="text-2xl font-bold text-gray-900 mb-2" data-testid="verify-email-error">Erreur de vérification</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="space-y-3">
              <Link
                to="/login"
                className="inline-block w-full px-6 py-2 text-white bg-gradient-to-r from-purple-600 to-cyan-500 rounded-lg hover:opacity-90"
              >
                Aller à la connexion
              </Link>
              <p className="text-sm text-gray-500">
                Besoin d'un nouveau lien ?{' '}
                <Link to="/login" className="text-cyan-600 hover:text-cyan-500">
                  Connectez-vous
                </Link>{' '}
                et demandez un renvoi.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
