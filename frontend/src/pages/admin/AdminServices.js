import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';

const AdminServices = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
    detailed_description: '',
    advantages: '',
    use_cases: '',
    icon: '',
    category: 'automation',
    featured: false,
  });

  useEffect(() => {
    loadServices();
  }, []);

  const loadServices = async () => {
    try {
      const response = await api.get('/admin/services');
      setServices(response.data);
    } catch (err) {
      console.error('Error loading services:', err);
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const data = {
      name: formData.name,
      slug: formData.slug || formData.name.toLowerCase().replace(/\s+/g, '-'),
      description: formData.description,
      detailed_description: formData.detailed_description,
      advantages: formData.advantages.split('\n').filter(a => a.trim()),
      use_cases: formData.use_cases.split('\n').filter(u => u.trim()),
      icon: formData.icon,
      category: formData.category,
      featured: formData.featured,
    };

    try {
      if (editingService) {
        await api.put('/admin/services/' + editingService.id, data);
      } else {
        await api.post('/admin/services', data);
      }
      setShowForm(false);
      setEditingService(null);
      resetForm();
      loadServices();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur');
    }
  };

  const handleEdit = (service) => {
    setEditingService(service);
    setFormData({
      name: service.name,
      slug: service.slug,
      description: service.description,
      detailed_description: service.detailed_description,
      advantages: (service.advantages || []).join('\n'),
      use_cases: (service.use_cases || []).join('\n'),
      icon: service.icon || '',
      category: service.category,
      featured: service.featured || false,
    });
    setShowForm(true);
  };

  const handleDelete = async (serviceId) => {
    if (!window.confirm('Supprimer ce service ?')) return;
    try {
      await api.delete('/admin/services/' + serviceId);
      loadServices();
    } catch (err) {
      alert('Erreur');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      slug: '',
      description: '',
      detailed_description: '',
      advantages: '',
      use_cases: '',
      icon: '',
      category: 'automation',
      featured: false,
    });
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
          <h1 className="text-2xl font-bold text-gray-900">Gestion des Services</h1>
          <button
            onClick={() => { setShowForm(!showForm); setEditingService(null); resetForm(); }}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90"
          >
            {showForm ? 'Annuler' : '+ Nouveau service'}
          </button>
        </div>

        {showForm && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">
              {editingService ? 'Modifier le service' : 'Nouveau service'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Catégorie</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  >
                    <option value="security">Sécurité</option>
                    <option value="automation">Automatisation</option>
                    <option value="control">Contrôle</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description courte</label>
                <textarea
                  required
                  rows="2"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description détaillée</label>
                <textarea
                  required
                  rows="4"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  value={formData.detailed_description}
                  onChange={(e) => setFormData({ ...formData, detailed_description: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Avantages (un par ligne)</label>
                  <textarea
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    value={formData.advantages}
                    onChange={(e) => setFormData({ ...formData, advantages: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cas d'usage (un par ligne)</label>
                  <textarea
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    value={formData.use_cases}
                    onChange={(e) => setFormData({ ...formData, use_cases: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Icône (emoji)</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="Ex: 🔒"
                    value={formData.icon}
                    onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                  />
                </div>
                <div className="flex items-center pt-6">
                  <input
                    type="checkbox"
                    id="featured"
                    checked={formData.featured}
                    onChange={(e) => setFormData({ ...formData, featured: e.target.checked })}
                  />
                  <label htmlFor="featured" className="ml-2 text-sm text-gray-700">Mis en avant</label>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowForm(false); setEditingService(null); resetForm(); }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600"
                >
                  {editingService ? 'Mettre à jour' : 'Créer'}
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Catégorie</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {services.map((service) => (
                <tr key={service.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{service.icon}</span>
                      <div>
                        <p className="font-medium text-gray-900">{service.name}</p>
                        <p className="text-sm text-gray-500 truncate max-w-xs">{service.description}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 text-xs bg-gray-100 rounded-full capitalize">
                      {service.category}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button onClick={() => handleEdit(service)} className="text-cyan-600 hover:text-cyan-800">
                        Modifier
                      </button>
                      <button onClick={() => handleDelete(service.id)} className="text-red-600 hover:text-red-800">
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminServices;
