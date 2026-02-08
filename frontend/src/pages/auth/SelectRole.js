import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import { User, Briefcase, ArrowRight } from 'lucide-react';

const SelectRole = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useAuth();
  const [selectedRole, setSelectedRole] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const user = location.state?.user;

  // If no user data, redirect to login
  if (!user) {
    navigate('/login');
    return null;
  }

  const handleSelectRole = async () => {
    if (!selectedRole) {
      setError('Veuillez choisir un type de compte');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/auth/google/set-role', {
        role: selectedRole
      }, {
        withCredentials: true
      });

      const data = response.data;

      // Store tokens and user
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      // Update auth context directly
      setUser(data.user);

      // Redirect to dashboard
      setTimeout(() => {
        navigate('/dashboard', { replace: true });
      }, 100);
    } catch (error) {
      console.error('Set role error:', error);
      setError(error.response?.data?.detail || 'Erreur lors de la configuration du compte');
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-cyan-600 p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-lg w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 mx-auto mb-4 rounded-full overflow-hidden border-4 border-purple-200">
            {user.picture ? (
              <img src={user.picture} alt={user.full_name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full bg-purple-100 flex items-center justify-center">
                <User className="w-10 h-10 text-purple-600" />
              </div>
            )}
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Bienvenue, {user.full_name} !
          </h1>
          <p className="text-gray-600">
            Pour finaliser votre inscription, choisissez votre type de compte
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Role selection */}
        <div className="space-y-4 mb-8">
          {/* Particulier */}
          <button
            type="button"
            onClick={() => setSelectedRole('PARTICULIER')}
            className={`w-full p-6 rounded-xl border-2 text-left transition-all ${
              selectedRole === 'PARTICULIER'
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50/50'
            }`}
            data-testid="select-particulier"
          >
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                selectedRole === 'PARTICULIER' ? 'bg-purple-500 text-white' : 'bg-purple-100 text-purple-600'
              }`}>
                <User className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 text-lg mb-1">Particulier</h3>
                <p className="text-gray-600 text-sm">
                  Je cherche des produits smart home et des installateurs pour mon domicile
                </p>
                <ul className="mt-3 text-sm text-gray-500 space-y-1">
                  <li>✓ Acheter des produits domotiques</li>
                  <li>✓ Publier des annonces de demande</li>
                  <li>✓ Recevoir des devis de professionnels</li>
                </ul>
              </div>
            </div>
          </button>

          {/* Professionnel */}
          <button
            type="button"
            onClick={() => setSelectedRole('PROFESSIONNEL')}
            className={`w-full p-6 rounded-xl border-2 text-left transition-all ${
              selectedRole === 'PROFESSIONNEL'
                ? 'border-cyan-500 bg-cyan-50'
                : 'border-gray-200 hover:border-cyan-300 hover:bg-cyan-50/50'
            }`}
            data-testid="select-professionnel"
          >
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                selectedRole === 'PROFESSIONNEL' ? 'bg-cyan-500 text-white' : 'bg-cyan-100 text-cyan-600'
              }`}>
                <Briefcase className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 text-lg mb-1">Professionnel</h3>
                <p className="text-gray-600 text-sm">
                  Je suis installateur et je cherche des missions domotiques
                </p>
                <ul className="mt-3 text-sm text-gray-500 space-y-1">
                  <li>✓ Consulter les annonces de clients</li>
                  <li>✓ Envoyer des devis et propositions</li>
                  <li>✓ Développer mon activité</li>
                </ul>
              </div>
            </div>
          </button>
        </div>

        {/* Submit button */}
        <button
          onClick={handleSelectRole}
          disabled={!selectedRole || loading}
          className={`w-full py-4 rounded-xl font-semibold text-white flex items-center justify-center gap-2 transition-all ${
            selectedRole && !loading
              ? 'bg-gradient-to-r from-purple-600 to-cyan-600 hover:opacity-90'
              : 'bg-gray-300 cursor-not-allowed'
          }`}
          data-testid="confirm-role-btn"
        >
          {loading ? (
            <>
              <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
              Configuration en cours...
            </>
          ) : (
            <>
              Continuer
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>

        {/* Footer */}
        <p className="text-center text-sm text-gray-500 mt-6">
          Vous pourrez modifier votre type de compte plus tard dans les paramètres
        </p>
      </div>
    </div>
  );
};

export default SelectRole;
