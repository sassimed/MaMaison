import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';

const AdminMessages = () => {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [replyContent, setReplyContent] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await api.get('/admin/messages/conversations');
      setConversations(response.data);
    } catch (err) {
      console.error('Error loading conversations:', err);
    }
    setLoading(false);
  };

  const loadMessages = async (conversationId) => {
    try {
      const response = await api.get(`/messages/conversation/${conversationId}`);
      setMessages(response.data);
      setSelectedConversation(conversationId);
    } catch (err) {
      console.error('Error loading messages:', err);
    }
  };

  const handleReply = async (e) => {
    e.preventDefault();
    if (!replyContent.trim() || !selectedConversation) return;

    setSubmitLoading(true);

    try {
      await api.post(`/admin/messages/reply/${selectedConversation}?content=${encodeURIComponent(replyContent)}`);
      setReplyContent('');
      loadMessages(selectedConversation);
      loadConversations();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'envoi');
    }

    setSubmitLoading(false);
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
        <h1 className="text-2xl font-bold text-gray-900">Messages Clients</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
          {/* Conversations list */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 border-b bg-gray-50">
              <h2 className="font-semibold text-gray-900">Conversations</h2>
            </div>
            <div className="flex-1 overflow-y-auto divide-y">
              {conversations.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  Aucun message
                </div>
              ) : (
                conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => loadMessages(conv.id)}
                    className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                      selectedConversation === conv.id ? 'bg-cyan-50 border-l-4 border-cyan-500' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{conv.user_name}</p>
                        <p className="text-sm text-gray-600 truncate">{conv.subject}</p>
                      </div>
                      {conv.unread_count > 0 && (
                        <span className="ml-2 px-2 py-0.5 text-xs bg-red-500 text-white rounded-full">
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(conv.last_message_at).toLocaleDateString('fr-FR')}
                    </p>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Message content */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm overflow-hidden flex flex-col">
            {selectedConversation ? (
              <>
                {/* Messages */}
                <div className="flex-1 p-4 overflow-y-auto space-y-4">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`max-w-[80%] ${
                        msg.sender_role === 'ADMIN' ? 'ml-auto' : ''
                      }`}
                    >
                      <div
                        className={`p-4 rounded-lg ${
                          msg.sender_role === 'ADMIN'
                            ? 'bg-cyan-500 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`text-xs font-medium ${msg.sender_role === 'ADMIN' ? 'text-cyan-100' : 'text-gray-500'}`}>
                            {msg.sender_name}
                          </span>
                          <span className={`px-1.5 py-0.5 text-xs rounded ${
                            msg.sender_role === 'ADMIN' 
                              ? 'bg-cyan-400 text-white' 
                              : 'bg-gray-200 text-gray-600'
                          }`}>
                            {msg.sender_role}
                          </span>
                        </div>
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                      <p className={`text-xs mt-1 ${msg.sender_role === 'ADMIN' ? 'text-right' : ''} text-gray-400`}>
                        {new Date(msg.created_at).toLocaleString('fr-FR')}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Reply form */}
                <form onSubmit={handleReply} className="p-4 border-t bg-gray-50">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Votre réponse..."
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                      value={replyContent}
                      onChange={(e) => setReplyContent(e.target.value)}
                    />
                    <button
                      type="submit"
                      disabled={submitLoading || !replyContent.trim()}
                      className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50"
                    >
                      {submitLoading ? '...' : 'Envoyer'}
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                Sélectionnez une conversation
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminMessages;
