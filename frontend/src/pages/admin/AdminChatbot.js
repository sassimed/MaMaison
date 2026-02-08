import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  MessageCircle, Users, TrendingUp, Clock, 
  ArrowLeft, RefreshCw, Trash2, Eye, Download,
  BarChart3, MessageSquare, Calendar, Globe,
  Bot, Cpu, Check, Settings
} from 'lucide-react';
import api from '../../services/api';

const AdminChatbot = () => {
  const [stats, setStats] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('7d');
  
  // AI Model settings
  const [aiModels, setAiModels] = useState(null);
  const [currentModel, setCurrentModel] = useState('');
  const [changingModel, setChangingModel] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchConversations();
    fetchAiModels();
  }, [dateRange]);

  const fetchStats = async () => {
    try {
      const response = await api.get(`/chatbot/admin/stats?range=${dateRange}`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchConversations = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/chatbot/admin/conversations?range=${dateRange}`);
      setConversations(response.data.conversations || []);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAiModels = async () => {
    try {
      const response = await api.get('/chatbot/admin/ai-models');
      setAiModels(response.data.models_details || {});
      setCurrentModel(response.data.current_model || 'gpt-5.2');
    } catch (error) {
      console.error('Error fetching AI models:', error);
    }
  };

  const changeAiModel = async (modelId) => {
    setChangingModel(true);
    try {
      await api.post('/chatbot/admin/ai-model', { model_id: modelId });
      setCurrentModel(modelId);
    } catch (error) {
      console.error('Error changing model:', error);
      alert('Erreur lors du changement de modèle');
    } finally {
      setChangingModel(false);
    }
  };

  const viewConversation = async (sessionId) => {
    try {
      const response = await api.get(`/chatbot/history/${sessionId}`);
      setSelectedConversation({
        session_id: sessionId,
        messages: response.data.messages || []
      });
    } catch (error) {
      console.error('Error fetching conversation:', error);
    }
  };

  const deleteConversation = async (sessionId) => {
    if (!window.confirm('Supprimer cette conversation ?')) return;
    try {
      await api.delete(`/chatbot/history/${sessionId}`);
      setConversations(prev => prev.filter(c => c.session_id !== sessionId));
      if (selectedConversation?.session_id === sessionId) {
        setSelectedConversation(null);
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { 
      day: '2-digit', 
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const detectLanguage = (messages) => {
    if (!messages || messages.length === 0) return 'FR';
    const text = messages.map(m => m.content).join(' ');
    const arabicPattern = /[\u0600-\u06FF]/;
    return arabicPattern.test(text) ? 'AR 🇹🇳' : 'FR 🇫🇷';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/dashboard" className="p-2 hover:bg-gray-100 rounded-lg">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <MessageCircle className="w-6 h-6 text-purple-600" />
                  Statistiques Chatbot
                </h1>
                <p className="text-sm text-gray-500">Assistant MyDar - Analytics</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm"
              >
                <option value="1d">Aujourd'hui</option>
                <option value="7d">7 derniers jours</option>
                <option value="30d">30 derniers jours</option>
                <option value="all">Tout</option>
              </select>
              <button
                onClick={() => { fetchStats(); fetchConversations(); }}
                className="p-2 hover:bg-gray-100 rounded-lg"
                title="Rafraîchir"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <MessageSquare className="w-6 h-6 text-purple-600" />
                </div>
                <span className="text-gray-500 text-sm">Conversations</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats.total_conversations || 0}</p>
              <p className="text-sm text-green-600 mt-1">+{stats.new_today || 0} aujourd'hui</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-cyan-100 rounded-lg">
                  <BarChart3 className="w-6 h-6 text-cyan-600" />
                </div>
                <span className="text-gray-500 text-sm">Messages Total</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats.total_messages || 0}</p>
              <p className="text-sm text-gray-500 mt-1">
                ~{stats.avg_messages_per_conv || 0} msg/conv
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-green-100 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
                <span className="text-gray-500 text-sm">Coût Estimé</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {((stats.total_messages || 0) * 0.002).toFixed(3)} DT
              </p>
              <p className="text-sm text-gray-500 mt-1">~0.002 DT/message</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-orange-100 rounded-lg">
                  <Globe className="w-6 h-6 text-orange-600" />
                </div>
                <span className="text-gray-500 text-sm">Langues</span>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-xl font-bold text-gray-900">{stats.french_pct || 0}%</p>
                  <p className="text-xs text-gray-500">Français</p>
                </div>
                <div>
                  <p className="text-xl font-bold text-gray-900">{stats.arabic_pct || 0}%</p>
                  <p className="text-xs text-gray-500">Arabe</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversations List */}
          <div className="bg-white rounded-xl shadow-sm border">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Conversations Récentes</h2>
              <span className="text-sm text-gray-500">{conversations.length} total</span>
            </div>
            <div className="divide-y max-h-[500px] overflow-y-auto">
              {loading ? (
                <div className="p-8 text-center text-gray-500">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                  Chargement...
                </div>
              ) : conversations.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <MessageCircle className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  Aucune conversation
                </div>
              ) : (
                conversations.map((conv) => (
                  <div
                    key={conv.session_id}
                    className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                      selectedConversation?.session_id === conv.session_id ? 'bg-purple-50' : ''
                    }`}
                    onClick={() => viewConversation(conv.session_id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-mono text-gray-400">
                            {conv.session_id.slice(0, 12)}...
                          </span>
                          <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                            {conv.language || 'FR 🇫🇷'}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 truncate">
                          {conv.last_message || 'Pas de message'}
                        </p>
                        <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <MessageSquare className="w-3 h-3" />
                            {conv.message_count || 0} msg
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDate(conv.last_activity)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 ml-2">
                        <button
                          onClick={(e) => { e.stopPropagation(); viewConversation(conv.session_id); }}
                          className="p-1.5 hover:bg-gray-200 rounded"
                          title="Voir"
                        >
                          <Eye className="w-4 h-4 text-gray-500" />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); deleteConversation(conv.session_id); }}
                          className="p-1.5 hover:bg-red-100 rounded"
                          title="Supprimer"
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Conversation Detail */}
          <div className="bg-white rounded-xl shadow-sm border">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-gray-900">Détail Conversation</h2>
            </div>
            <div className="h-[500px] overflow-y-auto p-4">
              {selectedConversation ? (
                <div className="space-y-3">
                  <div className="text-xs text-gray-500 text-center mb-4">
                    Session: {selectedConversation.session_id}
                  </div>
                  {selectedConversation.messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[85%] px-4 py-2 rounded-xl text-sm ${
                          msg.role === 'user'
                            ? 'bg-purple-600 text-white rounded-br-none'
                            : 'bg-gray-100 text-gray-800 rounded-bl-none'
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                        {msg.timestamp && (
                          <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-purple-200' : 'text-gray-400'}`}>
                            {formatDate(msg.timestamp)}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Eye className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>Sélectionnez une conversation</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* AI Model Selection Panel */}
        <div className="mt-6 bg-white rounded-xl p-6 shadow-sm border" data-testid="ai-model-settings">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5 text-purple-600" />
            Configuration du Modèle IA
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Model Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Modèle actif du chatbot
              </label>
              <div className="relative">
                <select
                  value={currentModel}
                  onChange={(e) => changeAiModel(e.target.value)}
                  disabled={changingModel}
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg appearance-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white disabled:bg-gray-100 disabled:cursor-not-allowed"
                  data-testid="ai-model-select"
                >
                  {aiModels && Object.entries(aiModels).map(([modelId, details]) => (
                    <option key={modelId} value={modelId}>
                      {modelId} — {details.provider} ({details.model})
                    </option>
                  ))}
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  {changingModel ? (
                    <RefreshCw className="w-5 h-5 text-purple-500 animate-spin" />
                  ) : (
                    <Cpu className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>
              {changingModel && (
                <p className="text-sm text-purple-600 mt-2 flex items-center gap-1">
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  Changement en cours...
                </p>
              )}
              {!changingModel && currentModel && (
                <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
                  <Check className="w-4 h-4" />
                  Modèle actif: <span className="font-medium">{currentModel}</span>
                </p>
              )}
            </div>
            
            {/* Model Info */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <Bot className="w-4 h-4" />
                Modèles disponibles
              </h4>
              <ul className="space-y-1 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  <strong>GPT-5.2</strong> — Meilleure qualité (recommandé)
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  <strong>GPT-4o</strong> — Rapide et efficace
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                  <strong>Gemini 2/3</strong> — Alternative économique
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                  <strong>Claude Sonnet</strong> — Bon pour les conversations
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Cost Info Box */}
        <div className="mt-6 bg-gradient-to-r from-purple-50 to-cyan-50 rounded-xl p-6 border border-purple-100">
          <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-purple-600" />
            Information Facturation
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Modèle utilisé</p>
              <p className="font-medium">{currentModel || 'GPT-5.2'}</p>
            </div>
            <div>
              <p className="text-gray-500">Coût par message</p>
              <p className="font-medium">~0.001-0.003 DT</p>
            </div>
            <div>
              <p className="text-gray-500">Gérer votre solde</p>
              <p className="font-medium text-purple-600">
                Profile → Universal Key → Balance
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminChatbot;
