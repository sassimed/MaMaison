import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { TrendingUp, Package, DollarSign, ShoppingCart, AlertTriangle, BarChart3 } from 'lucide-react';

const AdminStatistics = () => {
  const [salesStats, setSalesStats] = useState(null);
  const [bestSellers, setBestSellers] = useState([]);
  const [inventoryStats, setInventoryStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const salesRes = await api.get('/admin/statistics/sales');
      const bestRes = await api.get('/admin/statistics/best-sellers?limit=10');
      const invRes = await api.get('/admin/statistics/inventory');
      setSalesStats(salesRes.data);
      setBestSellers(bestRes.data);
      setInventoryStats(invRes.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
    setLoading(false);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value || 0);
  };

  const renderMonthBar = (item, idx, maxRev) => {
    const height = Math.max((item.revenue / maxRev) * 100, 5);
    return (
      <div key={idx} className="flex flex-col items-center">
        <div className="w-full bg-gray-200 rounded-t-lg h-24 flex items-end">
          <div className="w-full bg-cyan-500 rounded-t-lg" style={{ height: height + '%' }}></div>
        </div>
        <span className="text-xs text-gray-500 mt-1">{item.month.slice(5)}</span>
        <span className="text-xs font-medium">{item.revenue.toFixed(0)}€</span>
      </div>
    );
  };

  const renderDayBar = (item, idx, maxRev) => {
    const height = Math.max((item.revenue / maxRev) * 100, 5);
    const dayName = new Date(item.date).toLocaleDateString('fr-FR', { weekday: 'short' });
    return (
      <div key={idx} className="flex flex-col items-center">
        <div className="w-full bg-gray-200 rounded-t-lg h-20 flex items-end">
          <div className="w-full bg-green-500 rounded-t-lg" style={{ height: height + '%' }}></div>
        </div>
        <span className="text-xs text-gray-500 mt-1 capitalize">{dayName}</span>
        <span className="text-xs font-medium">{item.revenue.toFixed(0)}€</span>
      </div>
    );
  };

  const renderBestSeller = (product, idx) => {
    const stockClass = product.stock_quantity === 0 
      ? 'bg-red-100 text-red-800' 
      : product.stock_quantity <= 5 
        ? 'bg-yellow-100 text-yellow-800' 
        : 'bg-green-100 text-green-800';
    
    return (
      <div key={product.product_id} className="flex items-center gap-4 bg-gray-50 rounded-xl p-4">
        <div className="w-8 h-8 bg-cyan-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
          {idx + 1}
        </div>
        <div className="w-16 h-16 bg-white rounded-lg flex-shrink-0 overflow-hidden">
          {product.image_url ? (
            <img src={product.image_url} alt="" className="w-full h-full object-contain" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-300">
              <Package className="w-8 h-8" />
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-gray-900 truncate">{product.name}</h4>
          <p className="text-sm text-gray-500">{product.category}</p>
        </div>
        <div className="text-right">
          <p className="font-bold text-cyan-600">{product.quantity_sold} vendus</p>
          <p className="text-sm text-gray-500">{formatCurrency(product.revenue)}</p>
        </div>
        <span className={'text-xs font-medium px-2 py-1 rounded-full ' + stockClass}>
          Stock: {product.stock_quantity}
        </span>
      </div>
    );
  };

  const renderStockProduct = (p, idx, type) => {
    const badgeClass = type === 'out' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800';
    const badgeText = type === 'out' ? 'Épuisé' : p.stock + ' restants';
    return (
      <div key={idx} className="flex justify-between items-center bg-white p-3 rounded-lg">
        <div>
          <p className="font-medium text-gray-900">{p.name}</p>
          <p className="text-sm text-gray-500">{p.category}</p>
        </div>
        <span className={'px-2 py-1 text-xs rounded-full ' + badgeClass}>{badgeText}</span>
      </div>
    );
  };

  const renderCategoryStock = (cat, idx) => (
    <div key={idx} className="flex justify-between items-center text-sm">
      <span className="text-gray-600">{cat.category}</span>
      <div className="flex gap-4">
        <span className="text-gray-900 font-medium">{cat.total_stock} unités</span>
        <span className="text-cyan-600">{formatCurrency(cat.value)}</span>
      </div>
    </div>
  );

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
        </div>
      </DashboardLayout>
    );
  }

  const monthlyData = salesStats ? salesStats.monthly_revenue.slice(-12) : [];
  const dailyData = salesStats ? salesStats.daily_revenue.slice(-7) : [];
  const maxMonthRev = Math.max(...monthlyData.map(r => r.revenue), 1);
  const maxDayRev = Math.max(...dailyData.map(r => r.revenue), 1);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <BarChart3 className="w-7 h-7 text-cyan-500" />
          Statistiques
        </h1>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm">
          <div className="border-b flex">
            <button onClick={() => setActiveTab('overview')} className={'px-6 py-3 text-sm font-medium border-b-2 ' + (activeTab === 'overview' ? 'border-cyan-500 text-cyan-600' : 'border-transparent text-gray-500')}>
              Vue d'ensemble
            </button>
            <button onClick={() => setActiveTab('products')} className={'px-6 py-3 text-sm font-medium border-b-2 ' + (activeTab === 'products' ? 'border-cyan-500 text-cyan-600' : 'border-transparent text-gray-500')}>
              Produits vendus
            </button>
            <button onClick={() => setActiveTab('inventory')} className={'px-6 py-3 text-sm font-medium border-b-2 ' + (activeTab === 'inventory' ? 'border-cyan-500 text-cyan-600' : 'border-transparent text-gray-500')}>
              Inventaire
            </button>
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && salesStats && (
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-green-500 rounded-xl p-5 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100 text-sm">Recette Totale</p>
                      <p className="text-2xl font-bold mt-1">{formatCurrency(salesStats.total_revenue)}</p>
                    </div>
                    <DollarSign className="w-10 h-10 text-green-200" />
                  </div>
                  <p className="text-green-100 text-xs mt-2">{salesStats.total_orders} commandes validées</p>
                </div>
                
                <div className="bg-cyan-500 rounded-xl p-5 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-cyan-100 text-sm">Ce Mois</p>
                      <p className="text-2xl font-bold mt-1">{formatCurrency(salesStats.month_revenue)}</p>
                    </div>
                    <TrendingUp className="w-10 h-10 text-cyan-200" />
                  </div>
                  <p className="text-cyan-100 text-xs mt-2">{salesStats.month_orders} commandes</p>
                </div>
                
                <div className="bg-purple-500 rounded-xl p-5 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-100 text-sm">Aujourd'hui</p>
                      <p className="text-2xl font-bold mt-1">{formatCurrency(salesStats.today_revenue)}</p>
                    </div>
                    <ShoppingCart className="w-10 h-10 text-purple-200" />
                  </div>
                  <p className="text-purple-100 text-xs mt-2">{salesStats.today_orders} commandes</p>
                </div>
                
                <div className="bg-orange-500 rounded-xl p-5 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-orange-100 text-sm">Panier Moyen</p>
                      <p className="text-2xl font-bold mt-1">
                        {formatCurrency(salesStats.total_orders > 0 ? salesStats.total_revenue / salesStats.total_orders : 0)}
                      </p>
                    </div>
                    <Package className="w-10 h-10 text-orange-200" />
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Recettes mensuelles</h3>
                <div className="grid grid-cols-6 md:grid-cols-12 gap-2">
                  {monthlyData.map((item, idx) => renderMonthBar(item, idx, maxMonthRev))}
                </div>
              </div>

              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Recettes des 7 derniers jours</h3>
                <div className="grid grid-cols-7 gap-2">
                  {dailyData.map((item, idx) => renderDayBar(item, idx, maxDayRev))}
                </div>
              </div>
            </div>
          )}

          {/* Products Tab */}
          {activeTab === 'products' && (
            <div className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Top 10 des produits les plus vendus</h3>
              {bestSellers.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Package className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p>Aucune vente enregistrée</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {bestSellers.map(renderBestSeller)}
                </div>
              )}
            </div>
          )}

          {/* Inventory Tab */}
          {activeTab === 'inventory' && inventoryStats && (
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white border rounded-xl p-5">
                  <p className="text-gray-500 text-sm">Total Produits</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{inventoryStats.total_products}</p>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-xl p-5">
                  <p className="text-green-700 text-sm">En stock (plus de 5)</p>
                  <p className="text-2xl font-bold text-green-800 mt-1">{inventoryStats.in_stock}</p>
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5">
                  <p className="text-yellow-700 text-sm">Stock faible (5 ou moins)</p>
                  <p className="text-2xl font-bold text-yellow-800 mt-1">{inventoryStats.low_stock}</p>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-xl p-5">
                  <p className="text-red-700 text-sm">Rupture de stock</p>
                  <p className="text-2xl font-bold text-red-800 mt-1">{inventoryStats.out_of_stock}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-purple-500 rounded-xl p-6 text-white">
                  <p className="text-purple-100 text-sm">Valeur totale du stock</p>
                  <p className="text-3xl font-bold mt-2">{formatCurrency(inventoryStats.total_stock_value)}</p>
                  <p className="text-purple-200 text-sm mt-2">{inventoryStats.total_items_in_stock} articles en stock</p>
                </div>
                <div className="bg-gray-50 rounded-xl p-6">
                  <h4 className="font-semibold text-gray-900 mb-3">Stock par catégorie</h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {inventoryStats.stock_by_category.map(renderCategoryStock)}
                  </div>
                </div>
              </div>

              {inventoryStats.products_by_stock.out_of_stock.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                  <h4 className="font-semibold text-red-900 mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    Produits en rupture de stock
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {inventoryStats.products_by_stock.out_of_stock.map((p, idx) => renderStockProduct(p, idx, 'out'))}
                  </div>
                </div>
              )}

              {inventoryStats.products_by_stock.low_stock.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                  <h4 className="font-semibold text-yellow-900 mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    Produits avec stock faible
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {inventoryStats.products_by_stock.low_stock.map((p, idx) => renderStockProduct(p, idx, 'low'))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminStatistics;
