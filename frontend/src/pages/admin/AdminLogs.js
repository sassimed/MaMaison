import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { 
  AlertTriangle, AlertCircle, AlertOctagon, Info, CheckCircle, XCircle,
  RefreshCw, Filter, Search, Clock, Monitor, Globe, User, ChevronDown,
  ChevronRight, Bell, BellOff, Trash2, Check, Eye, TrendingUp, Server,
  Smartphone, Code, Zap
} from 'lucide-react';

const AdminLogs = () => {
  const [errors, setErrors] = useState([]);
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dateRange, setDateRange] = useState('24h');
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Selected error for detail view
  const [selectedError, setSelectedError] = useState(null);

  // Load summary and alerts
  const loadSummary = useCallback(async () => {
    try {
      const [summaryRes, alertsRes] = await Promise.all([
        api.get(`/logs/admin/errors/summary?range=${dateRange}`),
        api.get('/logs/admin/alerts')
      ]);
      setSummary(summaryRes.data);
      setAlerts(alertsRes.data.alerts || []);
    } catch (error) {
      console.error('Error loading summary:', error);
    }
  }, [dateRange]);

  // Load errors list
  const loadErrors = useCallback(async () => {
    try {
      let url = `/logs/admin/errors?range=${dateRange}&page=${page}&limit=50`;
      if (statusFilter) url += `&status=${statusFilter}`;
      if (severityFilter) url += `&severity=${severityFilter}`;
      if (typeFilter) url += `&error_type=${typeFilter}`;
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
      
      const res = await api.get(url);
      setErrors(res.data.errors || []);
      setTotalPages(res.data.total_pages || 1);
    } catch (error) {
      console.error('Error loading errors:', error);
    }
  }, [dateRange, page, statusFilter, severityFilter, typeFilter, searchQuery]);

  // Initial load
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await Promise.all([loadSummary(), loadErrors()]);
      setLoading(false);
    };
    load();
    
    // Auto-refresh alerts every 30 seconds
    const interval = setInterval(loadSummary, 30000);
    return () => clearInterval(interval);
  }, [loadSummary, loadErrors]);

  // Reload errors when filters change
  useEffect(() => {
    loadErrors();
  }, [loadErrors]);

  // Update error status
  const updateErrorStatus = async (errorId, status, notes = '') => {
    try {
      await api.put(`/logs/admin/errors/${errorId}/status`, { status, notes });
      loadErrors();
      loadSummary();
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  // Delete error
  const deleteError = async (errorId) => {
    if (!window.confirm('Supprimer cette erreur ?')) return;
    try {
      await api.delete(`/logs/admin/errors/${errorId}`);
      loadErrors();
      loadSummary();
    } catch (error) {
      console.error('Error deleting:', error);
    }
  };

  // Resolve all errors
  const resolveAll = async () => {
    if (!window.confirm('Marquer toutes les erreurs comme résolues ?')) return;
    try {
      await api.post('/logs/admin/errors/resolve-all');
      loadErrors();
      loadSummary();
    } catch (error) {
      console.error('Error resolving all:', error);
    }
  };

  // Severity badge
  const SeverityBadge = ({ severity }) => {
    const styles = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-blue-100 text-blue-800 border-blue-200'
    };
    const icons = {
      critical: <AlertOctagon className="w-3 h-3" />,
      high: <AlertTriangle className="w-3 h-3" />,
      medium: <AlertCircle className="w-3 h-3" />,
      low: <Info className="w-3 h-3" />
    };
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${styles[severity] || styles.medium}`}>
        {icons[severity]}
        {severity?.toUpperCase()}
      </span>
    );
  };

  // Status badge
  const StatusBadge = ({ status }) => {
    const styles = {
      new: 'bg-red-500 text-white',
      acknowledged: 'bg-yellow-500 text-white',
      investigating: 'bg-blue-500 text-white',
      resolved: 'bg-green-500 text-white',
      ignored: 'bg-gray-400 text-white'
    };
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[status] || styles.new}`}>
        {status?.toUpperCase()}
      </span>
    );
  };

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('fr-FR', {
      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <AlertTriangle className="w-7 h-7 text-red-500" />
            Logs & Erreurs
          </h1>
          
          <div className="flex items-center gap-2">
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
              data-testid="date-range-select"
            >
              <option value="1h">Dernière heure</option>
              <option value="24h">24 dernières heures</option>
              <option value="7d">7 derniers jours</option>
              <option value="30d">30 derniers jours</option>
            </select>
            <button
              onClick={() => { loadSummary(); loadErrors(); }}
              className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50"
              data-testid="refresh-btn"
            >
              <RefreshCw className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Alerts Banner */}
        {alerts.length > 0 && (
          <div className="space-y-2" data-testid="alerts-banner">
            {alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl flex items-center gap-4 ${
                  alert.type === 'critical' ? 'bg-red-500 text-white' :
                  alert.type === 'danger' ? 'bg-red-100 text-red-800 border border-red-200' :
                  alert.type === 'warning' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                  'bg-blue-100 text-blue-800 border border-blue-200'
                }`}
              >
                <div className="p-2 rounded-full bg-white/20">
                  {alert.type === 'critical' ? <AlertOctagon className="w-6 h-6" /> :
                   alert.type === 'danger' ? <AlertTriangle className="w-6 h-6" /> :
                   <AlertCircle className="w-6 h-6" />}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold">{alert.title}</h4>
                  <p className="text-sm opacity-90">{alert.message}</p>
                </div>
                <span className="text-2xl font-bold">{alert.count}</span>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm">
          <div className="border-b flex overflow-x-auto">
            {[
              { id: 'dashboard', label: 'Tableau de bord', icon: TrendingUp },
              { id: 'errors', label: 'Liste des erreurs', icon: AlertTriangle },
              { id: 'api', label: 'Erreurs API', icon: Server }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 sm:px-6 py-3 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-red-500 text-red-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
                data-testid={`tab-${tab.id}`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && summary && (
            <div className="p-6 space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-red-500 rounded-xl p-5 text-white" data-testid="stat-critical">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-red-100 text-sm">Critique</p>
                      <p className="text-3xl font-bold mt-1">{summary.summary.critical_count}</p>
                    </div>
                    <AlertOctagon className="w-10 h-10 text-red-200" />
                  </div>
                </div>
                
                <div className="bg-orange-500 rounded-xl p-5 text-white" data-testid="stat-high">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-orange-100 text-sm">Haute</p>
                      <p className="text-3xl font-bold mt-1">{summary.summary.high_count}</p>
                    </div>
                    <AlertTriangle className="w-10 h-10 text-orange-200" />
                  </div>
                </div>
                
                <div className="bg-yellow-500 rounded-xl p-5 text-white" data-testid="stat-medium">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-yellow-100 text-sm">Moyenne</p>
                      <p className="text-3xl font-bold mt-1">{summary.summary.medium_count}</p>
                    </div>
                    <AlertCircle className="w-10 h-10 text-yellow-200" />
                  </div>
                </div>
                
                <div className="bg-green-500 rounded-xl p-5 text-white" data-testid="stat-resolved">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100 text-sm">Résolues</p>
                      <p className="text-3xl font-bold mt-1">{summary.summary.resolved_count}</p>
                    </div>
                    <CheckCircle className="w-10 h-10 text-green-200" />
                  </div>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Error Types */}
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Code className="w-5 h-5" />
                    Types d'erreurs
                  </h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <div className="flex items-center gap-3">
                        <Server className="w-5 h-5 text-purple-500" />
                        <span>Erreurs API</span>
                      </div>
                      <span className="font-bold text-purple-600">{summary.summary.api_errors}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <div className="flex items-center gap-3">
                        <Code className="w-5 h-5 text-blue-500" />
                        <span>Erreurs JavaScript</span>
                      </div>
                      <span className="font-bold text-blue-600">{summary.summary.js_errors}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                      <div className="flex items-center gap-3">
                        <Zap className="w-5 h-5 text-red-500" />
                        <span>Erreurs 500</span>
                      </div>
                      <span className="font-bold text-red-600">{summary.errors_500_count}</span>
                    </div>
                  </div>
                </div>

                {/* Top Errors */}
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Top erreurs
                  </h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {(summary.top_errors || []).map((error, idx) => (
                      <div key={idx} className="flex items-center gap-3 p-3 bg-white rounded-lg">
                        <span className="w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-xs font-bold">
                          {idx + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{error._id}</p>
                          <p className="text-xs text-gray-500">{error.error_type}</p>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-red-600">{error.count}</span>
                          <SeverityBadge severity={error.severity} />
                        </div>
                      </div>
                    ))}
                    {(!summary.top_errors || summary.top_errors.length === 0) && (
                      <p className="text-center text-gray-500 py-4">Aucune erreur</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Hourly Chart */}
              {summary.hourly && summary.hourly.length > 0 && (
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Erreurs par heure</h3>
                  <div className="flex items-end gap-1 h-32 overflow-x-auto">
                    {summary.hourly.slice(-24).map((hour, idx) => {
                      const maxCount = Math.max(...summary.hourly.map(h => h.count), 1);
                      const height = Math.max((hour.count / maxCount) * 100, 5);
                      const criticalHeight = Math.max((hour.critical / maxCount) * 100, 0);
                      return (
                        <div key={idx} className="flex flex-col items-center min-w-[20px]">
                          <div className="relative w-4 bg-gray-200 rounded-t" style={{ height: `${height}%` }}>
                            <div 
                              className="absolute bottom-0 w-full bg-red-500 rounded-t"
                              style={{ height: `${criticalHeight}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-400 mt-1">
                            {hour._id?.split(' ')[1]?.slice(0, 2) || ''}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Errors List Tab */}
          {(activeTab === 'errors' || activeTab === 'api') && (
            <div className="p-6 space-y-4">
              {/* Filters */}
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-gray-400" />
                  <select
                    value={statusFilter}
                    onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
                  >
                    <option value="">Tous les statuts</option>
                    <option value="new">Nouveau</option>
                    <option value="acknowledged">Confirmé</option>
                    <option value="investigating">En cours</option>
                    <option value="resolved">Résolu</option>
                    <option value="ignored">Ignoré</option>
                  </select>
                </div>
                <select
                  value={severityFilter}
                  onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
                  className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
                >
                  <option value="">Toutes sévérités</option>
                  <option value="critical">Critique</option>
                  <option value="high">Haute</option>
                  <option value="medium">Moyenne</option>
                  <option value="low">Basse</option>
                </select>
                <div className="relative flex-1 max-w-xs">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Rechercher..."
                    value={searchQuery}
                    onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
                    className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm"
                  />
                </div>
                <button
                  onClick={resolveAll}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 flex items-center gap-2"
                >
                  <Check className="w-4 h-4" />
                  Tout résoudre
                </button>
              </div>

              {/* Errors Table */}
              <div className="overflow-x-auto">
                <table className="w-full" data-testid="errors-table">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-3 font-medium">Sévérité</th>
                      <th className="pb-3 font-medium">Message</th>
                      <th className="pb-3 font-medium">Type</th>
                      <th className="pb-3 font-medium">URL</th>
                      <th className="pb-3 font-medium">Occurrences</th>
                      <th className="pb-3 font-medium">Statut</th>
                      <th className="pb-3 font-medium">Date</th>
                      <th className="pb-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {errors.map((error, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3">
                          <SeverityBadge severity={error.severity} />
                        </td>
                        <td className="py-3 max-w-xs">
                          <p className="truncate font-medium" title={error.message}>
                            {error.message?.slice(0, 50)}...
                          </p>
                        </td>
                        <td className="py-3">
                          <span className="text-gray-600">{error.error_type}</span>
                        </td>
                        <td className="py-3 max-w-[150px]">
                          <p className="truncate text-gray-500 text-xs" title={error.url || error.endpoint}>
                            {error.url?.replace(/^https?:\/\/[^/]+/, '') || error.endpoint || '-'}
                          </p>
                        </td>
                        <td className="py-3">
                          <span className="font-bold text-red-600">{error.occurrence_count || 1}</span>
                        </td>
                        <td className="py-3">
                          <StatusBadge status={error.status} />
                        </td>
                        <td className="py-3 text-gray-500 text-xs">
                          {formatDate(error.created_at)}
                        </td>
                        <td className="py-3">
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => setSelectedError(error)}
                              className="p-1 hover:bg-gray-100 rounded"
                              title="Voir détails"
                            >
                              <Eye className="w-4 h-4 text-gray-500" />
                            </button>
                            {error.status !== 'resolved' && (
                              <button
                                onClick={() => updateErrorStatus(error.id, 'resolved')}
                                className="p-1 hover:bg-green-100 rounded"
                                title="Marquer résolu"
                              >
                                <Check className="w-4 h-4 text-green-500" />
                              </button>
                            )}
                            <button
                              onClick={() => deleteError(error.id)}
                              className="p-1 hover:bg-red-100 rounded"
                              title="Supprimer"
                            >
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {errors.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-300" />
                  <p>Aucune erreur trouvée</p>
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex justify-center gap-2 pt-4">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border rounded-lg text-sm disabled:opacity-50"
                  >
                    Précédent
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-600">
                    Page {page} / {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="px-3 py-1 border rounded-lg text-sm disabled:opacity-50"
                  >
                    Suivant
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Error Detail Modal */}
        {selectedError && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
              <div className="p-6 border-b flex items-center justify-between">
                <h3 className="text-lg font-semibold">Détails de l'erreur</h3>
                <button onClick={() => setSelectedError(null)} className="p-2 hover:bg-gray-100 rounded-full">
                  <XCircle className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex gap-4">
                  <SeverityBadge severity={selectedError.severity} />
                  <StatusBadge status={selectedError.status} />
                </div>
                
                <div>
                  <label className="text-sm text-gray-500">Message</label>
                  <p className="font-medium mt-1">{selectedError.message}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">Type</label>
                    <p className="mt-1">{selectedError.error_type}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Occurrences</label>
                    <p className="mt-1 font-bold text-red-600">{selectedError.occurrence_count || 1}</p>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm text-gray-500">URL</label>
                  <p className="mt-1 text-sm break-all">{selectedError.url || selectedError.endpoint || '-'}</p>
                </div>
                
                {selectedError.stack_trace && (
                  <div>
                    <label className="text-sm text-gray-500">Stack Trace</label>
                    <pre className="mt-1 p-3 bg-gray-900 text-green-400 text-xs rounded-lg overflow-x-auto">
                      {selectedError.stack_trace}
                    </pre>
                  </div>
                )}
                
                <div>
                  <label className="text-sm text-gray-500">User Agent</label>
                  <p className="mt-1 text-sm text-gray-600">{selectedError.user_agent || '-'}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">Créé le</label>
                    <p className="mt-1">{formatDate(selectedError.created_at)}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Dernière occurrence</label>
                    <p className="mt-1">{formatDate(selectedError.last_occurrence)}</p>
                  </div>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t">
                  <select
                    defaultValue={selectedError.status}
                    onChange={(e) => updateErrorStatus(selectedError.id, e.target.value)}
                    className="px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="new">Nouveau</option>
                    <option value="acknowledged">Confirmé</option>
                    <option value="investigating">En cours</option>
                    <option value="resolved">Résolu</option>
                    <option value="ignored">Ignoré</option>
                  </select>
                  <button
                    onClick={() => { deleteError(selectedError.id); setSelectedError(null); }}
                    className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600"
                  >
                    Supprimer
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AdminLogs;
