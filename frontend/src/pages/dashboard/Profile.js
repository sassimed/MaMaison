import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { MapPin } from 'lucide-react';

function Profile() {
  const { user, refreshUser } = useAuth();
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    street: '',
    street2: '',
    postal_code: '',
    city: '',
    country: 'Tunisie',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(function() {
    if (user) {
      var addressDetails = user.address_details || {};
      setFormData({
        full_name: user.full_name || '',
        phone: user.phone || '',
        street: addressDetails.street || '',
        street2: addressDetails.street2 || '',
        postal_code: addressDetails.postal_code || '',
        city: addressDetails.city || '',
        country: addressDetails.country || 'France',
      });
    }
  }, [user]);

  function handleChange(e) {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
    setMessage('');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      var payload = {
        full_name: formData.full_name,
        phone: formData.phone,
        address_details: {
          street: formData.street,
          street2: formData.street2,
          postal_code: formData.postal_code,
          city: formData.city,
          country: formData.country,
        }
      };
      
      await api.put('/user/profile', payload);
      setMessage('Profil mis à jour avec succès !');
      
      // Refresh user data in context
      if (refreshUser) {
        refreshUser();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la mise à jour');
    }

    setLoading(false);
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Mon Profil</h1>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {message && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
                {message}
              </div>
            )}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
              />
              <p className="text-xs text-gray-500 mt-1">L'email ne peut pas être modifié</p>
            </div>

            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
                Nom complet
              </label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                required
                data-testid="profile-name-input"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                value={formData.full_name}
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
                data-testid="profile-phone-input"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                placeholder="06 12 34 56 78"
                value={formData.phone}
                onChange={handleChange}
              />
            </div>

            {/* Address Section */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-cyan-500" />
                Adresse
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="street" className="block text-sm font-medium text-gray-700 mb-1">
                    Adresse (rue, numéro)
                  </label>
                  <input
                    id="street"
                    name="street"
                    type="text"
                    data-testid="profile-street-input"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    placeholder="123 rue de la Domotique"
                    value={formData.street}
                    onChange={handleChange}
                  />
                </div>

                <div>
                  <label htmlFor="street2" className="block text-sm font-medium text-gray-700 mb-1">
                    Complément d'adresse (optionnel)
                  </label>
                  <input
                    id="street2"
                    name="street2"
                    type="text"
                    data-testid="profile-street2-input"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    placeholder="Appartement, étage, bâtiment..."
                    value={formData.street2}
                    onChange={handleChange}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="postal_code" className="block text-sm font-medium text-gray-700 mb-1">
                      Code postal
                    </label>
                    <input
                      id="postal_code"
                      name="postal_code"
                      type="text"
                      data-testid="profile-postal-input"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                      placeholder="75001"
                      value={formData.postal_code}
                      onChange={handleChange}
                    />
                  </div>

                  <div>
                    <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
                      Ville
                    </label>
                    <input
                      id="city"
                      name="city"
                      type="text"
                      data-testid="profile-city-input"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                      placeholder="Paris"
                      value={formData.city}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-1">
                    Pays
                  </label>
                  <select
                    id="country"
                    name="country"
                    data-testid="profile-country-select"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    value={formData.country}
                    onChange={handleChange}
                  >
                    <option value="Tunisie">Tunisie</option>
                    <option value="Algérie">Algérie</option>
                    <option value="Maroc">Maroc</option>
                    <option value="Libye">Libye</option>
                    <option value="France">France</option>
                    <option value="Autre">Autre</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 pt-4 border-t">
              <button
                type="submit"
                disabled={loading}
                data-testid="profile-submit-button"
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {loading ? 'Enregistrement...' : 'Enregistrer'}
              </button>
              <span className="text-sm text-gray-500">
                Type de compte: <span className="font-medium">{user?.role}</span>
              </span>
            </div>
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default Profile;
