import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { ShoppingCart, Trash2, Plus, Minus, Send, AlertCircle, Gift, Star } from 'lucide-react';

function CartPage() {
  var navigate = useNavigate();
  var [cart, setCart] = useState({ items: [], total: 0 });
  var [loading, setLoading] = useState(true);
  var [updatingItem, setUpdatingItem] = useState(null);
  var [submitting, setSubmitting] = useState(false);
  var [success, setSuccess] = useState(false);
  var [loyaltyPoints, setLoyaltyPoints] = useState({ points: 0, redemption_value: 0 });
  var [usePoints, setUsePoints] = useState(false);
  var [orderResult, setOrderResult] = useState(null);

  useEffect(function() {
    loadCart();
    loadLoyaltyPoints();
  }, []);

  async function loadCart() {
    try {
      var response = await api.get('/cart');
      setCart(response.data);
    } catch (error) {
      console.error('Error loading cart:', error);
    }
    setLoading(false);
  }

  async function loadLoyaltyPoints() {
    try {
      var response = await api.get('/loyalty-points');
      setLoyaltyPoints(response.data);
    } catch (error) {
      console.error('Error loading loyalty points:', error);
    }
  }

  async function updateQty(pid, qty) {
    if (qty < 1) return;
    setUpdatingItem(pid);
    try {
      await api.put('/cart/' + pid, { quantity: qty });
      loadCart();
    } catch (e) {
      console.error(e);
    }
    setUpdatingItem(null);
  }

  async function removeItem(pid) {
    setUpdatingItem(pid);
    try {
      await api.delete('/cart/' + pid);
      loadCart();
    } catch (e) {
      console.error(e);
    }
    setUpdatingItem(null);
  }

  async function clearCart() {
    if (!window.confirm('Vider le panier ?')) return;
    setLoading(true);
    try {
      await api.delete('/cart');
      setCart({ items: [], total: 0 });
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }

  async function validateCart() {
    if (!window.confirm('Confirmer l\'envoi de votre demande ?')) return;
    setSubmitting(true);
    try {
      var response = await api.post('/cart/validate?use_points=' + usePoints);
      setSuccess(true);
      setOrderResult(response.data);
      setCart({ items: [], total: 0 });
      loadLoyaltyPoints(); // Refresh points
    } catch (e) {
      alert(e.response?.data?.detail || 'Erreur');
    }
    setSubmitting(false);
  }

  function goToCatalog() { navigate('/catalogue'); }
  function goToRequests() { navigate('/dashboard/my-purchase-requests'); }

  // Calculate totals
  var cartTotal = cart.total || 0;
  var discount = usePoints ? Math.min(loyaltyPoints.redemption_value, cartTotal) : 0;
  var pointsToUse = discount > 0 ? Math.floor(discount / 5 * 100) : 0;
  var totalAfterDiscount = cartTotal - discount;
  var tva = totalAfterDiscount * 0.19;
  var timbreFiscal = 1;
  var totalTTC = totalAfterDiscount + tva + timbreFiscal;

  function renderCartItem(item) {
    var pid = item.product_id;
    var prod = item.product;
    var qty = item.quantity;
    var sub = item.subtotal;
    
    return (
      <div key={pid} className="bg-white rounded-xl shadow-sm p-4 flex gap-4">
        <div className="w-20 h-20 bg-gray-100 rounded-lg flex-shrink-0">
          {prod.image_url && <img src={prod.image_url} alt="" className="w-full h-full object-contain" />}
        </div>
        <div className="flex-1">
          <div className="flex justify-between">
            <h3 className="font-semibold">{prod.name}</h3>
            <button onClick={function() { removeItem(pid); }} className="text-gray-400 hover:text-red-500">
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
          <p className="text-sm text-gray-500">{prod.category}</p>
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <button onClick={function() { updateQty(pid, qty - 1); }} disabled={updatingItem === pid || qty <= 1} className="w-8 h-8 rounded border flex items-center justify-center disabled:opacity-50">
                <Minus className="w-4 h-4" />
              </button>
              <span className="w-8 text-center">{qty}</span>
              <button onClick={function() { updateQty(pid, qty + 1); }} disabled={updatingItem === pid} className="w-8 h-8 rounded border flex items-center justify-center disabled:opacity-50">
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <span className="font-bold text-cyan-600">{sub ? sub.toFixed(3) : '—'} DT</span>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (success) {
    return (
      <DashboardLayout>
        <div className="max-w-2xl mx-auto text-center py-12">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Send className="w-10 h-10 text-green-500" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Demande envoyée !</h1>
          <p className="text-gray-600 mb-4">Nous vous contacterons prochainement.</p>
          
          {orderResult && orderResult.points_used > 0 && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6 text-left max-w-sm mx-auto">
              <p className="text-purple-800">
                <Star className="w-5 h-5 inline mr-2" />
                <strong>{orderResult.points_used} points</strong> utilisés pour une remise de <strong>{orderResult.discount.toFixed(3)} DT</strong>
              </p>
            </div>
          )}
          
          <div className="flex gap-4 justify-center">
            <button onClick={goToRequests} className="px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600">
              Voir mes demandes
            </button>
            <button onClick={goToCatalog} className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50">
              Continuer
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  var cartItems = cart.items || [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <ShoppingCart className="w-7 h-7 text-cyan-500" />
            Mon Panier ({cartItems.length})
          </h1>
          {cartItems.length > 0 && (
            <button onClick={clearCart} className="text-red-600 text-sm flex items-center gap-1">
              <Trash2 className="w-4 h-4" /> Vider
            </button>
          )}
        </div>

        {/* Loyalty Points Banner */}
        {loyaltyPoints.points > 0 && (
          <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl p-4 flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                <Gift className="w-6 h-6" />
              </div>
              <div>
                <p className="font-bold text-lg">{loyaltyPoints.points} points de fidélité</p>
                <p className="text-sm text-white/80">Valeur: {loyaltyPoints.redemption_value.toFixed(3)} DT (100 pts = 5 DT)</p>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-lg">
              <Star className="w-5 h-5" />
              <span className="text-sm">1 DT dépensé = 1 point gagné</span>
            </div>
          </div>
        )}

        {cartItems.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <ShoppingCart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Panier vide</h2>
            <button onClick={goToCatalog} className="mt-4 px-6 py-3 bg-cyan-500 text-white rounded-lg">
              Voir le catalogue
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              {cartItems.map(renderCartItem)}
            </div>
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-sm p-6 sticky top-6">
                <h2 className="text-lg font-semibold mb-4">Récapitulatif</h2>
                
                {/* Use Points Option */}
                {loyaltyPoints.points >= 100 && cartTotal > 0 && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={usePoints}
                        onChange={function(e) { setUsePoints(e.target.checked); }}
                        className="mt-1 w-5 h-5 text-purple-600 rounded"
                        data-testid="use-points-checkbox"
                      />
                      <div>
                        <p className="font-semibold text-purple-800">Utiliser mes points</p>
                        <p className="text-sm text-purple-600">
                          {pointsToUse} points = -{discount.toFixed(3)} DT
                        </p>
                      </div>
                    </label>
                  </div>
                )}

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Sous-total HT</span>
                    <span>{cartTotal.toFixed(3)} DT</span>
                  </div>
                  {discount > 0 && (
                    <div className="flex justify-between text-purple-600">
                      <span>Remise fidélité</span>
                      <span>-{discount.toFixed(3)} DT</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600">TVA (19%)</span>
                    <span>{tva.toFixed(3)} DT</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Timbre fiscal</span>
                    <span>{timbreFiscal.toFixed(3)} DT</span>
                  </div>
                </div>

                <div className="border-t pt-3 mt-3 flex justify-between text-lg font-bold">
                  <span>Total TTC</span>
                  <span className="text-cyan-600">{totalTTC.toFixed(3)} DT</span>
                </div>

                {cartTotal > 0 && (
                  <p className="text-xs text-green-600 mt-2 flex items-center gap-1">
                    <Star className="w-4 h-4" />
                    Vous gagnerez {Math.floor(totalAfterDiscount)} points avec cette commande
                  </p>
                )}

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 my-4 flex gap-2">
                  <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                  <p className="text-sm text-amber-800">Pas de paiement en ligne. Notre équipe vous contactera.</p>
                </div>

                <button 
                  onClick={validateCart} 
                  disabled={submitting} 
                  className="w-full py-3 bg-cyan-500 text-white font-semibold rounded-lg hover:bg-cyan-600 disabled:opacity-50 flex items-center justify-center gap-2"
                  data-testid="validate-cart-btn"
                >
                  {submitting ? 'Envoi...' : <React.Fragment><Send className="w-5 h-5" />Envoyer la demande</React.Fragment>}
                </button>
                <button onClick={goToCatalog} className="w-full mt-3 py-3 border border-gray-300 rounded-lg hover:bg-gray-50">
                  Continuer mes achats
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default CartPage;
