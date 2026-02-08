import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';

const AdminAppointments = () => {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [updateData, setUpdateData] = useState({ status: '', meet_link: '' });

  useEffect(() => {
    loadAppointments();
  }, [filter]);

  const loadAppointments = async () => {
    try {
      let url = '/admin/appointments';
      if (filter) url += `?status_filter=${filter}`;
      const response = await api.get(url);
      setAppointments(response.data);
    } catch (err) {
      console.error('Error loading appointments:', err);
    }
    setLoading(false);
  };

  const handleUpdateStatus = async () => {
    if (!selectedAppointment) return;

    try {
      let url = `/admin/appointments/${selectedAppointment.id}/status?new_status=${updateData.status}`;
      if (updateData.meet_link) url += `&meet_link=${encodeURIComponent(updateData.meet_link)}`;
      
      await api.patch(url);
      setSelectedAppointment(null);
      setUpdateData({ status: '', meet_link: '' });
      loadAppointments();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la mise à jour');
    }
  };

  const handleDelete = async (appointmentId) => {
    if (!window.confirm('Voulez-vous vraiment supprimer ce rendez-vous ?')) return;

    try {
      await api.delete(`/admin/appointments/${appointmentId}`);
      loadAppointments();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      'En attente': 'bg-yellow-100 text-yellow-800',
      'Confirmé': 'bg-green-100 text-green-800',
      'Terminé': 'bg-blue-100 text-blue-800',
      'Annulé': 'bg-red-100 text-red-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || 'bg-gray-100'}`}>
        {status}
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
        <h1 className="text-2xl font-bold text-gray-900">Gestion des Rendez-vous</h1>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 flex gap-4">
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="">Tous les statuts</option>
            <option value="En attente">En attente</option>
            <option value="Confirmé">Confirmé</option>
            <option value="Terminé">Terminé</option>
            <option value="Annulé">Annulé</option>
          </select>
        </div>

        {/* Appointments table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Heure</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Meet</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {appointments.map((apt) => (
                  <tr key={apt.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <p className="font-medium text-gray-900">{apt.full_name}</p>
                      <p className="text-xs text-gray-500">{apt.email}</p>
                      <p className="text-xs text-gray-500">{apt.phone}</p>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{apt.service_type}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(apt.preferred_date).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{apt.preferred_time}</td>
                    <td className="px-6 py-4">{getStatusBadge(apt.status)}</td>
                    <td className="px-6 py-4">
                      {apt.meet_link ? (
                        <a href={apt.meet_link} target="_blank" rel="noopener noreferrer" className="text-cyan-600 hover:underline text-sm">
                          Lien
                        </a>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedAppointment(apt);
                            setUpdateData({ status: apt.status, meet_link: apt.meet_link || '' });
                          }}
                          className="text-cyan-600 hover:text-cyan-800"
                        >
                          Modifier
                        </button>
                        <button
                          onClick={() => handleDelete(apt.id)}
                          className="text-red-600 hover:text-red-800"
                        >
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

        {/* Edit Modal */}
        {selectedAppointment && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4">
              <h2 className="text-lg font-semibold mb-4">Modifier le rendez-vous</h2>
              
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Client</p>
                  <p className="font-medium">{selectedAppointment.full_name}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Statut</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={updateData.status}
                    onChange={(e) => setUpdateData({ ...updateData, status: e.target.value })}
                  >
                    <option value="En attente">En attente</option>
                    <option value="Confirmé">Confirmé</option>
                    <option value="Terminé">Terminé</option>
                    <option value="Annulé">Annulé</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Lien Google Meet</label>
                  <input
                    type="url"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    placeholder="https://meet.google.com/..."
                    value={updateData.meet_link}
                    onChange={(e) => setUpdateData({ ...updateData, meet_link: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setSelectedAppointment(null)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  onClick={handleUpdateStatus}
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

export default AdminAppointments;
