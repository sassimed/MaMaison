import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';

const Messages = () => {
  const [searchParams] = useSearchParams();
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewMessage, setShowNewMessage] = useState(searchParams.get('new') === 'true');
  const [newMessageData, setNewMessageData] = useState({
    subject: '',
    content: '',
  });
  const [replyContent, setReplyContent] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await api.get('/messages/conversations');
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

  const handleSendNewMessage = async (e) => {
    e.preventDefault();
    setSubmitLoading(true);

    try {
      await api.post('/messages', newMessageData);
      setShowNewMessage(false);
      setNewMessageData({ subject: '', content: '' });
      loadConversations();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'envoi');
    }

    setSubmitLoading(false);
  };

  const handleReply = async (e) => {
    e.preventDefault();
    if (!replyContent.trim()) return;

    setSubmitLoading(true);

    try {
      await api.post(`/messages/conversation/${selectedConversation}/reply`, {
        content: replyContent,
      });
      setReplyContent('');
      loadMessages(selectedConversation);
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
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Messages</h1>
          <button
            onClick={() => { setShowNewMessage(!showNewMessage); setSelectedConversation(null); }}
            data-testid="new-message-button"
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            {showNewMessage ? 'Annuler' : '+ Nouveau message'}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Conversations list */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-gray-900">Conversations</h2>
            </div>
            <div className="divide-y max-h-96 overflow-y-auto">
              {conversations.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  Aucune conversation
                </div>
              ) : (
                conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => { loadMessages(conv.id); setShowNewMessage(false); }}
                    className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                      selectedConversation === conv.id ? 'bg-cyan-50' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-medium text-gray-900 truncate">{conv.subject}</span>
                      {conv.unread_count > 0 && (
                        <span className="ml-2 px-2 py-0.5 text-xs bg-cyan-500 text-white rounded-full">
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {new Date(conv.last_message_at).toLocaleDateString('fr-FR')}
                    </p>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Message content or new message form */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm overflow-hidden">
            {showNewMessage ? (
              <div className="p-6">
                <h2 className="font-semibold text-gray-900 mb-4">Nouveau message</h2>
                <form onSubmit={handleSendNewMessage} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Sujet *
                    </label>
                    <input
                      type="text"
                      required
                      data-testid="message-subject-input"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                      placeholder="Objet du message"
                      value={newMessageData.subject}
                      onChange={(e) => setNewMessageData({ ...newMessageData, subject: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Message *
                    </label>
                    <textarea
                      required
                      rows="6"
                      data-testid="message-content-input"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                      placeholder="Votre message..."
                      value={newMessageData.content}
                      onChange={(e) => setNewMessageData({ ...newMessageData, content: e.target.value })}
                    />
                  </div>
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={submitLoading}
                      data-testid="message-submit-button"
                      className="px-6 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50"
                    >
                      {submitLoading ? 'Envoi...' : 'Envoyer'}
                    </button>
                  </div>
                </form>
              </div>
            ) : selectedConversation ? (
              <div className="flex flex-col h-96">
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
                        className={`p-3 rounded-lg ${
                          msg.sender_role === 'ADMIN'
                            ? 'bg-cyan-100 text-cyan-900'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <p className="text-xs font-medium mb-1">
                          {msg.sender_name} ({msg.sender_role})
                        </p>
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(msg.created_at).toLocaleString('fr-FR')}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Reply form */}
                <form onSubmit={handleReply} className="p-4 border-t">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Votre réponse..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                      value={replyContent}
                      onChange={(e) => setReplyContent(e.target.value)}
                    />
                    <button
                      type="submit"
                      disabled={submitLoading || !replyContent.trim()}
                      className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50"
                    >
                      Envoyer
                    </button>
                  </div>
                </form>
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500">
                Sélectionnez une conversation ou créez un nouveau message
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Messages;
