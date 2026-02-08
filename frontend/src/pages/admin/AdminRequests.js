import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';

const AdminRequests = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [updateData, setUpdateData] = useState({ status: '', admin_notes: '' });

  useEffect(() => {
    loadRequests();
  }, [filter]);

  const loadRequests = async () => {
    try {
      let url = '/admin/requests';
      if (filter) url += `?status_filter=${filter}`;
      const response = await api.get(url);
      setRequests(response.data);
    } catch (err) {
      console.error('Error loading requests:', err);
    }
    setLoading(false);
  };

  const handleUpdate = async () => {
    if (!selectedRequest) return;

    try {
      const data = {};
      if (updateData.status) data.status = updateData.status;
      if (updateData.admin_notes) data.admin_notes = updateData.admin_notes;

      await api.patch(`/admin/requests/${selectedRequest.id}`, data);
      setSelectedRequest(null);
      setUpdateData({ status: '', admin_notes: '' });
      loadRequests();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la mise à jour');
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
        <h1 className="text-2xl font-bold text-gray-900">Gestion des Demandes</h1>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 flex gap-4">
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="">Tous les statuts</option>
            <option value="En attente">En attente</option>
            <option value="En cours">En cours</option>
            <option value="Terminé">Terminé</option>
            <option value="Annulé">Annulé</option>
          </select>
        </div>

        {/* Requests table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Demande</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
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
                      <p className="font-medium text-gray-900">{request.title}</p>
                      <p className="text-sm text-gray-500 truncate max-w-xs">{request.description}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-gray-900">{request.user_name}</p>
                      <p className="text-xs text-gray-500">{request.user_email}</p>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{request.service_type}</td>
                    <td className="px-6 py-4">{getPriorityBadge(request.priority)}</td>
                    <td className="px-6 py-4">{getStatusBadge(request.status)}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(request.created_at).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => {
                          setSelectedRequest(request);
                          setUpdateData({ status: request.status, admin_notes: request.admin_notes || '' });
                        }}
                        className="text-cyan-600 hover:text-cyan-800"
                      >
                        Modifier
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Edit Modal */}
        {selectedRequest && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4">
              <h2 className="text-lg font-semibold mb-4">Modifier la demande</h2>
              
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Titre</p>
                  <p className="font-medium">{selectedRequest.title}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Statut</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={updateData.status}
                    onChange={(e) => setUpdateData({ ...updateData, status: e.target.value })}
                  >
                    <option value="En attente">En attente</option>
                    <option value="En cours">En cours</option>
                    <option value="Terminé">Terminé</option>
                    <option value="Annulé">Annulé</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes admin</label>
                  <textarea
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    placeholder="Notes internes..."
                    value={updateData.admin_notes}
                    onChange={(e) => setUpdateData({ ...updateData, admin_notes: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setSelectedRequest(null)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  onClick={handleUpdate}
                  className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600"
                >
                  Enregistrer
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AdminRequests;
