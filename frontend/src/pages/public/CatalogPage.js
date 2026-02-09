import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import analytics from '../../services/analytics';
import { 
  ShoppingCart, Heart, Check, Search, SlidersHorizontal, X, ArrowUp, Loader2, AlertCircle, ArrowUpDown,
  Camera, Bell, Lightbulb, Cpu, ToggleRight, Plug, Blinds, Monitor, Wifi, Shield, Home, Package, Play,
  Lock, Video, Flame, Box, Zap, Settings, Router, ChevronRight, ChevronDown
} from 'lucide-react';
import { SEO } from '../../components/SEO';

// Map icon names to Lucide components - Updated for new categories
const iconMap = {
  'Camera': Camera,
  'Bell': Bell,
  'Lightbulb': Lightbulb,
  'Cpu': Cpu,
  'ToggleRight': ToggleRight,
  'Plug': Plug,
  'Blinds': Blinds,
  'Monitor': Monitor,
  'Wifi': Wifi,
  'Shield': Shield,
  'Home': Home,
  'Package': Package,
  'Lock': Lock,
  'Video': Video,
  'Flame': Flame,
  'Box': Box,
  'Zap': Zap,
  'Settings': Settings,
  'Router': Router,
};

// Category icon mapping for new categories
const categoryIconMap = {
  'Vidéosurveillance': 'Camera',
  'Alarme': 'Bell',
  'Contrôle d\'Accès': 'Lock',
  'Vidéophonie': 'Video',
  'Incendie': 'Flame',
  'Interrupteur': 'ToggleRight',
  'Prise': 'Plug',
  'Plaque': 'Box',
  'Coffret & Tableau': 'Zap',
  'Boîte & Monture': 'Box',
  'Éclairage': 'Lightbulb',
  'Domotique': 'Home',
  'Motorisation': 'Settings',
  'Réseau': 'Router',
  'Accessoire': 'Package',
};

// Component to render category icon
const CategoryIcon = ({ iconName, className = "w-4 h-4" }) => {
  const IconComponent = iconMap[iconName];
  if (IconComponent) {
    return <IconComponent className={className} />;
  }
  return <Package className={className} />;
};

// Cache for storing list state
const productCache = new Map();

