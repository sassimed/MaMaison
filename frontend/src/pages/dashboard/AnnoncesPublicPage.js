import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { Megaphone, MapPin, Clock, User, Filter, Send, ChevronRight, DollarSign, Calendar, X, CheckCircle, Loader2, AlertCircle, ArrowUp, RefreshCw, Search } from 'lucide-react';

// Cache for storing list state
const listCache = new Map();

function AnnoncesPublicPage() {
  var navigate = useNavigate();
  var location = useLocation();
  var [searchParams, setSearchParams] = useSearchParams();
  
  // Generate cache key from filters
  var cacheKey = useMemo(function() {
    return searchParams.toString() || 'default';
  }, [searchParams]);
  
  // State
  var [annonces, setAnnonces] = useState([]);
  var [cities, setCities] = useState([]);
  var [loading, setLoading] = useState(true);
  var [loadingMore, setLoadingMore] = useState(false);
  var [error, setError] = useState(null);
  var [hasMore, setHasMore] = useState(true);
  var [cursor, setCursor] = useState(null);
  var [firstCursor, setFirstCursor] = useState(null); // For checking new items
  var [total, setTotal] = useState(0);
  var [newCount, setNewCount] = useState(0);
  var [showScrollTop, setShowScrollTop] = useState(false);
  
  // Filters from URL
  var selectedCity = searchParams.get('city') || '';
  var selectedCategory = searchParams.get('category') || '';
  var selectedSort = searchParams.get('sort') || 'recent';
  
  // Modal state
  var [showResponseModal, setShowResponseModal] = useState(false);
  var [selectedAnnonce, setSelectedAnnonce] = useState(null);
  var [submitting, setSubmitting] = useState(false);
  var [responseData, setResponseData] = useState({
    message: '',
    price_estimate: '',
    availability: ''
  });

  // Refs
  var sentinelRef = useRef(null);
  var prefetchSentinelRef = useRef(null);
  var isFetching = useRef(false);
  var scrollPositionRef = useRef(0);
  var observerRef = useRef(null);
  var prefetchObserverRef = useRef(null);
  var prefetchedData = useRef(null);

  var categories = [
    'Installation Caméra',
    'Système d\'Alarme',
    'Domotique',
    'Éclairage Connecté',
    'Serrure Connectée',
    'Réseau WiFi/Câblage',
    'Autre'
  ];

  // Save state to cache
  var saveToCache = useCallback(function(items, cursorVal, firstCursorVal, hasMoreVal, totalVal) {
    listCache.set(cacheKey, {
      items: items,
      cursor: cursorVal,
      firstCursor: firstCursorVal,
      hasMore: hasMoreVal,
      total: totalVal,
      scrollY: window.scrollY,
      timestamp: Date.now()
    });
  }, [cacheKey]);

  // Restore from cache
  var restoreFromCache = useCallback(function() {
    var cached = listCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) { // 5 min cache
      setAnnonces(cached.items);
      setCursor(cached.cursor);
      setFirstCursor(cached.firstCursor);
      setHasMore(cached.hasMore);
      setTotal(cached.total);
      setLoading(false);
      
      // Restore scroll position after render
      requestAnimationFrame(function() {
        window.scrollTo(0, cached.scrollY);
      });
      return true;
    }
    return false;
  }, [cacheKey]);

  // Deduplicate items by id
  var deduplicateItems = function(items) {
    var seen = new Set();
    return items.filter(function(item) {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  };

  // Fetch annonces
  var fetchAnnonces = useCallback(async function(cursorParam, append) {
    if (isFetching.current) return;
    isFetching.current = true;
    
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }
    setError(null);
    
    try {
      var params = new URLSearchParams();
      if (selectedCity) params.append('city', selectedCity);
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedSort) params.append('sort', selectedSort);
      if (cursorParam) params.append('cursor', cursorParam);
      params.append('limit', '10');
      
      var response = await api.get('/annonces/public?' + params.toString());
      var data = response.data;
      
      var newItems = data.items;
      var newCursor = data.pagination.next_cursor;
      var newHasMore = data.pagination.has_more;
      var newTotal = data.pagination.total;
      
      if (append) {
        setAnnonces(function(prev) {
          var combined = [...prev, ...newItems];
          return deduplicateItems(combined);
        });
      } else {
        setAnnonces(deduplicateItems(newItems));
        // Store first cursor for checking new items
        if (newItems.length > 0) {
          var firstItem = newItems[0];
          var timestamp = firstItem.published_at || firstItem.created_at;
          setFirstCursor(timestamp + '|' + firstItem.id);
        }
      }
      
      setCursor(newCursor);
      setHasMore(newHasMore);
      setTotal(newTotal);
      
      // Save to cache
      setAnnonces(function(currentItems) {
        saveToCache(currentItems, newCursor, firstCursor, newHasMore, newTotal);
        return currentItems;
      });
      
      // Clear prefetched data after use
      prefetchedData.current = null;
      
    } catch (err) {
      console.error('Error loading annonces:', err);
      if (err.response?.status === 403) {
        setError('Accès réservé aux professionnels');
      } else {
        setError('Erreur de chargement. Vérifiez votre connexion.');
      }
    }
    
    setLoading(false);
    setLoadingMore(false);
    isFetching.current = false;
  }, [selectedCity, selectedCategory, selectedSort, saveToCache, firstCursor]);

  // Prefetch next page
  var prefetchNextPage = useCallback(async function() {
    if (!cursor || !hasMore || prefetchedData.current || isFetching.current) return;
    
    try {
      var params = new URLSearchParams();
      if (selectedCity) params.append('city', selectedCity);
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedSort) params.append('sort', selectedSort);
      params.append('cursor', cursor);
      params.append('limit', '10');
      
      var response = await api.get('/annonces/public?' + params.toString());
      prefetchedData.current = response.data;
    } catch (err) {
      // Silently fail prefetch
    }
  }, [cursor, hasMore, selectedCity, selectedCategory, selectedSort]);

  // Check for new announcements
  var checkNewAnnonces = useCallback(async function() {
    if (!firstCursor) return;
    
    try {
      var params = new URLSearchParams();
      params.append('since_cursor', firstCursor);
      if (selectedCity) params.append('city', selectedCity);
      if (selectedCategory) params.append('category', selectedCategory);
      
      var response = await api.get('/annonces/public/new-count?' + params.toString());
      setNewCount(response.data.new_count);
    } catch (err) {
      // Silently fail
    }
  }, [firstCursor, selectedCity, selectedCategory]);

  // Load cities on mount
  useEffect(function() {
    async function loadCities() {
      try {
        var citiesRes = await api.get('/annonces/public/cities');
        setCities(citiesRes.data);
      } catch (err) {
        console.error('Error loading cities:', err);
      }
    }
    loadCities();
  }, []);

  // Initial load or restore from cache
  useEffect(function() {
    // Check if we're coming back from detail page
    var restoredFromCache = restoreFromCache();
    
    if (!restoredFromCache) {
      setAnnonces([]);
      setCursor(null);
      setHasMore(true);
      setNewCount(0);
      fetchAnnonces(null, false);
    }
  }, [cacheKey]); // eslint-disable-line react-hooks/exhaustive-deps

  // Check for new items periodically
  useEffect(function() {
    var interval = setInterval(checkNewAnnonces, 30000); // Every 30 seconds
    return function() { clearInterval(interval); };
  }, [checkNewAnnonces]);

  // Scroll position tracking
  useEffect(function() {
    var handleScroll = function() {
      scrollPositionRef.current = window.scrollY;
      setShowScrollTop(window.scrollY > 500);
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return function() { window.removeEventListener('scroll', handleScroll); };
  }, []);

  // IntersectionObserver for infinite scroll
  useEffect(function() {
    if (loading || !hasMore) return;

    var observer = new IntersectionObserver(
      function(entries) {
        if (entries[0].isIntersecting && hasMore && !isFetching.current && cursor) {
          // Use prefetched data if available
          if (prefetchedData.current) {
            var data = prefetchedData.current;
            setAnnonces(function(prev) {
              var combined = [...prev, ...data.items];
              return deduplicateItems(combined);
            });
            setCursor(data.pagination.next_cursor);
            setHasMore(data.pagination.has_more);
            prefetchedData.current = null;
          } else {
            fetchAnnonces(cursor, true);
          }
        }
      },
      { threshold: 0.1 }
    );

    if (sentinelRef.current) {
      observer.observe(sentinelRef.current);
    }

    observerRef.current = observer;

    return function() {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [loading, hasMore, cursor, fetchAnnonces]);

  // IntersectionObserver for prefetching (600px before end)
  useEffect(function() {
    if (loading || !hasMore || !cursor) return;

    var prefetchObserver = new IntersectionObserver(
      function(entries) {
        if (entries[0].isIntersecting) {
          prefetchNextPage();
        }
      },
      { rootMargin: '600px' }
    );

    if (prefetchSentinelRef.current) {
      prefetchObserver.observe(prefetchSentinelRef.current);
    }

    prefetchObserverRef.current = prefetchObserver;

    return function() {
      if (prefetchObserverRef.current) {
        prefetchObserverRef.current.disconnect();
      }
    };
  }, [loading, hasMore, cursor, prefetchNextPage]);

  // Update URL when filters change
  var updateURL = useCallback(function(city, category, sort) {
    var params = new URLSearchParams();
    if (city) params.set('city', city);
    if (category) params.set('category', category);
    if (sort && sort !== 'recent') params.set('sort', sort);
    setSearchParams(params);
  }, [setSearchParams]);

  // Handle filter changes - reset and scroll to top
  function handleFilterChange(type, value) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    listCache.delete(cacheKey); // Clear cache for old filters
    
    if (type === 'city') {
      updateURL(value, selectedCategory, selectedSort);
    } else if (type === 'category') {
      updateURL(selectedCity, value, selectedSort);
    } else if (type === 'sort') {
      updateURL(selectedCity, selectedCategory, value);
    }
  }

  function clearFilters() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    listCache.delete(cacheKey);
    setSearchParams(new URLSearchParams());
  }

  // Refresh to see new items
  function handleRefresh() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    listCache.delete(cacheKey);
    setNewCount(0);
    setAnnonces([]);
    setCursor(null);
    setHasMore(true);
    fetchAnnonces(null, false);
  }

  // Retry on error
  function handleRetry() {
    if (cursor) {
      fetchAnnonces(cursor, true);
    } else {
      fetchAnnonces(null, false);
    }
  }

  // Scroll to top
  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Navigate to detail with state
  function handleAnnonceClick(annonce) {
    // Save current scroll position before navigating
    saveToCache(annonces, cursor, firstCursor, hasMore, total);
    // Navigate to response modal instead of detail page for this use case
    openResponseModal(annonce);
  }

  function openResponseModal(annonce) {
    setSelectedAnnonce(annonce);
    setResponseData({ message: '', price_estimate: '', availability: '' });
    setShowResponseModal(true);
  }

  async function handleSubmitResponse(e) {
    e.preventDefault();
    if (!selectedAnnonce) return;
    
    setSubmitting(true);
    try {
      var data = {
        message: responseData.message,
        price_estimate: responseData.price_estimate ? parseFloat(responseData.price_estimate) : null,
        availability: responseData.availability || null
      };
      
      await api.post('/annonces/public/' + selectedAnnonce.id + '/respond', data);
      alert('Votre réponse a été envoyée avec succès !');
      setShowResponseModal(false);
      
      // Update the annonce in the list
      setAnnonces(function(prev) {
        return prev.map(function(a) {
          if (a.id === selectedAnnonce.id) {
            return { ...a, already_responded: true };
          }
          return a;
        });
      });
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'envoi');
    }
    setSubmitting(false);
  }

  function formatDate(d) {
    return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  // Skeleton loader
  function renderSkeleton() {
    return Array.from({ length: 8 }).map(function(_, i) {
      return (
        <div key={'skeleton-' + i} className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
          <div className="flex items-center gap-2 mb-4">
            <div className="h-6 w-24 bg-gray-200 rounded-full"></div>
            <div className="h-6 w-20 bg-gray-200 rounded-full"></div>
          </div>
          <div className="h-5 w-3/4 bg-gray-200 rounded mb-3"></div>
          <div className="space-y-2 mb-4">
            <div className="h-4 w-full bg-gray-200 rounded"></div>
            <div className="h-4 w-2/3 bg-gray-200 rounded"></div>
          </div>
          <div className="flex items-center gap-4 mb-4">
            <div className="h-4 w-24 bg-gray-200 rounded"></div>
            <div className="h-4 w-32 bg-gray-200 rounded"></div>
          </div>
          <div className="pt-4 border-t flex justify-between items-center">
            <div className="h-4 w-20 bg-gray-200 rounded"></div>
            <div className="h-10 w-28 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      );
    });
  }

  function renderAnnonceCard(annonce) {
    return (
      <div 
        key={annonce.id} 
        className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow border border-gray-100"
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="px-3 py-1 bg-gradient-to-r from-purple-100 to-cyan-100 text-purple-700 text-xs font-medium rounded-full">
                {annonce.category}
              </span>
              <span className="flex items-center text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                <MapPin className="w-3 h-3 mr-1" />
                {annonce.city}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">{annonce.title}</h3>
          </div>
        </div>
        
        <p className="text-gray-600 mb-4 line-clamp-3">{annonce.description}</p>
        
        <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
          <span className="flex items-center gap-1">
            <User className="w-4 h-4" />
            {annonce.client_name}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {formatDate(annonce.published_at || annonce.created_at)}
          </span>
        </div>
        
        <div className="flex items-center justify-between pt-4 border-t">
          {annonce.already_responded ? (
            <span className="flex items-center gap-2 text-green-600 text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              Vous avez déjà répondu
            </span>
          ) : (
            <span className="text-sm text-gray-400">—</span>
          )}
          
          <button
            onClick={function(e) { e.stopPropagation(); openResponseModal(annonce); }}
            disabled={annonce.already_responded}
            className={'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ' + 
              (annonce.already_responded 
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                : 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white hover:from-purple-700 hover:to-cyan-600')}
            data-testid={'respond-annonce-' + annonce.id}
          >
            <Send className="w-4 h-4" />
            {annonce.already_responded ? 'Répondu' : 'Répondre'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6" role="main" aria-busy={loading}>
        {/* New announcements banner */}
        {newCount > 0 && (
          <div 
            className="bg-cyan-50 border border-cyan-200 rounded-xl p-4 flex items-center justify-between cursor-pointer hover:bg-cyan-100 transition-colors"
            onClick={handleRefresh}
            role="button"
            aria-label={'Voir ' + newCount + ' nouvelles annonces'}
          >
            <span className="flex items-center gap-2 text-cyan-700 font-medium">
              <RefreshCw className="w-5 h-5" />
              {newCount} nouvelle{newCount > 1 ? 's' : ''} annonce{newCount > 1 ? 's' : ''} disponible{newCount > 1 ? 's' : ''}
            </span>
            <span className="text-cyan-600 text-sm">Cliquez pour actualiser</span>
          </div>
        )}

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <Megaphone className="w-7 h-7 text-cyan-500" />
              Annonces disponibles
            </h1>
            <p className="text-gray-500 mt-1">Trouvez des missions près de chez vous</p>
          </div>
          
          <button
            onClick={function() { navigate('/dashboard/my-responses'); }}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium"
            data-testid="view-my-responses-btn"
          >
            Mes réponses
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex items-center gap-2 text-gray-500">
              <Filter className="w-5 h-5" />
              <span className="font-medium">Filtres :</span>
            </div>
            
            <div className="flex-1 flex flex-col sm:flex-row gap-3 flex-wrap">
              <select
                value={selectedCity}
                onChange={function(e) { handleFilterChange('city', e.target.value); }}
                className="px-4 py-2 border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                data-testid="filter-city"
              >
                <option value="">Toutes les villes</option>
                {cities.map(function(city) {
                  return <option key={city} value={city}>{city}</option>;
                })}
              </select>
              
              <select
                value={selectedCategory}
                onChange={function(e) { handleFilterChange('category', e.target.value); }}
                className="px-4 py-2 border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                data-testid="filter-category"
              >
                <option value="">Toutes les catégories</option>
                {categories.map(function(cat) {
                  return <option key={cat} value={cat}>{cat}</option>;
                })}
              </select>
              
              <select
                value={selectedSort}
                onChange={function(e) { handleFilterChange('sort', e.target.value); }}
                className="px-4 py-2 border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                data-testid="filter-sort"
              >
                <option value="recent">Plus récentes</option>
                <option value="oldest">Plus anciennes</option>
              </select>
              
              {(selectedCity || selectedCategory || selectedSort !== 'recent') && (
                <button
                  onClick={clearFilters}
                  className="px-4 py-2 text-red-600 hover:text-red-700 flex items-center gap-1"
                >
                  <X className="w-4 h-4" />
                  Effacer
                </button>
              )}
            </div>
            
            {!loading && (
              <span className="text-sm text-gray-500 self-center whitespace-nowrap">
                {total} annonce{total > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {/* Results */}
        {loading && annonces.length === 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" aria-label="Chargement des annonces">
            {renderSkeleton()}
          </div>
        ) : annonces.length === 0 && !loading ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Aucune annonce disponible</h2>
            <p className="text-gray-500">
              {selectedCity || selectedCategory 
                ? 'Aucune annonce ne correspond à vos critères. Essayez de modifier vos filtres.'
                : 'Il n\'y a pas d\'annonces publiées pour le moment. Revenez plus tard !'}
            </p>
            {(selectedCity || selectedCategory) && (
              <button
                onClick={clearFilters}
                className="mt-4 text-cyan-600 hover:text-cyan-700 font-medium"
              >
                Voir toutes les annonces
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {annonces.map(renderAnnonceCard)}
            </div>
            
            {/* Prefetch sentinel (600px before end) */}
            <div ref={prefetchSentinelRef} style={{ height: '1px' }} aria-hidden="true" />
            
            {/* Loading sentinel */}
            <div ref={sentinelRef} className="py-4 flex flex-col items-center gap-4">
              {loadingMore && (
                <div className="flex items-center gap-2 text-gray-500" role="status" aria-label="Chargement en cours">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Chargement...</span>
                </div>
              )}
              
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3 w-full max-w-md">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                  <span className="text-red-700 flex-1">{error}</span>
                  <button
                    onClick={handleRetry}
                    className="px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm font-medium"
                  >
                    Réessayer
                  </button>
                </div>
              )}
              
              {!hasMore && annonces.length > 0 && !error && (
                <div className="text-center space-y-3">
                  <p className="text-sm text-gray-400">Vous avez tout vu !</p>
                  <button
                    onClick={scrollToTop}
                    className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 text-sm font-medium flex items-center gap-2 mx-auto"
                  >
                    <ArrowUp className="w-4 h-4" />
                    Retour en haut
                  </button>
                </div>
              )}
              
              {/* Fallback button for loading more (accessibility) */}
              {hasMore && !loadingMore && cursor && (
                <button
                  onClick={function() { fetchAnnonces(cursor, true); }}
                  className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm font-medium sr-only focus:not-sr-only"
                >
                  Charger plus d'annonces
                </button>
              )}
            </div>
          </div>
        )}

        {/* Floating scroll to top button */}
        {showScrollTop && (
          <button
            onClick={scrollToTop}
            className="fixed bottom-6 right-6 p-3 bg-cyan-500 text-white rounded-full shadow-lg hover:bg-cyan-600 transition-all z-40"
            aria-label="Retour en haut"
          >
            <ArrowUp className="w-5 h-5" />
          </button>
        )}

        {/* Response Modal */}
        {showResponseModal && selectedAnnonce && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b">
                <h2 className="text-xl font-bold">Répondre à l'annonce</h2>
                <p className="text-sm text-gray-500 mt-1">{selectedAnnonce.title}</p>
              </div>
              
              <form onSubmit={handleSubmitResponse} className="p-6 space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">
                    <strong>Client :</strong> {selectedAnnonce.client_name}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    <strong>Ville :</strong> {selectedAnnonce.city}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Votre message *
                  </label>
                  <textarea
                    required
                    rows="4"
                    placeholder="Présentez-vous et expliquez comment vous pouvez aider..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={responseData.message}
                    onChange={function(e) { setResponseData({...responseData, message: e.target.value}); }}
                    data-testid="response-message-input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Estimation de prix (DT) - optionnel
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="Ex: 150.00"
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                      value={responseData.price_estimate}
                      onChange={function(e) { setResponseData({...responseData, price_estimate: e.target.value}); }}
                      data-testid="response-price-input"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Disponibilité - optionnel
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Ex: Disponible dès lundi prochain"
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                      value={responseData.availability}
                      onChange={function(e) { setResponseData({...responseData, availability: e.target.value}); }}
                      data-testid="response-availability-input"
                    />
                  </div>
                </div>
                
                <div className="flex gap-3 pt-4 border-t">
                  <button
                    type="button"
                    onClick={function() { setShowResponseModal(false); }}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:from-purple-700 hover:to-cyan-600 disabled:opacity-50"
                    data-testid="submit-response-btn"
                  >
                    {submitting ? 'Envoi...' : 'Envoyer ma réponse'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default AnnoncesPublicPage;
