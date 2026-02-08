import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';

const MyRequests = () => {
  const [searchParams] = useSearchParams();
  const [requests, setRequests] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(searchParams.get('new') === 'true');
  const [formData, setFormData] = useState({
    service_type: '',
    title: '',
    description: '',
    priority: 'Normale',
    preferred_date: '',
    site_address: '',
  });
  const [submitLoading, setSubmitLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [requestsRes, servicesRes] = await Promise.all([
        api.get('/requests'),
        api.get('/services'),
      ]);
      setRequests(requestsRes.data);
      setServices(servicesRes.data);
    } catch (err) {
      console.error('Error loading data:', err);
    }
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitLoading(true);
    setError('');
    setMessage('');

    try {
      await api.post('/requests', formData);
      setMessage('Demande créée avec succès !');
      setShowForm(false);
      setFormData({
        service_type: '',
        title: '',
        description: '',
        priority: 'Normale',
        preferred_date: '',
        site_address: '',
      });
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la création');
    }

    setSubmitLoading(false);
  };

  const handleCancel = async (requestId) => {
    if (!window.confirm('Voulez-vous vraiment annuler cette demande ?')) return;

    try {
      await api.delete(`/requests/${requestId}`);
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'annulation');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      'En attente': 'bg-yellow-100 text-yellow-800',
      'En cours': 'bg-blue-100 text-blue-800',
      'Terminé': 'bg-green-100 text-green-800',
      'Annulé': 'bg-red-100 text-red-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || 'bg-gray-100'}`}>
        {status}
      </span>
    );
  };

  const getPriorityBadge = (priority) => {
    const styles = {
      'Basse': 'bg-gray-100 text-gray-800',
      'Normale': 'bg-blue-100 text-blue-800',
      'Haute': 'bg-orange-100 text-orange-800',
      'Urgente': 'bg-red-100 text-red-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[priority] || 'bg-gray-100'}`}>
        {priority}
      </span>
    );
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Mes Demandes</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            data-testid="new-request-button"
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            {showForm ? 'Annuler' : '+ Nouvelle demande'}
          </button>
        </div>

        {message && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            {message}
          </div>
        )}

        {/* New Request Form */}
        {showForm && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Nouvelle demande de service</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de service *
                  </label>
                  <select
                    name="service_type"
                    required
                    data-testid="request-service-select"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.service_type}
                    onChange={handleChange}
                  >
                    <option value="">Sélectionnez un service</option>
                    {services.map((service) => (
                      <option key={service.id} value={service.name}>
                        {service.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priorité
                  </label>
                  <select
                    name="priority"
                    data-testid="request-priority-select"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.priority}
                    onChange={handleChange}
                  >
                    <option value="Basse">Basse</option>
                    <option value="Normale">Normale</option>
                    <option value="Haute">Haute</option>
                    <option value="Urgente">Urgente</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Titre *
                </label>
                <input
                  type="text"
                  name="title"
                  required
                  data-testid="request-title-input"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                  placeholder="Ex: Installation vidéophone entrée"
                  value={formData.title}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <textarea
                  name="description"
                  required
                  rows="4"
                  data-testid="request-description-input"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                  placeholder="Décrivez votre demande en détail..."
                  value={formData.description}
                  onChange={handleChange}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date souhaitée
                  </label>
                  <input
                    type="date"
                    name="preferred_date"
                    data-testid="request-date-input"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.preferred_date}
                    onChange={handleChange}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Adresse du site
                  </label>
                  <input
                    type="text"
                    name="site_address"
                    data-testid="request-address-input"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    placeholder="Adresse d'intervention"
                    value={formData.site_address}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={submitLoading}
                  data-testid="request-submit-button"
                  className="px-6 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50"
                >
                  {submitLoading ? 'Envoi...' : 'Envoyer la demande'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Requests List */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {requests.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p>Aucune demande pour le moment.</p>
              <button
                onClick={() => setShowForm(true)}
                className="mt-4 text-cyan-600 hover:text-cyan-500"
              >
                Créer votre première demande
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Titre</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priorité</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {requests.map((request) => (
                    <tr key={request.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <span className="font-medium text-gray-900">{request.title}</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">{request.service_type}</td>
                      <td className="px-6 py-4">{getPriorityBadge(request.priority)}</td>
                      <td className="px-6 py-4">{getStatusBadge(request.status)}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(request.created_at).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-6 py-4">
                        {request.status === 'En attente' && (
                          <button
                            onClick={() => handleCancel(request.id)}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            Annuler
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default MyRequests;
