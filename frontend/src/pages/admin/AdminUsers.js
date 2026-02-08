import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ role: '', is_active: '' });

  useEffect(() => {
    loadUsers();
  }, [filter]);

  const loadUsers = async () => {
    try {
      let url = '/admin/users?';
      if (filter.role) url += `role=${filter.role}&`;
      if (filter.is_active !== '') url += `is_active=${filter.is_active}`;
      const response = await api.get(url);
      setUsers(response.data);
    } catch (err) {
      console.error('Error loading users:', err);
    }
    setLoading(false);
  };

  const handleChangeRole = async (userId, newRole) => {
    try {
      await api.patch(`/admin/users/${userId}/role?new_role=${newRole}`);
      loadUsers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la mise à jour');
    }
  };

  const handleToggleStatus = async (userId, isActive) => {
    try {
      await api.patch(`/admin/users/${userId}/status?is_active=${!isActive}`);
      loadUsers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la mise à jour');
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Voulez-vous vraiment supprimer cet utilisateur ?')) return;

    try {
      await api.delete(`/admin/users/${userId}`);
      loadUsers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const getRoleBadge = (role) => {
    const styles = {
      'PARTICULIER': 'bg-blue-100 text-blue-800',
      'PROFESSIONNEL': 'bg-purple-100 text-purple-800',
      'ADMIN': 'bg-red-100 text-red-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[role]}`}>
        {role}
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
        <h1 className="text-2xl font-bold text-gray-900">Gestion des Utilisateurs</h1>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 flex gap-4">
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
            value={filter.role}
            onChange={(e) => setFilter({ ...filter, role: e.target.value })}
          >
            <option value="">Tous les rôles</option>
            <option value="PARTICULIER">Particulier</option>
            <option value="PROFESSIONNEL">Professionnel</option>
            <option value="ADMIN">Admin</option>
          </select>
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
            value={filter.is_active}
            onChange={(e) => setFilter({ ...filter, is_active: e.target.value })}
          >
            <option value="">Tous les statuts</option>
            <option value="true">Actifs</option>
            <option value="false">Désactivés</option>
          </select>
        </div>

        {/* Users table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Utilisateur</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rôle</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 flex items-center justify-center text-white font-bold">
                          {user.full_name?.charAt(0).toUpperCase()}
                        </div>
                        <div className="ml-3">
                          <p className="font-medium text-gray-900">{user.full_name}</p>
                          <p className="text-sm text-gray-500">{user.phone || '-'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{user.email}</td>
                    <td className="px-6 py-4">
                      <select
                        value={user.role}
                        onChange={(e) => handleChangeRole(user.id, e.target.value)}
                        className="text-xs border border-gray-300 rounded px-2 py-1"
                      >
                        <option value="PARTICULIER">Particulier</option>
                        <option value="PROFESSIONNEL">Professionnel</option>
                        <option value="ADMIN">Admin</option>
                      </select>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleToggleStatus(user.id, user.is_active)}
                        className={`px-2 py-1 text-xs font-medium rounded-full ${
                          user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {user.is_active ? 'Actif' : 'Désactivé'}
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleDelete(user.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminUsers;
