import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { Heart, ShoppingCart, Trash2 } from 'lucide-react';

const FavoritesPage = () => {
  const navigate = useNavigate();
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState(null);
  const [addingToCart, setAddingToCart] = useState(null);

  const loadFavorites = async () => {
    try {
      const response = await api.get('/favorites');
      setFavorites(response.data.products || []);
    } catch (error) {
      console.error('Error loading favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFavorites();
  }, []);

  const handleRemove = async (productId) => {
    setRemovingId(productId);
    try {
      await api.delete(`/favorites/${productId}`);
      setFavorites(favorites.filter(p => p.id !== productId));
    } catch (error) {
      console.error('Error removing from favorites:', error);
    } finally {
      setRemovingId(null);
    }
  };

  const handleAddToCart = async (productId) => {
    setAddingToCart(productId);
    try {
      await api.post('/cart', { product_id: productId, quantity: 1 });
      alert('Produit ajouté au panier !');
    } catch (error) {
      console.error('Error adding to cart:', error);
      alert('Erreur lors de l\'ajout au panier');
    } finally {
      setAddingToCart(null);
    }
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
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Heart className="w-7 h-7 text-red-500" />
            Mes Favoris
          </h1>
          <p className="text-gray-500 mt-1">
            {favorites.length} produit(s) sauvegardé(s)
          </p>
        </div>

        {favorites.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Heart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Aucun favori</h2>
            <p className="text-gray-500 mb-6">Parcourez notre catalogue et sauvegardez vos produits préférés</p>
            <button
              onClick={() => navigate('/catalog')}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90"
            >
              Voir le catalogue
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {favorites.map((product) => (
              <div
                key={product.id}
                className="bg-white rounded-xl shadow-sm overflow-hidden group hover:shadow-lg transition-shadow"
              >
                <div className="relative h-40 bg-gray-100">
                  {product.image_url ? (
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="w-full h-full object-contain p-2"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <ShoppingCart className="w-12 h-12" />
                    </div>
                  )}
                  <button
                    onClick={() => handleRemove(product.id)}
                    disabled={removingId === product.id}
                    className="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                    title="Retirer des favoris"
                  >
                    {removingId === product.id ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                  {product.technology && (
                    <span className="absolute top-2 left-2 px-2 py-0.5 text-xs bg-cyan-500 text-white rounded">
                      {product.technology}
                    </span>
                  )}
                </div>
                <div className="p-4">
                  <p className="text-xs text-gray-500 mb-1">{product.category}</p>
                  <h3 className="font-semibold text-gray-900 line-clamp-1 mb-2">{product.name}</h3>
                  <p className="text-sm text-gray-600 line-clamp-2 mb-3">{product.description}</p>
                  <div className="flex items-center justify-between pt-3 border-t">
                    {product.price ? (
                      <span className="text-lg font-bold text-cyan-600">{product.price.toFixed(2)} €</span>
                    ) : (
                      <span className="text-sm text-gray-500">Prix sur demande</span>
                    )}
                    <button
                      onClick={() => handleAddToCart(product.id)}
                      disabled={addingToCart === product.id}
                      className="flex items-center gap-1 px-3 py-1.5 bg-gradient-to-r from-purple-600 to-cyan-500 text-white text-sm rounded-lg hover:opacity-90 disabled:opacity-50"
                    >
                      {addingToCart === product.id ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <>
                          <ShoppingCart className="w-4 h-4" />
                          <span>Panier</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default FavoritesPage;
