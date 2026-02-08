import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-cyan-500">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center text-white">
          <h1 className="text-5xl font-bold mb-6" data-testid="home-title">
            SmartHome
          </h1>
          <p className="text-xl mb-8">
            Expert en domotique & sécurité connectée
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              to="/login"
              data-testid="home-login-button"
              className="bg-white text-cyan-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Connexion
            </Link>
            <Link
              to="/register"
              data-testid="home-register-button"
              className="bg-blue-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-400 transition-colors border-2 border-white"
            >
              Créer un compte
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