const CatalogPage = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  
  // Generate cache key from filters
  const cacheKey = useMemo(() => {
    return searchParams.toString() || 'default';
  }, [searchParams]);
  
  // Data state
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  const [brands, setBrands] = useState([]);
  const [technologies, setTechnologies] = useState([]);
  const [priceRange, setPriceRange] = useState({ min: 0, max: 1000 });
  const [total, setTotal] = useState(0);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadingSubcategories, setLoadingSubcategories] = useState(false);
  const [error, setError] = useState(null);
  const [favorites, setFavorites] = useState([]);
  const [cartItems, setCartItems] = useState([]);
  const [addingToCart, setAddingToCart] = useState(null);
  const [togglingFavorite, setTogglingFavorite] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);
  const [categorySearch, setCategorySearch] = useState('');

  // Refs
  const sentinelRef = useRef(null);
  const prefetchSentinelRef = useRef(null);
  const isFetching = useRef(false);
  const observerRef = useRef(null);
  const prefetchObserverRef = useRef(null);
  const prefetchedData = useRef(null);

  // Get filters from URL
  const filters = useMemo(() => ({
    q: searchParams.get('q') || '',
    category: searchParams.get('category') || '',      // category_id (e.g., "videosurveillance")
    subcategory: searchParams.get('subcategory') || '', // subcategory_id (e.g., "videosurveillance__cameras")
    technology: searchParams.get('technology') || '',
    brand: searchParams.get('brand') || '',
    price_min: searchParams.get('price_min') || '',
    price_max: searchParams.get('price_max') || '',
    sort: searchParams.get('sort') || 'recent'
  }), [searchParams]);

  // Fetch subcategories when category changes
  const fetchSubcategories = useCallback(async (categoryId) => {
    if (!categoryId) {
      setSubcategories([]);
      return;
    }
    setLoadingSubcategories(true);
    try {
      const response = await api.get(`/categories/${categoryId}/children`);
      setSubcategories(response.data.children || []);
    } catch (err) {
      console.error('Error fetching subcategories:', err);
      setSubcategories([]);
    } finally {
      setLoadingSubcategories(false);
    }
  }, []);

  // Handle category selection - fetch subcategories
  useEffect(() => {
    if (filters.category) {
      setSelectedCategoryId(filters.category);
      fetchSubcategories(filters.category);
    } else {
      setSelectedCategoryId(null);
      setSubcategories([]);
    }
  }, [filters.category, fetchSubcategories]);

  const sortOptions = [
    { value: 'recent', label: 'Plus récents' },
    { value: 'oldest', label: 'Plus anciens' },
    { value: 'price_asc', label: 'Prix croissant' },
    { value: 'price_desc', label: 'Prix décroissant' },
    { value: 'name_asc', label: 'Nom A-Z' },
    { value: 'name_desc', label: 'Nom Z-A' },
    { value: 'popular', label: 'Populaires' },
    { value: 'quality', label: 'Recommandés' },
  ];

  // Save to cache
  const saveToCache = useCallback((items, cursorVal, hasMoreVal, totalVal) => {
    productCache.set(cacheKey, {
      items,
      cursor: cursorVal,
      hasMore: hasMoreVal,
      total: totalVal,
      scrollY: window.scrollY,
      timestamp: Date.now()
    });
  }, [cacheKey]);

  // Restore from cache
  const restoreFromCache = useCallback(() => {
    const cached = productCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
      setProducts(cached.items);
      setCursor(cached.cursor);
      setHasMore(cached.hasMore);
      setTotal(cached.total);
      setLoading(false);
      requestAnimationFrame(() => {
        window.scrollTo(0, cached.scrollY);
      });
      return true;
    }
    return false;
  }, [cacheKey]);

  // Deduplicate by id
  const deduplicateItems = (items) => {
    const seen = new Set();
    return items.filter(item => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  };

  // Fetch products - V2 API with hierarchical categories
  const fetchProducts = useCallback(async (cursorParam, append) => {
    if (isFetching.current) return;
    isFetching.current = true;
    
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (filters.q) params.append('q', filters.q);
      
      // V2: Use category_id for filtering
      // If subcategory is selected, use it. Otherwise, use category for hierarchical search
      if (filters.subcategory) {
        params.append('category_id', filters.subcategory);
      } else if (filters.category) {
        params.append('category', filters.category);
      }
      
      if (filters.technology) params.append('technology', filters.technology);
      if (filters.brand) params.append('brand', filters.brand);
      if (filters.price_min) params.append('price_min', filters.price_min);
      if (filters.price_max) params.append('price_max', filters.price_max);
      if (filters.sort) params.append('sort', filters.sort);
      if (cursorParam) params.append('cursor', cursorParam);
      params.append('limit', '12');

      const response = await api.get('/products?' + params.toString());
      const data = response.data;
      
      if (append) {
        setProducts(prev => deduplicateItems([...prev, ...data.items]));
      } else {
        setProducts(deduplicateItems(data.items));
      }
      
      setCursor(data.pagination.next_cursor);
      setHasMore(data.pagination.has_more);
      setTotal(data.pagination.total);
      
      // Save to cache
      setProducts(currentItems => {
        saveToCache(currentItems, data.pagination.next_cursor, data.pagination.has_more, data.pagination.total);
        return currentItems;
      });
      
      prefetchedData.current = null;
    } catch (err) {
      console.error('Error fetching products:', err);
      setError('Erreur de chargement. Vérifiez votre connexion.');
    }
    
    setLoading(false);
    setLoadingMore(false);
    isFetching.current = false;
  }, [filters, saveToCache]);

  // Prefetch next page - V2 API
  const prefetchNextPage = useCallback(async () => {
    if (!cursor || !hasMore || prefetchedData.current || isFetching.current) return;
    
    try {
      const params = new URLSearchParams();
      if (filters.q) params.append('q', filters.q);
      
      // V2: Same logic as fetchProducts
      if (filters.subcategory) {
        params.append('category_id', filters.subcategory);
      } else if (filters.category) {
        params.append('category', filters.category);
      }
      
      if (filters.technology) params.append('technology', filters.technology);
      if (filters.brand) params.append('brand', filters.brand);
      if (filters.price_min) params.append('price_min', filters.price_min);
      if (filters.price_max) params.append('price_max', filters.price_max);
      if (filters.sort) params.append('sort', filters.sort);
      params.append('cursor', cursor);
      params.append('limit', '12');

      const response = await api.get('/products?' + params.toString());
      prefetchedData.current = response.data;
    } catch (err) {
      // Silently fail prefetch
    }
  }, [cursor, hasMore, filters]);

  // Fetch initial data - V2 API
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [categoriesRes, brandsRes, techRes, priceRangeRes] = await Promise.all([
          api.get('/categories'),  // V2: returns {categories: [...], total}
          api.get('/products/brands/list'),
          api.get('/products/technologies/list'),
          api.get('/products/price-range')
        ]);
        
        // V2: Extract categories array from response
        const cats = categoriesRes.data.categories || categoriesRes.data || [];
        setCategories(cats);
        
        setBrands(brandsRes.data || []);
        setTechnologies(techRes.data || []);
        setPriceRange(priceRangeRes.data);

        if (user) {
          try {
            const [favRes, cartRes] = await Promise.all([
              api.get('/favorites'),
              api.get('/cart')
            ]);
            setFavorites(favRes.data.products?.map(p => p.id) || []);
            setCartItems(cartRes.data.items?.map(i => i.product_id) || []);
          } catch (err) {
            console.error('Error fetching user data:', err);
          }
        }
      } catch (error) {
        console.error('Error fetching initial data:', error);
      }
    };
    fetchInitialData();
  }, [user]);

  // Initial load or restore from cache
  useEffect(() => {
    const restored = restoreFromCache();
    if (!restored) {
      setProducts([]);
      setCursor(null);
      setHasMore(true);
      // Use timeout to ensure filters are updated in the next render cycle
      const timer = setTimeout(() => {
        fetchProducts(null, false);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [cacheKey, fetchProducts]); // Include fetchProducts to use updated filters

  // Scroll tracking
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 500);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Save current catalog URL for back navigation
  useEffect(() => {
    const currentUrl = window.location.pathname + window.location.search;
    sessionStorage.setItem('lastCatalogUrl', currentUrl);
  }, [searchParams]);

  // Restore scroll position and scroll to last clicked product when returning to catalog
  useEffect(() => {
    const lastClickedProductId = sessionStorage.getItem('lastClickedProductId');
    const savedScrollPosition = sessionStorage.getItem('catalogScrollPosition');
    
    if (products.length > 0 && (lastClickedProductId || savedScrollPosition)) {
      // Wait for DOM to render
      const timer = setTimeout(() => {
        if (lastClickedProductId) {
          const productElement = document.querySelector(`[data-product-id="${lastClickedProductId}"]`);
          if (productElement) {
            // Scroll to the product with some offset from top
            const rect = productElement.getBoundingClientRect();
            const scrollTop = window.scrollY + rect.top - 120; // 120px offset from top
            window.scrollTo({ top: Math.max(0, scrollTop), behavior: 'instant' });
            
            // Highlight the product briefly
            productElement.style.transition = 'box-shadow 0.3s ease';
            productElement.style.boxShadow = '0 0 0 3px rgba(6, 182, 212, 0.5)';
            setTimeout(() => {
              productElement.style.boxShadow = '';
            }, 1500);
          }
          sessionStorage.removeItem('lastClickedProductId');
        } else if (savedScrollPosition) {
          // Fallback to saved scroll position
          const scrollPos = parseInt(savedScrollPosition, 10);
          window.scrollTo({ top: scrollPos, behavior: 'instant' });
        }
        sessionStorage.removeItem('catalogScrollPosition');
      }, 200);
      
      return () => clearTimeout(timer);
    }
  }, [products]);

  // Close category dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (showCategoryDropdown && !e.target.closest('[data-testid="category-dropdown-btn"]') && !e.target.closest('.category-dropdown-menu')) {
        setShowCategoryDropdown(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [showCategoryDropdown]);

  // IntersectionObserver for infinite scroll
  useEffect(() => {
    if (loading || !hasMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isFetching.current && cursor) {
          if (prefetchedData.current) {
            const data = prefetchedData.current;
            setProducts(prev => deduplicateItems([...prev, ...data.items]));
            setCursor(data.pagination.next_cursor);
            setHasMore(data.pagination.has_more);
            prefetchedData.current = null;
          } else {
            fetchProducts(cursor, true);
          }
        }
      },
      { threshold: 0.1 }
    );

    if (sentinelRef.current) {
      observer.observe(sentinelRef.current);
    }
    observerRef.current = observer;

    return () => {
      if (observerRef.current) observerRef.current.disconnect();
    };
  }, [loading, hasMore, cursor, fetchProducts]);

  // Prefetch observer
  useEffect(() => {
    if (loading || !hasMore || !cursor) return;

    const prefetchObserver = new IntersectionObserver(
      (entries) => {
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

    return () => {
      if (prefetchObserverRef.current) prefetchObserverRef.current.disconnect();
    };
  }, [loading, hasMore, cursor, prefetchNextPage]);

  // Update URL
  const updateURL = useCallback((newFilters) => {
    const params = new URLSearchParams();
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value && value !== '' && !(key === 'sort' && value === 'recent')) {
        params.set(key, value);
      }
    });
    setSearchParams(params);
  }, [setSearchParams]);

  // Handle filter change
  const handleFilterChange = (key, value) => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    productCache.delete(cacheKey);
    
    let newFilters = { ...filters, [key]: value };
    
    // Reset subcategory when category changes
    if (key === 'category') {
      newFilters.subcategory = '';
    }
    
    updateURL(newFilters);
  };

  // Handle subcategory selection
  const handleSubcategoryChange = (subcategoryId) => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    productCache.delete(cacheKey);
    updateURL({ ...filters, subcategory: subcategoryId });
  };

  // Clear all filters
  const clearFilters = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    productCache.delete(cacheKey);
    setSearchParams(new URLSearchParams());
  };

  // Handle search
  const handleSearch = (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    productCache.delete(cacheKey);
    
    // Track search event
    if (filters.q && filters.q.trim()) {
      analytics.search(filters.q.trim());
    }
    
    updateURL(filters);
  };

  // Check if any filter is active
  const hasActiveFilters = filters.q || filters.category || filters.subcategory || filters.technology || filters.brand || filters.price_min || filters.price_max || filters.sort !== 'recent';

  // Get the currently selected category object
  const selectedCategory = useMemo(() => {
    return categories.find(cat => cat.id === filters.category);
  }, [categories, filters.category]);

  // Get the currently selected subcategory object
  const selectedSubcategory = useMemo(() => {
    return subcategories.find(sub => sub.id === filters.subcategory);
  }, [subcategories, filters.subcategory]);

  // Retry on error
  const handleRetry = () => {
    if (cursor) {
      fetchProducts(cursor, true);
    } else {
      fetchProducts(null, false);
    }
  };

  // Scroll to top
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleAddToCart = async (productId) => {
    if (!user) {
      navigate('/login', { state: { from: '/catalog', message: 'Connectez-vous pour ajouter au panier' } });
      return;
    }
    setAddingToCart(productId);
    try {
      await api.post('/cart', { product_id: productId, quantity: 1 });
      setCartItems([...cartItems, productId]);
      
      // Track add to cart event
      const product = products.find(p => p.id === productId);
      if (product) {
        analytics.addToCart(productId, product.name, 1);
      }
    } catch (error) {
      console.error('Error adding to cart:', error);
      alert('Erreur lors de l\'ajout au panier');
    } finally {
      setAddingToCart(null);
    }
  };

  const handleToggleFavorite = async (productId) => {
    if (!user) {
      navigate('/login', { state: { from: '/catalog', message: 'Connectez-vous pour ajouter aux favoris' } });
      return;
    }
    setTogglingFavorite(productId);
    try {
      if (favorites.includes(productId)) {
        await api.delete('/favorites/' + productId);
        setFavorites(favorites.filter(id => id !== productId));
      } else {
        await api.post('/favorites', { product_id: productId });
        setFavorites([...favorites, productId]);
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
    } finally {
      setTogglingFavorite(null);
    }
  };

  // Skeleton loader
  const renderSkeletons = () => {
    return Array.from({ length: 12 }).map((_, i) => (
      <div key={'skeleton-' + i} className="bg-white rounded-xl shadow-md overflow-hidden animate-pulse">
        <div className="h-48 bg-gray-200"></div>
        <div className="p-4 space-y-3">
          <div className="flex justify-between">
            <div className="h-3 w-20 bg-gray-200 rounded"></div>
            <div className="h-5 w-16 bg-gray-200 rounded"></div>
          </div>
          <div className="h-5 w-3/4 bg-gray-200 rounded"></div>
          <div className="h-4 w-full bg-gray-200 rounded"></div>
          <div className="h-4 w-2/3 bg-gray-200 rounded"></div>
          <div className="pt-3 border-t flex justify-between items-center">
            <div className="h-6 w-24 bg-gray-200 rounded"></div>
            <div className="h-10 w-24 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    ));
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <SEO 
        title="Boutique Smart Home - Produits Domotique | SmartHome Tunisie"
        description="Achetez vos équipements smart home : caméras, détecteurs, ampoules connectées, interrupteurs WiFi, capteurs intelligents. Livraison en Tunisie. Prix en Dinar Tunisien."
        keywords="boutique domotique, produits smart home, équipements connectés tunisie, caméra wifi, ampoule connectée, interrupteur intelligent, capteur domotique"
        url="/catalog"
      />
      <Header />

      {/* Hero Header */}
      <section className="bg-gradient-to-r from-purple-600 to-cyan-500 text-white py-10">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold mb-2" data-testid="catalog-title">
                Catalogue Produits
              </h1>
              <p className="text-blue-100">
                Découvrez notre sélection de produits domotiques
              </p>
            </div>
            {user && (
              <button
                onClick={() => navigate('/dashboard/cart')}
                className="flex items-center gap-2 bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition-colors"
                data-testid="view-cart-btn"
              >
                <ShoppingCart className="w-5 h-5" />
                <span>Mon Panier</span>
                {cartItems.length > 0 && (
                  <span className="bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-0.5 rounded-full">
                    {cartItems.length}
                  </span>
                )}
              </button>
            )}
          </div>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="mt-6 max-w-2xl">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher un produit..."
                value={filters.q}
                onChange={(e) => handleFilterChange('q', e.target.value)}
                className="w-full pl-12 pr-4 py-3 rounded-xl text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-cyan-300 focus:outline-none"
                data-testid="search-input"
              />
              {filters.q && (
                <button
                  type="button"
                  onClick={() => handleFilterChange('q', '')}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          </form>
        </div>
      </section>

      {/* Categories - Desktop: horizontal buttons, Mobile: dropdown with search */}
      {categories.length > 0 && (
        <section className="bg-white py-4 border-b shadow-sm">
          <div className="container mx-auto px-4">
            
            {/* Desktop: Horizontal category buttons */}
            <div className="hidden md:flex flex-wrap gap-2">
              <button
                onClick={() => handleFilterChange('category', '')}
                data-testid="category-all-btn"
                className={'px-4 py-2 rounded-full text-sm font-medium transition-colors ' +
                  (!filters.category
                    ? 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200')}
              >
                Tous
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => handleFilterChange('category', cat.id)}
                  data-testid={`category-btn-${cat.id}`}
                  className={'px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2 ' +
                    (filters.category === cat.id
                      ? 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200')}
                >
                  <CategoryIcon iconName={cat.icon} className="w-4 h-4" />
                  {cat.label || cat.name}
                </button>
              ))}
            </div>

            {/* Mobile: Dropdown with search */}
            <div className="md:hidden relative">
              <button
                onClick={() => setShowCategoryDropdown(!showCategoryDropdown)}
                data-testid="category-dropdown-btn"
                className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-medium hover:opacity-90 transition-all"
              >
                <Package className="w-4 h-4" />
                <span>Catégorie</span>
                <span className="px-2 py-0.5 bg-white/20 rounded text-sm">
                  {selectedCategory?.label || selectedCategory?.name || 'Tous'}
                </span>
                <svg className={'w-4 h-4 transition-transform ' + (showCategoryDropdown ? 'rotate-180' : '')} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {showCategoryDropdown && (
                <div className="absolute top-full left-0 mt-2 w-72 bg-white rounded-xl shadow-xl border border-gray-100 py-2 z-50 max-h-96 overflow-hidden flex flex-col category-dropdown-menu">
                  {/* Search input */}
                  <div className="px-3 pb-2 border-b">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Rechercher une catégorie..."
                        value={categorySearch}
                        onChange={(e) => setCategorySearch(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        autoFocus
                      />
                    </div>
                  </div>
                  
                  {/* Category list */}
                  <div className="overflow-y-auto flex-1">
                    {/* "Tous" option - always visible */}
                    {(!categorySearch || 'tous'.includes(categorySearch.toLowerCase())) && (
                      <button
                        onClick={() => { handleFilterChange('category', ''); setShowCategoryDropdown(false); setCategorySearch(''); }}
                        className={'w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-gray-50 transition-colors ' +
                          (!filters.category ? 'bg-purple-50 text-purple-700 font-medium' : 'text-gray-700')}
                      >
                        <div className={'w-8 h-8 rounded-lg flex items-center justify-center ' + 
                          (!filters.category ? 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white' : 'bg-gray-100')}>
                          <Home className="w-4 h-4" />
                        </div>
                        <span>Tous</span>
                        {!filters.category && <Check className="w-4 h-4 ml-auto text-purple-600" />}
                      </button>
                    )}
                    
                    {/* Filtered categories */}
                    {categories
                      .filter(cat => !categorySearch || (cat.label || cat.name).toLowerCase().includes(categorySearch.toLowerCase()))
                      .map((cat) => (
                        <button
                          key={cat.id}
                          onClick={() => { handleFilterChange('category', cat.id); setShowCategoryDropdown(false); setCategorySearch(''); }}
                          className={'w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-gray-50 transition-colors ' +
                            (filters.category === cat.id ? 'bg-purple-50 text-purple-700 font-medium' : 'text-gray-700')}
                        >
                          <div className={'w-8 h-8 rounded-lg flex items-center justify-center ' + 
                            (filters.category === cat.id ? 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white' : 'bg-gray-100')}>
                            <CategoryIcon iconName={cat.icon} className="w-4 h-4" />
                          </div>
                          <span>{cat.label || cat.name}</span>
                          {filters.category === cat.id && <Check className="w-4 h-4 ml-auto text-purple-600" />}
                        </button>
                      ))}
                    
                    {/* No results */}
                    {categorySearch && categories.filter(cat => (cat.label || cat.name).toLowerCase().includes(categorySearch.toLowerCase())).length === 0 && !('tous'.includes(categorySearch.toLowerCase())) && (
                      <div className="px-4 py-3 text-sm text-gray-500 text-center">
                        Aucune catégorie trouvée
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Subcategories - Show when a category is selected */}
      {filters.category && (subcategories.length > 0 || loadingSubcategories) && (
        <section className="bg-gray-50 py-3 border-b" data-testid="subcategories-section">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-2 mb-2">
              <ChevronRight className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600 font-medium">
                {selectedCategory?.label || selectedCategory?.name}
              </span>
            </div>
            
            {loadingSubcategories ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Chargement des sous-catégories...</span>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleSubcategoryChange('')}
                  data-testid="subcategory-all-btn"
                  className={'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ' +
                    (!filters.subcategory
                      ? 'bg-cyan-500 text-white'
                      : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-100')}
                >
                  Tout voir ({subcategories.reduce((acc, sub) => acc + (sub.products_count || 0), 0)})
                </button>
                {subcategories.map((sub) => (
                  <button
                    key={sub.id}
                    onClick={() => handleSubcategoryChange(sub.id)}
                    data-testid={`subcategory-btn-${sub.id}`}
                    className={'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ' +
                      (filters.subcategory === sub.id
                        ? 'bg-cyan-500 text-white'
                        : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-100')}
                  >
                    {sub.label}
                    {sub.products_count > 0 && (
                      <span className={`text-xs ${filters.subcategory === sub.id ? 'text-cyan-100' : 'text-gray-400'}`}>
                        ({sub.products_count})
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Filters Bar */}
      <section className="bg-white border-b sticky top-0 z-30">
        <div className="container mx-auto px-4 py-3">
          <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
            <div className="flex items-center gap-4 flex-wrap">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={'flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ' +
                  (showFilters ? 'bg-cyan-50 border-cyan-500 text-cyan-700' : 'border-gray-300 hover:bg-gray-50')}
              >
                <SlidersHorizontal className="w-4 h-4" />
                Filtres
                {hasActiveFilters && (
                  <span className="bg-cyan-500 text-white text-xs px-2 py-0.5 rounded-full">!</span>
                )}
              </button>
              
              <span className="text-sm text-gray-600">
                {total} produit{total > 1 ? 's' : ''} trouvé{total > 1 ? 's' : ''}
              </span>

              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1"
                >
                  <X className="w-4 h-4" />
                  Effacer les filtres
                </button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <ArrowUpDown className="w-4 h-4 text-gray-500" />
              <select
                value={filters.sort}
                onChange={(e) => handleFilterChange('sort', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cyan-500"
                data-testid="sort-select"
              >
                {sortOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Expanded Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Technologie</label>
                <select
                  value={filters.technology}
                  onChange={(e) => handleFilterChange('technology', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cyan-500"
                  data-testid="technology-filter"
                >
                  <option value="">Toutes technologies</option>
                  {technologies.map((tech) => (
                    <option key={tech} value={tech}>{tech}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Marque</label>
                <select
                  value={filters.brand}
                  onChange={(e) => handleFilterChange('brand', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cyan-500"
                  data-testid="brand-filter"
                >
                  <option value="">Toutes les marques</option>
                  {brands.map((brand) => (
                    <option key={brand} value={brand}>{brand}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prix min (DT)</label>
                <input
                  type="number"
                  min="0"
                  step="0.001"
                  placeholder={priceRange.min?.toFixed(0) || "0"}
                  value={filters.price_min}
                  onChange={(e) => handleFilterChange('price_min', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cyan-500"
                  data-testid="price-min-filter"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prix max (DT)</label>
                <input
                  type="number"
                  min="0"
                  step="0.001"
                  placeholder={priceRange.max?.toFixed(0) || "1000"}
                  value={filters.price_max}
                  onChange={(e) => handleFilterChange('price_max', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cyan-500"
                  data-testid="price-max-filter"
                />
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Products Grid */}
      <section className="py-8 flex-1">
        <div className="container mx-auto px-4">
          {loading && products.length === 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {renderSkeletons()}
            </div>
          ) : products.length === 0 && !loading ? (
            <div className="text-center py-20">
              <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg mb-2">Aucun produit trouvé</p>
              <p className="text-gray-400 mb-4">Essayez de modifier vos filtres de recherche</p>
              <button
                onClick={clearFilters}
                className="text-cyan-600 hover:text-cyan-700 font-medium"
              >
                Voir tous les produits
              </button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {products.map((product) => (
                  <Link
                    key={product.id}
                    to={'/catalog/' + product.id}
                    data-testid={'product-' + product.id}
                    data-product-id={product.id}
                    onClick={() => {
                      // Save scroll position before navigating to product
                      sessionStorage.setItem('catalogScrollPosition', window.scrollY.toString());
                      sessionStorage.setItem('lastClickedProductId', product.id);
                    }}
                    className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden group block"
                  >
                    <div className="relative h-48 bg-white border-b">
                      {(product.image || product.image_url) ? (
                        <img
                          src={product.image || product.image_url}
                          alt={product.name}
                          className="h-full w-full object-contain p-2 group-hover:scale-105 transition-transform duration-300"
                          loading="lazy"
                          referrerPolicy="no-referrer"
                          onError={(e) => { 
                            e.target.onerror = null;
                            e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjIwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IiNGM0Y0RjYiLz48cGF0aCBkPSJNNjAgMTIwTDgwIDEwMEwxMDAgMTIwTTEyMCAxMDBMMTQwIDEyME02MCAxMjBMMTQwIDEyMCIgc3Ryb2tlPSIjRDFENURCIiBzdHJva2Utd2lkdGg9IjIiLz48Y2lyY2xlIGN4PSIxMjAiIGN5PSI3MCIgcj0iMTAiIGZpbGw9IiNEMUQ1REIiLz48L3N2Zz4=';
                          }}
                        />
                      ) : (
                        <div className="h-full w-full flex items-center justify-center bg-gray-100">
                          <svg className="w-16 h-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </div>
                      )}
                      {product.is_featured && (
                        <span className="absolute top-2 right-10 px-2 py-1 bg-yellow-400 text-yellow-900 text-xs font-bold rounded-full">
                          Populaire
                        </span>
                      )}
                      {(product.youtube_url || (product.videos && product.videos.length > 0)) && (
                        <span className="absolute top-2 left-2 px-2 py-1 bg-red-600 text-white text-xs font-bold rounded-full flex items-center gap-1 shadow-lg">
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg>
                          Vidéo
                        </span>
                      )}
                      <button
                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleToggleFavorite(product.id); }}
                        disabled={togglingFavorite === product.id}
                        className={'absolute top-2 right-2 p-1.5 rounded-full transition-all ' +
                          (favorites.includes(product.id)
                            ? 'bg-red-500 text-white'
                            : 'bg-white/80 text-gray-600 hover:bg-red-100 hover:text-red-500')}
                        data-testid={'favorite-btn-' + product.id}
                      >
                        <Heart className={'w-4 h-4 ' + (favorites.includes(product.id) ? 'fill-current' : '')} />
                      </button>
                    </div>
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-gray-500">{product.category}</span>
                      </div>
                      <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-1">{product.name}</h3>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{product.description}</p>
                      <div className="flex items-center justify-between pt-3 border-t">
                        {product.price ? (
                          <span className="text-xl font-bold text-cyan-600">
                            {product.price.toFixed(3)} DT
                          </span>
                        ) : (
                          <span className="text-sm text-gray-500">Prix sur demande</span>
                        )}
                        <button
                          onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleAddToCart(product.id); }}
                          disabled={addingToCart === product.id || cartItems.includes(product.id)}
                          className={'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ' +
                            (cartItems.includes(product.id)
                              ? 'bg-green-500 text-white cursor-default'
                              : 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white hover:opacity-90')}
                          data-testid={'add-cart-btn-' + product.id}
                        >
                          {addingToCart === product.id ? (
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          ) : cartItems.includes(product.id) ? (
                            <>
                              <Check className="w-4 h-4" />
                              <span>Ajouté</span>
                            </>
                          ) : (
                            <>
                              <ShoppingCart className="w-4 h-4" />
                              <span>Panier</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>

              {/* Prefetch sentinel */}
              <div ref={prefetchSentinelRef} style={{ height: '1px' }} aria-hidden="true" />

              {/* Loading sentinel */}
              <div ref={sentinelRef} className="py-8 flex flex-col items-center gap-4">
                {loadingMore && (
                  <div className="flex items-center gap-2 text-gray-500">
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
                
                {!hasMore && products.length > 0 && !error && (
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
              </div>
            </>
          )}
        </div>
      </section>

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

      <Footer />
    </div>
  );
};

export default CatalogPage;
