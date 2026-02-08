import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';

const MyAppointments = () => {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAppointments();
  }, []);

  const loadAppointments = async () => {
    try {
      const response = await api.get('/appointments/my-appointments');
      setAppointments(response.data);
    } catch (err) {
      console.error('Error loading appointments:', err);
    }
    setLoading(false);
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
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Mes Rendez-vous</h1>
          <a
            href="/rendez-vous"
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            + Nouveau rendez-vous
          </a>
        </div>

        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {appointments.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p>Aucun rendez-vous pour le moment.</p>
              <a
                href="/rendez-vous"
                className="mt-4 inline-block text-cyan-600 hover:text-cyan-500"
              >
                Prendre un rendez-vous
              </a>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Heure</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lien Meet</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {appointments.map((appointment) => (
                    <tr key={appointment.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <span className="font-medium text-gray-900">{appointment.service_type}</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(appointment.preferred_date).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">{appointment.preferred_time}</td>
                      <td className="px-6 py-4">{getStatusBadge(appointment.status)}</td>
                      <td className="px-6 py-4">
                        {appointment.meet_link ? (
                          <a
                            href={appointment.meet_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-cyan-600 hover:text-cyan-500"
                          >
                            Rejoindre
                          </a>
                        ) : (
                          <span className="text-gray-400">-</span>
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

export default MyAppointments;
