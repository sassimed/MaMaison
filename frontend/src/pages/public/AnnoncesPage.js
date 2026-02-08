import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import { Megaphone, MapPin, Clock, Filter, ChevronRight, Search, Loader2, ArrowUp } from 'lucide-react';
import { SEO } from '../../components/SEO';

function AnnoncesPage() {
  const navigate = useNavigate();
  const auth = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [annonces, setAnnonces] = useState([]);
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [cursor, setCursor] = useState(null);
  const [total, setTotal] = useState(0);
  const [showScrollTop, setShowScrollTop] = useState(false);
  
  const selectedCity = searchParams.get('city') || '';
  const selectedCategory = searchParams.get('category') || '';

  const categories = [
    'Installation Caméra',
    'Système d\'Alarme',
    'Vidéophone',
    'Éclairage Connecté',
    'Domotique',
    'Maintenance'
  ];

  useEffect(() => {
    fetchCities();
    fetchAnnonces();
  }, [selectedCity, selectedCategory]);

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const fetchCities = async () => {
    try {
      const res = await api.get('/annonces/browse/cities');
      setCities(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAnnonces = async (cursorParam = null) => {
    if (cursorParam) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setAnnonces([]);
    }

    try {
      const params = new URLSearchParams();
      params.append('limit', '12');
      if (cursorParam) params.append('cursor', cursorParam);
      if (selectedCity) params.append('city', selectedCity);
      if (selectedCategory) params.append('category', selectedCategory);

      const res = await api.get('/annonces/browse?' + params.toString());
      const data = res.data;

      if (cursorParam) {
        setAnnonces(prev => [...prev, ...data.annonces]);
      } else {
        setAnnonces(data.annonces);
        setTotal(data.pagination.total);
      }

      setCursor(data.pagination.next_cursor);
      setHasMore(data.pagination.has_more);
    } catch (err) {
      console.error(err);
    }

    setLoading(false);
    setLoadingMore(false);
  };

  const loadMore = () => {
    if (cursor && hasMore && !loadingMore) {
      fetchAnnonces(cursor);
    }
  };

  const handleFilterChange = (key, value) => {
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    setSearchParams(params);
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <SEO 
        title="Trouver un Installateur - Annonces Domotique | SmartHome Tunisie"
        description="Consultez les annonces de demandes de service smart home en Tunisie. Professionnels, trouvez des missions d'installation vidéophone, alarme, caméra, éclairage connecté."
        keywords="annonces domotique, demandes service, professionnels tunisie, installation, maintenance, vidéophone, alarme, caméra"
        url="/annonces"
      />
      
      <Header />

      {/* Hero */}
      <section className="bg-gradient-to-r from-purple-600 to-cyan-500 text-white py-12">
        <div className="container mx-auto px-4 text-center">
          <Megaphone className="w-16 h-16 mx-auto mb-4 opacity-90" />
          <h1 className="text-3xl md:text-4xl font-bold mb-4">Annonces Domotique</h1>
          <p className="text-lg opacity-90 max-w-2xl mx-auto">
            Découvrez les demandes de service en domotique et sécurité. 
            Professionnels, trouvez de nouvelles missions près de chez vous.
          </p>
          {total > 0 && (
            <p className="mt-4 text-sm opacity-75">{total} annonces disponibles</p>
          )}
        </div>
      </section>

      {/* Filters */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-30">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2 text-gray-600">
              <Filter className="w-5 h-5" />
              <span className="font-medium">Filtres:</span>
            </div>
            
            <select
              value={selectedCity}
              onChange={(e) => handleFilterChange('city', e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            >
              <option value="">Toutes les villes</option>
              {cities.map(city => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
            
            <select
              value={selectedCategory}
              onChange={(e) => handleFilterChange('category', e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            >
              <option value="">Toutes catégories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>

            {(selectedCity || selectedCategory) && (
              <button
                onClick={() => setSearchParams({})}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Réinitialiser
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8 flex-1">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
          </div>
        ) : annonces.length === 0 ? (
          <div className="text-center py-16">
            <Megaphone className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">Aucune annonce trouvée</h2>
            <p className="text-gray-500">Modifiez vos filtres ou revenez plus tard.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {annonces.map(annonce => (
                <article 
                  key={annonce.id}
                  className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden border border-gray-100"
                >
                  <div className="p-5">
                    <div className="flex items-start justify-between mb-3">
                      <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                        {annonce.category}
                      </span>
                    </div>
                    
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                      {annonce.title}
                    </h3>
                    
                    <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                      {annonce.description}
                    </p>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {annonce.city}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatDate(annonce.published_at || annonce.created_at)}
                      </span>
                    </div>
                    
                    {auth.user && auth.user.role === 'PROFESSIONNEL' ? (
                      <Link
                        to={`/dashboard/annonces?respond=${annonce.id}`}
                        className="w-full py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-medium hover:from-purple-700 hover:to-cyan-600 transition-all flex items-center justify-center gap-2"
                      >
                        Répondre
                        <ChevronRight className="w-4 h-4" />
                      </Link>
                    ) : (
                      <Link
                        to="/login"
                        state={{ from: '/annonces', message: 'Connectez-vous en tant que professionnel pour répondre aux annonces' }}
                        className="w-full py-2 border border-purple-500 text-purple-600 rounded-lg font-medium hover:bg-purple-50 transition-all flex items-center justify-center gap-2"
                      >
                        Se connecter pour répondre
                      </Link>
                    )}
                  </div>
                </article>
              ))}
            </div>

            {/* Load more */}
            {hasMore && (
              <div className="text-center mt-8">
                <button
                  onClick={loadMore}
                  disabled={loadingMore}
                  className="px-8 py-3 bg-white border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  {loadingMore ? (
                    <span className="flex items-center gap-2">
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Chargement...
                    </span>
                  ) : (
                    'Voir plus d\'annonces'
                  )}
                </button>
              </div>
            )}

            {!hasMore && annonces.length > 0 && (
              <p className="text-center text-gray-500 mt-8">
                Vous avez vu toutes les annonces disponibles
              </p>
            )}
          </>
        )}
      </div>

      {/* CTA for clients */}
      <section className="bg-gradient-to-r from-cyan-500 to-purple-600 text-white py-12">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-2xl font-bold mb-4">Vous avez besoin d'un professionnel ?</h2>
          <p className="mb-6 opacity-90">Publiez votre annonce et recevez des propositions de professionnels qualifiés.</p>
          <Link
            to={auth.user ? "/dashboard/my-annonces" : "/register"}
            className="inline-block px-8 py-3 bg-white text-purple-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
          >
            {auth.user ? "Publier une annonce" : "Créer un compte"}
          </Link>
        </div>
      </section>

      <Footer />

      {/* Scroll to top */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 p-3 bg-purple-600 text-white rounded-full shadow-lg hover:bg-purple-700 transition-colors z-50"
        >
          <ArrowUp className="w-6 h-6" />
        </button>
      )}
    </div>
  );
}

export default AnnoncesPage;
