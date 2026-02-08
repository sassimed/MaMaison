import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-cyan-600">SmartHome</h1>
          <button
            onClick={handleLogout}
            data-testid="logout-button"
            className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
          >
            Déconnexion
          </button>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4" data-testid="dashboard-welcome">
            Bienvenue, {user?.full_name} !
          </h2>
          <div className="space-y-2">
            <p data-testid="dashboard-email">
              <span className="font-semibold">Email:</span> {user?.email}
            </p>
            <p data-testid="dashboard-role">
              <span className="font-semibold">Rôle:</span>{' '}
              <span className="inline-block px-3 py-1 rounded-full text-sm font-semibold bg-cyan-100 text-cyan-800">
                {user?.role}
              </span>
            </p>
            {user?.phone && (
              <p>
                <span className="font-semibold">Téléphone:</span> {user.phone}
              </p>
            )}
          </div>
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-cyan-800">
              🚀 Phase 1 terminée : Authentification fonctionnelle !
            </p>
            <p className="text-sm text-gray-600 mt-2">
              Les prochaines phases incluront le site vitrine complet et toutes les fonctionnalités.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
