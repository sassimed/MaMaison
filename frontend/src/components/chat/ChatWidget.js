import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, X, Send, Loader2, Trash2, ShoppingCart, ExternalLink } from 'lucide-react';
import api from '../../services/api';

const ChatWidget = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [addingToCart, setAddingToCart] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Generate or retrieve session ID
  useEffect(() => {
    const storedSessionId = localStorage.getItem('mydar_chat_session');
    if (storedSessionId) {
      setSessionId(storedSessionId);
      loadChatHistory(storedSessionId);
    } else {
      const newSessionId = 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('mydar_chat_session', newSessionId);
      setSessionId(newSessionId);
    }
  }, []);

  // Listen for "Ask AI" button clicks from product pages
  useEffect(() => {
    const handleOpenChatWithProduct = async (event) => {
      const productInfo = event.detail;
      
      // Clear previous session and create new one
      const newSessionId = 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('mydar_chat_session', newSessionId);
      setSessionId(newSessionId);
      setMessages([]);
      
      // Open chat
      setIsOpen(true);
      
      // Auto-detect language from browser
      const browserLang = navigator.language || navigator.userLanguage || 'fr';
      const isFrench = browserLang.startsWith('fr');
      const langChoice = isFrench ? '1' : '1'; // Default French, can be '2' for Tounsi
      
      // Start conversation flow automatically
      setIsLoading(true);
      try {
        // Step 1: Start
        await api.post('/chatbot/chat', {
          message: 'start',
          session_id: newSessionId
        });
        
        // Step 2: Choose language (auto French)
        await api.post('/chatbot/chat', {
          message: langChoice,
          session_id: newSessionId
        });
        
        // Step 3: Choose mode 2 (question produit)
        await api.post('/chatbot/chat', {
          message: '2',
          session_id: newSessionId
        });
        
        // Step 4: Send product name/code
        const productQuery = productInfo.model_code || productInfo.name;
        const response = await api.post('/chatbot/chat', {
          message: productQuery,
          session_id: newSessionId
        });
        
        // Show only the final response
        setMessages([{ 
          role: 'assistant', 
          content: response.data.response,
          products: response.data.products || []
        }]);
        
      } catch (error) {
        console.error('Error starting product chat:', error);
        setMessages([{ 
          role: 'assistant', 
          content: 'Erreur lors de l\'ouverture du chat. Veuillez réessayer.',
          products: []
        }]);
      } finally {
        setIsLoading(false);
      }
    };
    
    window.addEventListener('openChatWithProduct', handleOpenChatWithProduct);
    return () => {
      window.removeEventListener('openChatWithProduct', handleOpenChatWithProduct);
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when chat opens AND trigger welcome message
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      // If no messages yet, trigger welcome message automatically
      if (messages.length === 0 && sessionId && !isLoading) {
        triggerWelcome();
      }
    }
  }, [isOpen]);

  // Trigger welcome message on chat open
  const triggerWelcome = async () => {
    setIsLoading(true);
    try {
      const response = await api.post('/chatbot/chat', {
        message: 'start',
        session_id: sessionId
      });

      // Add bot welcome message
      setMessages([{ 
        role: 'assistant', 
        content: response.data.response,
        products: []
      }]);

      // Update session ID if new
      if (response.data.session_id && response.data.session_id !== sessionId) {
        setSessionId(response.data.session_id);
        localStorage.setItem('mydar_chat_session', response.data.session_id);
      }
    } catch (error) {
      console.error('Welcome trigger error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadChatHistory = async (sid) => {
    try {
      const response = await api.get(`/chatbot/history/${sid}`);
      if (response.data.messages && response.data.messages.length > 0) {
        setMessages(response.data.messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          products: []
        })));
      }
    } catch (error) {
      console.log('No previous chat history');
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    
    // Add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: userMessage, products: [] }]);
    setIsLoading(true);

    try {
      const response = await api.post('/chatbot/chat', {
        message: userMessage,
        session_id: sessionId
      });

      // Extract product IDs from response content
      const productIds = extractProductsFromContent(response.data.response);
      
      // Use products from response (v2 format) or fetch if needed
      let products = response.data.products || response.data.products_mentioned || [];
      if (products.length === 0 && productIds.length > 0) {
        products = await fetchProductDetails(productIds);
      }

      // Add bot response with products
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.response,
        products: products
      }]);

      // Update session ID if new
      if (response.data.session_id && response.data.session_id !== sessionId) {
        setSessionId(response.data.session_id);
        localStorage.setItem('mydar_chat_session', response.data.session_id);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Désolé, une erreur est survenue. Veuillez réessayer.',
        products: []
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = async () => {
    if (sessionId) {
      try {
        await api.delete(`/chatbot/history/${sessionId}`);
      } catch (error) {
        console.log('Error clearing history');
      }
    }
    setMessages([]);
    const newSessionId = 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('mydar_chat_session', newSessionId);
    setSessionId(newSessionId);
    
    // Trigger welcome message for new session
    setTimeout(async () => {
      setIsLoading(true);
      try {
        const response = await api.post('/chatbot/chat', {
          message: 'start',
          session_id: newSessionId
        });
        setMessages([{ 
          role: 'assistant', 
          content: response.data.response,
          products: []
        }]);
      } catch (error) {
        console.error('Welcome trigger error:', error);
      } finally {
        setIsLoading(false);
      }
    }, 100);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleAddToCart = async (productId) => {
    setAddingToCart(productId);
    try {
      await api.post('/cart', { product_id: productId, quantity: 1 });
      // Show success feedback
      alert('Produit ajouté au panier !');
    } catch (error) {
      if (error.response?.status === 401) {
        // User not logged in
        navigate('/login', { state: { from: '/catalog', message: 'Connectez-vous pour ajouter au panier' } });
      } else {
        alert('Erreur lors de l\'ajout au panier');
      }
    } finally {
      setAddingToCart(null);
    }
  };

  const handleViewProduct = (productId) => {
    setIsOpen(false);
    navigate(`/catalog/${productId}`);
  };

  const formatMessage = (content, extractedProducts = []) => {
    // Remove product action links from text (they'll be shown as cards)
    let cleanContent = content
      // Remove the markdown links for products
      .replace(/🔍\s*\[Voir détails\]\([^)]+\)\s*\|\s*🛒\s*\[Ajouter au panier\]\([^)]+\)/g, '')
      // Remove empty lines left over
      .replace(/\n\s*\n\s*\n/g, '\n\n')
      .trim();
    
    // Convert markdown-like formatting to HTML
    return cleanContent
      .split('\n')
      .map((line, i) => {
        // Bold text
        line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        return line;
      })
      .join('<br/>');
  };

  // Parse product IDs from message content
  const extractProductsFromContent = (content) => {
    const productIds = [];
    // Match patterns like /produit/xxx or ADD_TO_CART:xxx
    const patterns = [
      /\/produit\/([a-zA-Z0-9\-]+)/g,
      /ADD_TO_CART:([a-zA-Z0-9\-]+)/g,
      /\{+PRODUCT_ACTIONS:([a-zA-Z0-9\-]+)\}+/g
    ];
    
    patterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        if (!productIds.includes(match[1])) {
          productIds.push(match[1]);
        }
      }
    });
    
    return productIds;
  };

  // Fetch product details by IDs
  const fetchProductDetails = async (productIds) => {
    if (!productIds || productIds.length === 0) return [];
    
    try {
      const products = await Promise.all(
        productIds.slice(0, 6).map(async (id) => {
          try {
            const response = await api.get(`/v2/products/${id}`);
            return response.data;
          } catch (e) {
            return null;
          }
        })
      );
      return products.filter(p => p !== null);
    } catch (error) {
      console.error('Error fetching products:', error);
      return [];
    }
  };

  // Product Card Component - Enhanced with more details
  const ProductCard = ({ product }) => (
    <div className="bg-white rounded-lg border shadow-sm p-3 mt-2 hover:shadow-md transition-shadow">
      <div className="flex gap-3">
        {(product.image_url || product.image) ? (
          <img 
            src={product.image_url || product.image} 
            alt={product.name}
            className="w-20 h-20 object-contain rounded bg-gray-50 flex-shrink-0"
          />
        ) : (
          <div className="w-20 h-20 bg-gray-100 rounded flex items-center justify-center flex-shrink-0">
            <ShoppingCart className="w-6 h-6 text-gray-300" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm text-gray-900 line-clamp-2">{product.name}</h4>
          <div className="flex flex-wrap gap-1 mt-1">
            {product.brand && (
              <span className="px-1.5 py-0.5 text-[10px] bg-blue-100 text-blue-700 rounded">
                {product.brand}
              </span>
            )}
            {product.category && (
              <span className="px-1.5 py-0.5 text-[10px] bg-gray-100 text-gray-600 rounded">
                {product.category}
              </span>
            )}
            {product.technology && (
              <span className="px-1.5 py-0.5 text-[10px] bg-green-100 text-green-700 rounded">
                {product.technology}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-sm font-bold text-purple-600">
              {product.price ? `${product.price.toFixed(3)} DT` : 'Prix sur demande'}
            </p>
            {product.youtube_url && (
              <span className="text-[10px] text-red-500 flex items-center gap-0.5">
                ▶ Vidéo
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button
          onClick={() => handleViewProduct(product.id)}
          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-xs font-medium text-purple-600 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
          Détails
        </button>
        <button
          onClick={() => handleAddToCart(product.id)}
          disabled={addingToCart === product.id}
          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-xs font-medium text-white bg-gradient-to-r from-purple-600 to-cyan-500 rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {addingToCart === product.id ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <ShoppingCart className="w-3 h-3" />
          )}
          Ajouter
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Chat Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center ${isOpen ? 'scale-0' : 'scale-100'}`}
        data-testid="chat-widget-button"
        aria-label="Ouvrir le chat"
      >
        <MessageCircle className="w-6 h-6" />
        {messages.length === 0 && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse"></span>
        )}
      </button>

      {/* Chat Window */}
      <div 
        className={`fixed bottom-6 right-6 z-50 w-96 max-w-[calc(100vw-2rem)] bg-white rounded-2xl shadow-2xl transition-all duration-300 overflow-hidden ${isOpen ? 'scale-100 opacity-100' : 'scale-0 opacity-0'}`}
        style={{ height: '550px', maxHeight: 'calc(100vh - 100px)' }}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-cyan-500 text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <MessageCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold">Assistant MyDar</h3>
              <p className="text-xs text-white/80">En ligne • Répond instantanément</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={clearChat}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Nouvelle conversation"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setIsOpen(false)}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ height: 'calc(100% - 140px)' }}>
          {messages.length === 0 && !isLoading && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-100 to-cyan-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="w-8 h-8 text-purple-600" />
              </div>
              <h4 className="font-semibold text-gray-800 mb-2">Chargement...</h4>
              <p className="text-sm text-gray-500">
                Préparation de l'assistant MyDar
              </p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index}>
              <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-br-md'
                      : 'bg-gray-100 text-gray-800 rounded-bl-md'
                  }`}
                >
                  <div 
                    className="text-sm whitespace-pre-wrap"
                    dangerouslySetInnerHTML={{ __html: formatMessage(msg.content, msg.products) }}
                  />
                </div>
              </div>
              
              {/* Product Cards - Always show when products exist */}
              {msg.role === 'assistant' && msg.products && msg.products.length > 0 && (
                <div className="mt-3 space-y-2">
                  {msg.products.map((product, pIdx) => (
                    <ProductCard key={product.id || pIdx} product={product} />
                  ))}
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-md">
                <div className="flex items-center gap-2 text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">En train d'écrire...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t bg-white">
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Écrivez votre message..."
              className="flex-1 px-4 py-2.5 bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
              data-testid="chat-input"
            />
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="w-10 h-10 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-full flex items-center justify-center hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="chat-send-button"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatWidget;
