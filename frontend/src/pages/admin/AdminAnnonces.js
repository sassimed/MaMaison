import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { Megaphone, Clock, CheckCircle, XCircle, Award, Lock, Trash2, Filter, MapPin, User, MessageSquare } from 'lucide-react';

function AdminAnnonces() {
  var [annonces, setAnnonces] = useState([]);
  var [stats, setStats] = useState(null);
  var [loading, setLoading] = useState(true);
  var [statusFilter, setStatusFilter] = useState('');
  var [actionLoading, setActionLoading] = useState(false);

  useEffect(function() {
    loadData();
  }, [statusFilter]);

  async function loadData() {
    setLoading(true);
    try {
      var params = statusFilter ? '?status_filter=' + statusFilter : '';
      var annoncesRes = await api.get('/annonces/admin/all' + params);
      var statsRes = await api.get('/annonces/admin/stats');
      setAnnonces(annoncesRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
    setLoading(false);
  }

  async function validateAnnonce(annonceId) {
    setActionLoading(true);
    try {
      await api.post('/annonces/admin/' + annonceId + '/validate');
      alert('Annonce validée et publiée');
      loadData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur');
    }
    setActionLoading(false);
  }

  async function rejectAnnonce(annonceId) {
    var reason = window.prompt('Raison du refus (optionnel):');
    if (reason === null) return;
    
    setActionLoading(true);
    try {
      await api.post('/annonces/admin/' + annonceId + '/reject?reason=' + encodeURIComponent(reason));
      alert('Annonce refusée');
      loadData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur');
    }
    setActionLoading(false);
  }

  async function deleteAnnonce(annonceId) {
    if (!window.confirm('Supprimer cette annonce ?')) return;
    
    setActionLoading(true);
    try {
      await api.delete('/annonces/admin/' + annonceId);
      alert('Annonce supprimée');
      loadData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur');
    }
    setActionLoading(false);
  }

  function formatDate(d) {
    return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function getStatusBadge(status) {
    var styles = {
      'EN_ATTENTE': 'bg-yellow-100 text-yellow-800',
      'PUBLIEE': 'bg-green-100 text-green-800',
      'REFUSEE': 'bg-red-100 text-red-800',
      'ATTRIBUEE': 'bg-purple-100 text-purple-800',
      'CLOTUREE': 'bg-gray-100 text-gray-800'
    };
    var labels = {
      'EN_ATTENTE': 'En attente',
      'PUBLIEE': 'Publiée',
      'REFUSEE': 'Refusée',
      'ATTRIBUEE': 'Attribuée',
      'CLOTUREE': 'Clôturée'
    };
    return (
      <span className={'px-2 py-1 rounded-full text-xs font-medium ' + (styles[status] || 'bg-gray-100')}>
        {labels[status] || status}
      </span>
    );
  }

  if (loading && !stats) {
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
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Megaphone className="w-7 h-7 text-cyan-500" />
            Gestion des Annonces
          </h1>
          <p className="text-gray-500 mt-1">Modérez les annonces des clients</p>
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="bg-white rounded-xl shadow-sm p-4 text-center">
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-xs text-gray-500">Total</p>
            </div>
            <div className="bg-yellow-50 rounded-xl p-4 text-center border border-yellow-200">
              <p className="text-2xl font-bold text-yellow-700">{stats.pending}</p>
              <p className="text-xs text-yellow-600">En attente</p>
            </div>
            <div className="bg-green-50 rounded-xl p-4 text-center border border-green-200">
              <p className="text-2xl font-bold text-green-700">{stats.published}</p>
              <p className="text-xs text-green-600">Publiées</p>
            </div>
            <div className="bg-purple-50 rounded-xl p-4 text-center border border-purple-200">
              <p className="text-2xl font-bold text-purple-700">{stats.attributed}</p>
              <p className="text-xs text-purple-600">Attribuées</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 text-center border border-gray-200">
              <p className="text-2xl font-bold text-gray-700">{stats.closed}</p>
              <p className="text-xs text-gray-600">Clôturées</p>
            </div>
            <div className="bg-red-50 rounded-xl p-4 text-center border border-red-200">
              <p className="text-2xl font-bold text-red-700">{stats.rejected}</p>
              <p className="text-xs text-red-600">Refusées</p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-gray-500" />
            <select
              value={statusFilter}
              onChange={function(e) { setStatusFilter(e.target.value); }}
              className="px-4 py-2 border border-gray-200 rounded-lg"
              data-testid="admin-status-filter"
            >
              <option value="">Tous les statuts</option>
              <option value="EN_ATTENTE">En attente</option>
              <option value="PUBLIEE">Publiées</option>
              <option value="ATTRIBUEE">Attribuées</option>
              <option value="CLOTUREE">Clôturées</option>
              <option value="REFUSEE">Refusées</option>
            </select>
          </div>
        </div>

        {annonces.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Megaphone className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Aucune annonce</h2>
            <p className="text-gray-500">
              {statusFilter ? 'Aucune annonce avec ce statut' : 'Aucune annonce créée'}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Annonce</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Réponses</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {annonces.map(function(annonce) {
                  return (
                    <tr key={annonce.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <div className="font-medium text-gray-900 truncate max-w-xs">{annonce.title}</div>
                        <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                          <span className="px-2 py-0.5 bg-cyan-100 text-cyan-700 rounded">{annonce.category}</span>
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {annonce.city}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm">{annonce.client_name}</div>
                        <div className="text-xs text-gray-500">{annonce.client_email}</div>
                      </td>
                      <td className="px-4 py-4">
                        {getStatusBadge(annonce.status)}
                      </td>
                      <td className="px-4 py-4">
                        <span className="flex items-center gap-1 text-sm text-gray-600">
                          <MessageSquare className="w-4 h-4" />
                          {(annonce.responses || []).length}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">
                        {formatDate(annonce.created_at)}
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center justify-end gap-2">
                          {annonce.status === 'EN_ATTENTE' && (
                            <>
                              <button
                                onClick={function() { validateAnnonce(annonce.id); }}
                                disabled={actionLoading}
                                className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600 disabled:opacity-50"
                                data-testid={'validate-' + annonce.id}
                              >
                                Valider
                              </button>
                              <button
                                onClick={function() { rejectAnnonce(annonce.id); }}
                                disabled={actionLoading}
                                className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600 disabled:opacity-50"
                                data-testid={'reject-' + annonce.id}
                              >
                                Refuser
                              </button>
                            </>
                          )}
                          <button
                            onClick={function() { deleteAnnonce(annonce.id); }}
                            disabled={actionLoading}
                            className="p-1 text-red-500 hover:bg-red-50 rounded"
                            data-testid={'delete-' + annonce.id}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default AdminAnnonces;
