import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';

const CompanyInfo = () => {
  const { user } = useAuth();
  const [companyName, setCompanyName] = useState('');
  const [siret, setSiret] = useState('');
  const [address, setAddress] = useState('');
  const [technicalContact, setTechnicalContact] = useState('');
  const [website, setWebsite] = useState('');
  const [sites, setSites] = useState([]);
  const [newSiteName, setNewSiteName] = useState('');
  const [newSiteAddress, setNewSiteAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (user?.company_info) {
      setCompanyName(user.company_info.company_name || '');
      setSiret(user.company_info.siret || '');
      setAddress(user.company_info.address || '');
      setTechnicalContact(user.company_info.technical_contact || '');
      setWebsite(user.company_info.website || '');
      setSites(user.company_info.sites || []);
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      await api.put('/user/company-info', {
        company_name: companyName,
        siret: siret,
        address: address,
        technical_contact: technicalContact,
        website: website,
        sites: sites,
      });
      setMessage('Informations mises à jour avec succès !');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la mise à jour');
    }

    setLoading(false);
  };

  const handleAddSite = async (e) => {
    e.preventDefault();
    if (!newSiteName || !newSiteAddress) return;

    try {
      const response = await api.post('/user/company-info/sites', {
        name: newSiteName,
        address: newSiteAddress,
      });
      setSites([...sites, response.data.site]);
      setNewSiteName('');
      setNewSiteAddress('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur');
    }
  };

  const handleRemoveSite = async (siteId) => {
    if (!window.confirm('Supprimer ce site ?')) return;

    try {
      await api.delete('/user/company-info/sites/' + siteId);
      setSites(sites.filter((s) => s.id !== siteId));
    } catch (err) {
      setError('Erreur lors de la suppression');
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Mon Entreprise</h1>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Informations de l'entreprise</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom de l'entreprise
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  SIRET
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  value={siret}
                  onChange={(e) => setSiret(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Adresse du siège
              </label>
              <textarea
                rows="2"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact technique
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="Email ou téléphone"
                  value={technicalContact}
                  onChange={(e) => setTechnicalContact(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Site web
                </label>
                <input
                  type="url"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="https://..."
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                />
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50"
              >
                {loading ? 'Enregistrement...' : 'Enregistrer'}
              </button>
            </div>
          </form>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Gestion des sites</h2>

          <form onSubmit={handleAddSite} className="flex gap-4 mb-6">
            <input
              type="text"
              placeholder="Nom du site"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
              value={newSiteName}
              onChange={(e) => setNewSiteName(e.target.value)}
            />
            <input
              type="text"
              placeholder="Adresse du site"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
              value={newSiteAddress}
              onChange={(e) => setNewSiteAddress(e.target.value)}
            />
            <button
              type="submit"
              className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600"
            >
              Ajouter
            </button>
          </form>

          <div className="space-y-2">
            {sites.length === 0 ? (
              <p className="text-gray-500 text-center py-4">Aucun site enregistré</p>
            ) : (
              sites.map((site) => (
                <div
                  key={site.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">{site.name}</p>
                    <p className="text-sm text-gray-500">{site.address}</p>
                  </div>
                  <button
                    onClick={() => handleRemoveSite(site.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Supprimer
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default CompanyInfo;
