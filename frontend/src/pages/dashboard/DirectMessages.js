import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { MessageSquare, Send, User, Briefcase, FileText, ArrowLeft, Loader2, Search } from 'lucide-react';

const DirectMessages = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [conversationData, setConversationData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [mobileShowMessages, setMobileShowMessages] = useState(false);

  // Get current user from localStorage
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    loadConversations();
    
    // Check if we should open a specific conversation
    const convId = searchParams.get('conversation');
    if (convId) {
      loadMessages(convId);
    }
  }, [searchParams]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Poll for new messages every 5 seconds
  useEffect(() => {
    if (!selectedConversation) return;
    
    const interval = setInterval(() => {
      loadMessages(selectedConversation, true);
    }, 5000);
    
    return () => clearInterval(interval);
  }, [selectedConversation]);

  const loadConversations = async () => {
    try {
      const response = await api.get('/direct-messages/conversations');
      setConversations(response.data);
    } catch (err) {
      console.error('Error loading conversations:', err);
    }
    setLoading(false);
  };

  const loadMessages = async (conversationId, silent = false) => {
    if (!silent) {
      setMessagesLoading(true);
    }
    
    try {
      const response = await api.get(`/direct-messages/conversation/${conversationId}`);
      setMessages(response.data.messages);
      setConversationData(response.data.conversation);
      setSelectedConversation(conversationId);
      setMobileShowMessages(true);
      
      // Refresh conversation list to update unread counts
      if (!silent) {
        loadConversations();
      }
    } catch (err) {
      console.error('Error loading messages:', err);
    }
    
    if (!silent) {
      setMessagesLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedConversation) return;
    
    setSending(true);
    try {
      await api.post(`/direct-messages/conversation/${selectedConversation}/send`, {
        content: newMessage
      });
      setNewMessage('');
      loadMessages(selectedConversation, true);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'envoi');
    }
    setSending(false);
  };

  const getRoleIcon = (role) => {
    if (role === 'PROFESSIONNEL') return <Briefcase className="w-4 h-4 text-purple-500" />;
    if (role === 'ADMIN') return <User className="w-4 h-4 text-red-500" />;
    return <User className="w-4 h-4 text-cyan-500" />;
  };

  const getRoleBadge = (role) => {
    if (role === 'PROFESSIONNEL') return 'bg-purple-100 text-purple-700';
    if (role === 'ADMIN') return 'bg-red-100 text-red-700';
    return 'bg-cyan-100 text-cyan-700';
  };

  const formatTime = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'À l\'instant';
    if (diff < 3600000) return `Il y a ${Math.floor(diff / 60000)} min`;
    if (diff < 86400000) return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  };

  const filteredConversations = conversations.filter(conv =>
    conv.other_user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (conv.annonce_title && conv.annonce_title.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="h-[calc(100vh-180px)] md:h-[calc(100vh-120px)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900">Messages</h1>
        </div>

        {/* Main container */}
        <div className="flex-1 bg-white rounded-xl shadow-sm overflow-hidden flex">
          {/* Conversations list - hidden on mobile when viewing messages */}
          <div className={`w-full md:w-80 lg:w-96 border-r flex flex-col ${mobileShowMessages ? 'hidden md:flex' : 'flex'}`}>
            {/* Search */}
            <div className="p-3 border-b">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  data-testid="message-search-input"
                />
              </div>
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto">
              {filteredConversations.length === 0 ? (
                <div className="p-6 text-center text-gray-500">
                  <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p className="font-medium">Aucune conversation</p>
                  <p className="text-sm mt-1">Vos discussions avec les professionnels apparaîtront ici</p>
                </div>
              ) : (
                filteredConversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => loadMessages(conv.id)}
                    className={`w-full p-4 text-left hover:bg-gray-50 transition-colors border-b ${
                      selectedConversation === conv.id ? 'bg-cyan-50 border-l-4 border-l-cyan-500' : ''
                    }`}
                    data-testid={`conversation-${conv.id}`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Avatar */}
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
                        {conv.other_user_name.charAt(0).toUpperCase()}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900 truncate">
                            {conv.other_user_name}
                          </span>
                          {conv.unread_count > 0 && (
                            <span className="ml-2 px-2 py-0.5 text-xs bg-cyan-500 text-white rounded-full">
                              {conv.unread_count}
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-1 mt-0.5">
                          {getRoleIcon(conv.other_user_role)}
                          <span className={`text-xs px-1.5 py-0.5 rounded ${getRoleBadge(conv.other_user_role)}`}>
                            {conv.other_user_role === 'PROFESSIONNEL' ? 'Pro' : conv.other_user_role === 'ADMIN' ? 'Admin' : 'Client'}
                          </span>
                        </div>
                        
                        {conv.annonce_title && (
                          <div className="flex items-center gap-1 mt-1 text-xs text-purple-600">
                            <FileText className="w-3 h-3" />
                            <span className="truncate">{conv.annonce_title}</span>
                          </div>
                        )}
                        
                        <p className="text-sm text-gray-500 truncate mt-1">
                          {conv.last_message || 'Nouvelle conversation'}
                        </p>
                        
                        <p className="text-xs text-gray-400 mt-1">
                          {formatTime(conv.last_message_at)}
                        </p>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Messages area */}
          <div className={`flex-1 flex flex-col ${!mobileShowMessages ? 'hidden md:flex' : 'flex'}`}>
            {selectedConversation && conversationData ? (
              <>
                {/* Conversation header */}
                <div className="p-4 border-b bg-gray-50 flex items-center gap-3">
                  <button 
                    onClick={() => setMobileShowMessages(false)}
                    className="md:hidden p-1 hover:bg-gray-200 rounded"
                  >
                    <ArrowLeft className="w-5 h-5" />
                  </button>
                  
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white font-semibold">
                    {conversationData.other_user_name.charAt(0).toUpperCase()}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">
                        {conversationData.other_user_name}
                      </h3>
                      <span className={`text-xs px-2 py-0.5 rounded ${getRoleBadge(conversationData.other_user_role)}`}>
                        {conversationData.other_user_role === 'PROFESSIONNEL' ? 'Professionnel' : 
                         conversationData.other_user_role === 'ADMIN' ? 'Admin' : 'Client'}
                      </span>
                    </div>
                    
                    {conversationData.annonce_title && (
                      <p className="text-sm text-purple-600 flex items-center gap-1">
                        <FileText className="w-3 h-3" />
                        {conversationData.annonce_title}
                      </p>
                    )}
                  </div>
                  
                  {conversationData.annonce_id && (
                    <button
                      onClick={() => navigate(`/dashboard/annonces/${conversationData.annonce_id}`)}
                      className="text-sm text-cyan-600 hover:text-cyan-700"
                    >
                      Voir l'annonce
                    </button>
                  )}
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messagesLoading ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin text-cyan-500" />
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <p>Commencez la conversation !</p>
                    </div>
                  ) : (
                    messages.map((msg) => {
                      const isMe = msg.sender_id === currentUser.id;
                      return (
                        <div
                          key={msg.id}
                          className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}
                        >
                          <div className={`max-w-[75%] ${isMe ? 'order-2' : ''}`}>
                            <div
                              className={`px-4 py-2 rounded-2xl ${
                                isMe
                                  ? 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-br-md'
                                  : 'bg-gray-100 text-gray-900 rounded-bl-md'
                              }`}
                            >
                              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            </div>
                            <p className={`text-xs text-gray-400 mt-1 ${isMe ? 'text-right' : ''}`}>
                              {formatTime(msg.created_at)}
                              {isMe && msg.is_read && (
                                <span className="ml-1 text-cyan-500">✓✓</span>
                              )}
                            </p>
                          </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Message input */}
                <form onSubmit={handleSendMessage} className="p-4 border-t bg-gray-50">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Écrivez votre message..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      className="flex-1 px-4 py-2 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      disabled={sending}
                      data-testid="message-input"
                    />
                    <button
                      type="submit"
                      disabled={sending || !newMessage.trim()}
                      className="p-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-full hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                      data-testid="send-message-btn"
                    >
                      {sending ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <Send className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p className="font-medium">Sélectionnez une conversation</p>
                  <p className="text-sm mt-1">ou démarrez une nouvelle discussion depuis une annonce</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DirectMessages;
