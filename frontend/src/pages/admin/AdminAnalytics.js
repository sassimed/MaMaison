import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { 
  Activity, Users, Eye, Globe, Monitor, Smartphone, Tablet,
  Search, Clock, TrendingUp, MousePointer, Package, AlertCircle,
  RefreshCw, ChevronDown, ChevronRight, User, Calendar, Filter,
  Chrome, BarChart3, MapPin, ArrowUpRight
} from 'lucide-react';

const AdminAnalytics = () => {
  const [stats, setStats] = useState(null);
  const [onlineUsers, setOnlineUsers] = useState(null);
  const [events, setEvents] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [searchTerms, setSearchTerms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState('7d');
  
  // Events filter state
  const [eventsPage, setEventsPage] = useState(1);
  const [eventsTotal, setEventsTotal] = useState(0);
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [userIdFilter, setUserIdFilter] = useState('');
  
  // User timeline state
  const [selectedUserId, setSelectedUserId] = useState('');
  const [userTimeline, setUserTimeline] = useState(null);

  // Load overview stats
  const loadStats = useCallback(async () => {
    try {
      const res = await api.get(`/analytics/admin/stats?range=${dateRange}`);
      setStats(res.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  }, [dateRange]);

  // Load online users
  const loadOnlineUsers = useCallback(async () => {
    try {
      const res = await api.get('/analytics/admin/online-users');
      setOnlineUsers(res.data);
    } catch (error) {
      console.error('Error loading online users:', error);
    }
  }, []);

  // Load events (audit trail)
  const loadEvents = useCallback(async () => {
    try {
      let url = `/analytics/admin/events?range=${dateRange}&page=${eventsPage}&limit=50`;
      if (eventTypeFilter) url += `&event_type=${eventTypeFilter}`;
      if (userIdFilter) url += `&user_id=${userIdFilter}`;
      
      const res = await api.get(url);
      setEvents(res.data.events);
      setEventsTotal(res.data.total);
    } catch (error) {
      console.error('Error loading events:', error);
    }
  }, [dateRange, eventsPage, eventTypeFilter, userIdFilter]);

  // Load top products
  const loadTopProducts = useCallback(async () => {
    try {
      const res = await api.get(`/analytics/admin/top-products?range=${dateRange}&limit=20`);
      setTopProducts(res.data.top_products || []);
    } catch (error) {
      console.error('Error loading top products:', error);
    }
  }, [dateRange]);

  // Load search terms
  const loadSearchTerms = useCallback(async () => {
    try {
      const res = await api.get(`/analytics/admin/search-terms?range=${dateRange}&limit=20`);
      setSearchTerms(res.data.search_terms || []);
    } catch (error) {
      console.error('Error loading search terms:', error);
    }
  }, [dateRange]);

  // Load user timeline
  const loadUserTimeline = async (userId) => {
    if (!userId) {
      setUserTimeline(null);
      return;
    }
    try {
      const res = await api.get(`/analytics/admin/user-timeline/${userId}?range=30d`);
      setUserTimeline(res.data);
    } catch (error) {
      console.error('Error loading user timeline:', error);
      setUserTimeline(null);
    }
  };

  // Initial load
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await Promise.all([loadStats(), loadOnlineUsers()]);
      setLoading(false);
    };
    load();
    
    // Refresh online users every 30 seconds
    const interval = setInterval(loadOnlineUsers, 30000);
    return () => clearInterval(interval);
  }, [loadStats, loadOnlineUsers]);

  // Load tab-specific data
  useEffect(() => {
    if (activeTab === 'events') {
      loadEvents();
    } else if (activeTab === 'products') {
      loadTopProducts();
      loadSearchTerms();
    }
  }, [activeTab, loadEvents, loadTopProducts, loadSearchTerms]);

  // Refresh when date range changes
  useEffect(() => {
    loadStats();
    if (activeTab === 'events') loadEvents();
    if (activeTab === 'products') {
      loadTopProducts();
      loadSearchTerms();
    }
  }, [dateRange, loadStats, activeTab, loadEvents, loadTopProducts, loadSearchTerms]);

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  const getDeviceIcon = (type) => {
    switch (type) {
      case 'mobile': return <Smartphone className="w-4 h-4" />;
      case 'tablet': return <Tablet className="w-4 h-4" />;
      default: return <Monitor className="w-4 h-4" />;
    }
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'page_view': return <Eye className="w-4 h-4 text-blue-500" />;
      case 'product_view': return <Package className="w-4 h-4 text-purple-500" />;
      case 'search': return <Search className="w-4 h-4 text-green-500" />;
      case 'add_to_cart': return <MousePointer className="w-4 h-4 text-orange-500" />;
      case 'checkout_start': return <MousePointer className="w-4 h-4 text-yellow-500" />;
      case 'checkout_complete': return <TrendingUp className="w-4 h-4 text-emerald-500" />;
      case 'login': return <User className="w-4 h-4 text-cyan-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const eventTypes = [
    { value: '', label: 'Tous les événements' },
    { value: 'page_view', label: 'Pages vues' },
    { value: 'product_view', label: 'Vues produits' },
    { value: 'search', label: 'Recherches' },
    { value: 'add_to_cart', label: 'Ajout panier' },
    { value: 'checkout_start', label: 'Début commande' },
    { value: 'checkout_complete', label: 'Commande terminée' },
    { value: 'login', label: 'Connexions' },
    { value: 'error', label: 'Erreurs' }
  ];

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
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Activity className="w-7 h-7 text-cyan-500" />
            Analytics & Tracking
          </h1>
          
          {/* Date Range Selector */}
          <div className="flex items-center gap-2">
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              data-testid="date-range-select"
            >
              <option value="24h">Dernières 24h</option>
              <option value="7d">7 derniers jours</option>
              <option value="30d">30 derniers jours</option>
              <option value="90d">90 derniers jours</option>
            </select>
            <button
              onClick={() => {
                loadStats();
                loadOnlineUsers();
                if (activeTab === 'events') loadEvents();
                if (activeTab === 'products') { loadTopProducts(); loadSearchTerms(); }
              }}
              className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50"
              data-testid="refresh-btn"
            >
              <RefreshCw className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Online Users Banner */}
        {onlineUsers && (
          <div className="bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl p-4 text-white" data-testid="online-users-banner">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Users className="w-8 h-8" />
                  <span className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></span>
                </div>
                <div>
                  <p className="text-green-100 text-sm">Utilisateurs en ligne</p>
                  <p className="text-3xl font-bold">{onlineUsers.total_active_sessions}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-green-100 text-sm">Utilisateurs connectés</p>
                <p className="text-xl font-semibold">{onlineUsers.online_users_count}</p>
              </div>
            </div>
            
            {/* Online users list */}
            {onlineUsers.online_users.length > 0 && (
              <div className="mt-4 pt-4 border-t border-green-400/30">
                <p className="text-green-100 text-xs mb-2">Utilisateurs actifs :</p>
                <div className="flex flex-wrap gap-2">
                  {onlineUsers.online_users.slice(0, 10).map((ou, idx) => (
                    <div key={idx} className="bg-white/20 rounded-full px-3 py-1 text-sm flex items-center gap-2">
                      <span className="w-2 h-2 bg-yellow-400 rounded-full"></span>
                      <span>{ou.user_info?.full_name || ou.user_info?.email || ou.user_id}</span>
                      <span className="text-green-200 text-xs truncate max-w-[120px]">{ou.current_page}</span>
                    </div>
                  ))}
                  {onlineUsers.online_users.length > 10 && (
                    <span className="text-green-200 text-sm">+{onlineUsers.online_users.length - 10} autres</span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm">
          <div className="border-b flex overflow-x-auto">
            {[
              { id: 'overview', label: 'Vue d\'ensemble', icon: BarChart3 },
              { id: 'events', label: 'Journal d\'audit', icon: Clock },
              { id: 'products', label: 'Top Produits', icon: Package },
              { id: 'timeline', label: 'Timeline Utilisateur', icon: User }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 sm:px-6 py-3 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-cyan-500 text-cyan-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
                data-testid={`tab-${tab.id}`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && stats && (
            <div className="p-6 space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-blue-500 rounded-xl p-5 text-white" data-testid="stat-visitors">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-100 text-sm">Visiteurs uniques</p>
                      <p className="text-3xl font-bold mt-1">{formatNumber(stats.summary.unique_visitors)}</p>
                    </div>
                    <Users className="w-10 h-10 text-blue-200" />
                  </div>
                </div>
                
                <div className="bg-purple-500 rounded-xl p-5 text-white" data-testid="stat-sessions">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-100 text-sm">Sessions</p>
                      <p className="text-3xl font-bold mt-1">{formatNumber(stats.summary.unique_sessions)}</p>
                    </div>
                    <Activity className="w-10 h-10 text-purple-200" />
                  </div>
                </div>
                
                <div className="bg-cyan-500 rounded-xl p-5 text-white" data-testid="stat-pageviews">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-cyan-100 text-sm">Pages vues</p>
                      <p className="text-3xl font-bold mt-1">{formatNumber(stats.summary.page_views)}</p>
                    </div>
                    <Eye className="w-10 h-10 text-cyan-200" />
                  </div>
                </div>
                
                <div className="bg-orange-500 rounded-xl p-5 text-white" data-testid="stat-avgpages">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-orange-100 text-sm">Pages/Session</p>
                      <p className="text-3xl font-bold mt-1">{stats.summary.avg_pages_per_session}</p>
                    </div>
                    <TrendingUp className="w-10 h-10 text-orange-200" />
                  </div>
                </div>
              </div>

              {/* Daily Chart */}
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Visiteurs par jour</h3>
                {stats.daily_stats && stats.daily_stats.length > 0 ? (
                  <div className="grid grid-cols-7 gap-2">
                    {stats.daily_stats.slice(-14).map((day, idx) => {
                      const maxVisitors = Math.max(...stats.daily_stats.slice(-14).map(d => d.visitors || 0), 1);
                      const height = Math.max(((day.visitors || 0) / maxVisitors) * 100, 5);
                      return (
                        <div key={idx} className="flex flex-col items-center">
                          <div className="w-full bg-gray-200 rounded-t-lg h-24 flex items-end">
                            <div
                              className="w-full bg-cyan-500 rounded-t-lg transition-all"
                              style={{ height: `${height}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-500 mt-1">
                            {new Date(day._id).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })}
                          </span>
                          <span className="text-xs font-medium">{day.visitors}</span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">Aucune donnée pour cette période</p>
                )}
              </div>

              {/* Breakdown Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Devices */}
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Monitor className="w-5 h-5" />
                    Appareils
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(stats.devices || {}).map(([device, count]) => {
                      const total = Object.values(stats.devices || {}).reduce((a, b) => a + b, 0);
                      const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
                      return (
                        <div key={device} className="flex items-center gap-3">
                          {getDeviceIcon(device)}
                          <span className="flex-1 capitalize text-gray-700">{device}</span>
                          <span className="text-gray-500">{pct}%</span>
                          <span className="font-medium">{formatNumber(count)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Browsers */}
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Chrome className="w-5 h-5" />
                    Navigateurs
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(stats.browsers || {}).slice(0, 5).map(([browser, count]) => {
                      const total = Object.values(stats.browsers || {}).reduce((a, b) => a + b, 0);
                      const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
                      return (
                        <div key={browser} className="flex items-center gap-3">
                          <Globe className="w-4 h-4 text-gray-400" />
                          <span className="flex-1 text-gray-700">{browser}</span>
                          <span className="text-gray-500">{pct}%</span>
                          <span className="font-medium">{formatNumber(count)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Countries */}
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <MapPin className="w-5 h-5" />
                    Pays
                  </h3>
                  <div className="space-y-3">
                    {(stats.countries || []).slice(0, 5).map((item, idx) => (
                      <div key={idx} className="flex items-center gap-3">
                        <span className="text-lg">{item._id === 'Tunisia' ? '🇹🇳' : item._id === 'France' ? '🇫🇷' : '🌍'}</span>
                        <span className="flex-1 text-gray-700">{item._id || 'Inconnu'}</span>
                        <span className="font-medium">{formatNumber(item.count)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Top Pages & Traffic Sources */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Pages */}
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Eye className="w-5 h-5" />
                    Pages les plus visitées
                  </h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {(stats.top_pages || []).map((page, idx) => (
                      <div key={idx} className="flex items-center gap-3 bg-white rounded-lg p-3">
                        <span className="w-6 h-6 bg-cyan-100 text-cyan-600 rounded-full flex items-center justify-center text-xs font-bold">
                          {idx + 1}
                        </span>
                        <span className="flex-1 text-gray-700 truncate text-sm">{page._id}</span>
                        <span className="font-medium text-gray-900">{formatNumber(page.views)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Traffic Sources */}
                <div className="bg-gray-50 rounded-xl p-6">
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <ArrowUpRight className="w-5 h-5" />
                    Sources de trafic
                  </h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {(stats.traffic_sources || []).map((source, idx) => (
                      <div key={idx} className="flex items-center gap-3 bg-white rounded-lg p-3">
                        <span className="w-6 h-6 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-xs font-bold">
                          {idx + 1}
                        </span>
                        <span className="flex-1 text-gray-700 capitalize">{source._id || 'direct'}</span>
                        <span className="font-medium text-gray-900">{formatNumber(source.visits)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Events Tab (Audit Trail) */}
          {activeTab === 'events' && (
            <div className="p-6 space-y-4">
              {/* Filters */}
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-gray-400" />
                  <select
                    value={eventTypeFilter}
                    onChange={(e) => { setEventTypeFilter(e.target.value); setEventsPage(1); }}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    data-testid="event-type-filter"
                  >
                    {eventTypes.map(et => (
                      <option key={et.value} value={et.value}>{et.label}</option>
                    ))}
                  </select>
                </div>
                <input
                  type="text"
                  placeholder="Filtrer par User ID..."
                  value={userIdFilter}
                  onChange={(e) => { setUserIdFilter(e.target.value); setEventsPage(1); }}
                  className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 w-48"
                  data-testid="user-id-filter"
                />
                <span className="text-sm text-gray-500">{eventsTotal} événements</span>
              </div>

              {/* Events Table */}
              <div className="overflow-x-auto">
                <table className="w-full" data-testid="events-table">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-3 font-medium">Type</th>
                      <th className="pb-3 font-medium">Utilisateur</th>
                      <th className="pb-3 font-medium">Page</th>
                      <th className="pb-3 font-medium">Détails</th>
                      <th className="pb-3 font-medium">Appareil</th>
                      <th className="pb-3 font-medium">Date</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {events.map((event, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            {getEventIcon(event.event_type)}
                            <span className="capitalize">{event.event_type.replace('_', ' ')}</span>
                          </div>
                        </td>
                        <td className="py-3">
                          {event.user_id ? (
                            <button
                              onClick={() => {
                                setSelectedUserId(event.user_id);
                                setActiveTab('timeline');
                                loadUserTimeline(event.user_id);
                              }}
                              className="text-cyan-600 hover:underline"
                            >
                              {event.user_id.slice(0, 8)}...
                            </button>
                          ) : (
                            <span className="text-gray-400">Anonyme</span>
                          )}
                        </td>
                        <td className="py-3 max-w-xs truncate" title={event.page_url}>
                          {event.page_url?.replace(/^https?:\/\/[^/]+/, '') || '-'}
                        </td>
                        <td className="py-3">
                          {event.product_name && <span className="text-purple-600">{event.product_name}</span>}
                          {event.search_query && <span className="text-green-600">"{event.search_query}"</span>}
                          {event.event_type === 'error' && event.metadata?.error && (
                            <span className="text-red-600">{event.metadata.error}</span>
                          )}
                        </td>
                        <td className="py-3">
                          <div className="flex items-center gap-1">
                            {getDeviceIcon(event.device?.device_type)}
                            <span className="text-gray-500 text-xs">{event.device?.browser}</span>
                          </div>
                        </td>
                        <td className="py-3 text-gray-500">
                          {new Date(event.timestamp).toLocaleString('fr-FR', {
                            day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                          })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {eventsTotal > 50 && (
                <div className="flex justify-center gap-2 pt-4">
                  <button
                    onClick={() => setEventsPage(p => Math.max(1, p - 1))}
                    disabled={eventsPage === 1}
                    className="px-3 py-1 border rounded-lg text-sm disabled:opacity-50"
                  >
                    Précédent
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-600">
                    Page {eventsPage} / {Math.ceil(eventsTotal / 50)}
                  </span>
                  <button
                    onClick={() => setEventsPage(p => p + 1)}
                    disabled={eventsPage >= Math.ceil(eventsTotal / 50)}
                    className="px-3 py-1 border rounded-lg text-sm disabled:opacity-50"
                  >
                    Suivant
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Top Products Tab */}
          {activeTab === 'products' && (
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Products */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Package className="w-5 h-5 text-purple-500" />
                    Produits les plus consultés
                  </h3>
                  {topProducts.length === 0 ? (
                    <div className="text-center py-12 text-gray-500 bg-gray-50 rounded-xl">
                      <Package className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <p>Aucune donnée pour cette période</p>
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-[500px] overflow-y-auto">
                      {topProducts.map((product, idx) => (
                        <div key={idx} className="flex items-center gap-4 bg-gray-50 rounded-xl p-4">
                          <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                            {idx + 1}
                          </div>
                          <div className="w-14 h-14 bg-white rounded-lg flex-shrink-0 overflow-hidden">
                            {product.product_info?.primary_image_url ? (
                              <img
                                src={product.product_info.primary_image_url}
                                alt=""
                                className="w-full h-full object-contain"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-gray-300">
                                <Package className="w-6 h-6" />
                              </div>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-gray-900 truncate">{product.product_name}</h4>
                            <p className="text-sm text-gray-500">{product.product_info?.category_label}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-purple-600">{product.total_views} vues</p>
                            <p className="text-xs text-gray-500">{product.unique_views} uniques</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Top Search Terms */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Search className="w-5 h-5 text-green-500" />
                    Termes de recherche populaires
                  </h3>
                  {searchTerms.length === 0 ? (
                    <div className="text-center py-12 text-gray-500 bg-gray-50 rounded-xl">
                      <Search className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <p>Aucune recherche pour cette période</p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[500px] overflow-y-auto">
                      {searchTerms.map((term, idx) => (
                        <div key={idx} className="flex items-center gap-3 bg-gray-50 rounded-lg p-3">
                          <span className="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs font-bold">
                            {idx + 1}
                          </span>
                          <span className="flex-1 text-gray-700">"{term.term}"</span>
                          <span className="font-medium text-gray-900">{term.count} recherches</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* User Timeline Tab */}
          {activeTab === 'timeline' && (
            <div className="p-6 space-y-4">
              {/* User ID Input */}
              <div className="flex items-center gap-4">
                <input
                  type="text"
                  placeholder="Entrez l'ID utilisateur..."
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 w-64"
                  data-testid="timeline-user-input"
                />
                <button
                  onClick={() => loadUserTimeline(selectedUserId)}
                  className="px-4 py-2 bg-cyan-500 text-white rounded-lg text-sm hover:bg-cyan-600"
                  data-testid="load-timeline-btn"
                >
                  Charger la timeline
                </button>
              </div>

              {/* Timeline Display */}
              {userTimeline ? (
                <div className="space-y-6">
                  {/* User Info Card */}
                  {userTimeline.user && (
                    <div className="bg-gray-50 rounded-xl p-4 flex items-center gap-4">
                      <div className="w-12 h-12 bg-cyan-500 rounded-full flex items-center justify-center text-white text-xl font-bold">
                        {(userTimeline.user.full_name || userTimeline.user.email || '?')[0].toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {userTimeline.user.full_name || userTimeline.user.email}
                        </h3>
                        <p className="text-sm text-gray-500">{userTimeline.user.email}</p>
                        <p className="text-xs text-gray-400">Rôle: {userTimeline.user.role}</p>
                      </div>
                      <div className="ml-auto text-right">
                        <p className="text-2xl font-bold text-cyan-600">{userTimeline.total_events}</p>
                        <p className="text-sm text-gray-500">événements</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-purple-600">{userTimeline.session_count}</p>
                        <p className="text-sm text-gray-500">sessions</p>
                      </div>
                    </div>
                  )}

                  {/* Sessions */}
                  <div className="space-y-4">
                    {Object.entries(userTimeline.sessions || {}).map(([sessionId, sessionEvents]) => (
                      <div key={sessionId} className="bg-white border rounded-xl overflow-hidden">
                        <div className="bg-gray-50 px-4 py-2 flex items-center gap-2 border-b">
                          <Activity className="w-4 h-4 text-gray-400" />
                          <span className="text-sm font-medium text-gray-600">Session: {sessionId.slice(0, 12)}...</span>
                          <span className="text-xs text-gray-400 ml-auto">{sessionEvents.length} événements</span>
                        </div>
                        <div className="divide-y">
                          {sessionEvents.map((event, idx) => (
                            <div key={idx} className="px-4 py-3 flex items-center gap-4 hover:bg-gray-50">
                              {getEventIcon(event.event_type)}
                              <div className="flex-1">
                                <span className="text-sm font-medium capitalize">
                                  {event.event_type.replace('_', ' ')}
                                </span>
                                <p className="text-xs text-gray-500 truncate">{event.page_url}</p>
                                {event.product_name && (
                                  <p className="text-xs text-purple-600">Produit: {event.product_name}</p>
                                )}
                                {event.search_query && (
                                  <p className="text-xs text-green-600">Recherche: "{event.search_query}"</p>
                                )}
                              </div>
                              <span className="text-xs text-gray-400">
                                {new Date(event.timestamp).toLocaleString('fr-FR', {
                                  day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                                })}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-16 text-gray-500">
                  <User className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p>Entrez un ID utilisateur pour voir sa timeline d'activité</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminAnalytics;
