import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { Search, Filter, Plus, Edit2, Trash2, Eye, EyeOff, Image, X, Save, ChevronLeft, ChevronRight, Upload, Loader2 } from 'lucide-react';

const AdminProducts = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterNoImage, setFilterNoImage] = useState(false);
  const [imageStats, setImageStats] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, limit: 24, total: 0, pages: 1 });
  const [saving, setSaving] = useState(false);
  const [uploadingPrimary, setUploadingPrimary] = useState(false);
  const [uploadingGallery, setUploadingGallery] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    description: '',
    brand: '',
    price: '',
    category_label: '',
    subcategory_label: '',
    primary_image_url: '',
    images: [],
    connectivity: '',
    technologies: [],
    featured: false,
    active: true,
    stock_quantity: 0,
    specifications: [],
    videos: []
  });

  // Load data on mount
  useEffect(() => {
    loadCategories();
    loadImageStats();
  }, []);

  // Reload products when filters change
  useEffect(() => {
    loadProducts();
  }, [pagination.page, filterCategory, filterNoImage, searchQuery]);

  const loadCategories = async () => {
    try {
      const res = await api.get('/categories');
      // API returns array directly, not {categories: [...]}
      const cats = Array.isArray(res.data) ? res.data : (res.data.categories || []);
      setCategories(cats);
    } catch (err) {
      console.error('Error loading categories:', err);
    }
  };

  const loadImageStats = async () => {
    try {
      const res = await api.get('/admin/products-manage/stats/images');
      setImageStats(res.data);
    } catch (err) {
      console.error('Error loading image stats:', err);
    }
  };

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      let url = `/admin/products-manage?page=${pagination.page}&limit=${pagination.limit}`;
      
      if (filterCategory) {
        url += `&category=${encodeURIComponent(filterCategory)}`;
      }
      if (filterNoImage) {
        url += '&has_image=false';
      }
      if (searchQuery) {
        url += `&q=${encodeURIComponent(searchQuery)}`;
      }

      const res = await api.get(url);
      setProducts(res.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: res.data.total,
        pages: res.data.pages
      }));
    } catch (err) {
      console.error('Error loading products:', err);
    }
    setLoading(false);
  }, [pagination.page, pagination.limit, filterCategory, filterNoImage, searchQuery]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleEdit = async (product) => {
    try {
      // Fetch full product details
      const res = await api.get(`/admin/products-manage/${product.id}`);
      const fullProduct = res.data;
      
      setFormData({
        name: fullProduct.name || '',
        sku: fullProduct.sku || '',
        description: fullProduct.description || '',
        brand: fullProduct.brand || '',
        price: fullProduct.price || '',
        category_label: fullProduct.category_label || '',
        subcategory_label: fullProduct.subcategory_label || '',
        primary_image_url: fullProduct.primary_image_url || '',
        images: fullProduct.images || [],
        connectivity: fullProduct.attributes?.connectivity || '',
        technologies: fullProduct.attributes_norm?.technologies || [],
        featured: fullProduct.featured || false,
        active: fullProduct.active !== false,
        stock_quantity: fullProduct.stock_quantity || 0,
        specifications: fullProduct.specifications || [],
        videos: fullProduct.videos || []
      });
      setEditingProduct(fullProduct);
      setShowForm(true);
    } catch (err) {
      alert('Erreur lors du chargement du produit');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const data = {
      name: formData.name,
      sku: formData.sku,
      description: formData.description,
      brand: formData.brand,
      price: formData.price ? parseFloat(formData.price) : null,
      category_label: formData.category_label,
      subcategory_label: formData.subcategory_label,
      primary_image_url: formData.primary_image_url || null,
      images: formData.images || [],
      connectivity: formData.connectivity,
      technologies: formData.technologies || [],
      featured: formData.featured,
      active: formData.active,
      stock_quantity: parseInt(formData.stock_quantity) || 0
    };
    
    // Only include specifications if it's a non-empty object
    if (formData.specifications && typeof formData.specifications === 'object' && !Array.isArray(formData.specifications) && Object.keys(formData.specifications).length > 0) {
      data.specifications = formData.specifications;
    }
    
    // Only include videos if it's a non-empty array
    if (formData.videos && Array.isArray(formData.videos) && formData.videos.length > 0) {
      data.videos = formData.videos;
    }

    try {
      if (editingProduct) {
        await api.put(`/admin/products-manage/${editingProduct.id}`, data);
      } else {
        await api.post('/admin/products-manage', data);
      }
      setShowForm(false);
      setEditingProduct(null);
      resetForm();
      loadProducts();
      loadImageStats();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Erreur lors de la sauvegarde';
      alert(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
    }
    setSaving(false);
  };

  // Upload image file
  const uploadImage = async (file) => {
    const formDataUpload = new FormData();
    formDataUpload.append('file', file);
    
    const response = await api.post('/upload/image', formDataUpload, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    return response.data.url;
  };

  // Handle primary image upload
  const handlePrimaryImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setUploadingPrimary(true);
    try {
      const url = await uploadImage(file);
      setFormData({ ...formData, primary_image_url: url });
    } catch (err) {
      alert('Erreur lors de l\'upload de l\'image');
    }
    setUploadingPrimary(false);
  };

  // Handle gallery image upload
  const handleGalleryImageUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    
    setUploadingGallery(true);
    try {
      const uploadedUrls = [];
      for (const file of files) {
        const url = await uploadImage(file);
        uploadedUrls.push(url);
      }
      setFormData({ 
        ...formData, 
        images: [...(formData.images || []), ...uploadedUrls] 
      });
    } catch (err) {
      alert('Erreur lors de l\'upload des images');
    }
    setUploadingGallery(false);
  };

  const handleDelete = async (productId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce produit ?')) return;
    
    try {
      await api.delete(`/admin/products-manage/${productId}`);
      loadProducts();
      loadImageStats();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const handleToggleActive = async (product) => {
    try {
      await api.post(`/admin/products-manage/${product.id}/toggle-active`);
      loadProducts();
    } catch (err) {
      alert('Erreur lors de la modification');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      sku: '',
      description: '',
      brand: '',
      price: '',
      category_label: '',
      subcategory_label: '',
      primary_image_url: '',
      images: [],
      connectivity: '',
      technologies: [],
      featured: false,
      active: true,
      stock_quantity: 0,
      specifications: [],
      videos: []
    });
  };

  // Get subcategories for selected category
  const getSubcategories = () => {
    const cat = categories.find(c => c.label === formData.category_label);
    return cat?.subcategories || [];
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Gestion des Produits</h1>
            <p className="text-gray-500 text-sm mt-1">
              {pagination.total} produit{pagination.total > 1 ? 's' : ''} au total
            </p>
          </div>
          <button
            onClick={() => { setShowForm(!showForm); setEditingProduct(null); resetForm(); }}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            {showForm ? <X size={18} /> : <Plus size={18} />}
            {showForm ? 'Fermer' : 'Nouveau produit'}
          </button>
        </div>

        {/* Filters - Hidden when form is open */}
        {!showForm && (
          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex flex-wrap gap-4 items-center">
              {/* Search */}
              <form onSubmit={handleSearch} className="flex-1 min-w-[200px] max-w-md">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <input
                    type="text"
                    placeholder="Rechercher par nom, SKU, marque..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </form>

              {/* Category filter */}
              <div className="flex items-center gap-2">
                <Filter size={18} className="text-gray-400" />
                <select
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                  value={filterCategory}
                  onChange={(e) => { setFilterCategory(e.target.value); setPagination(prev => ({ ...prev, page: 1 })); }}
                >
                  <option value="">Toutes les catégories</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.label}>{cat.label}</option>
                  ))}
                </select>
              </div>

            {/* No image filter */}
            {imageStats && imageStats.without_image > 0 && (
              <button
                onClick={() => { setFilterNoImage(!filterNoImage); setPagination(prev => ({ ...prev, page: 1 })); }}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filterNoImage 
                    ? 'bg-red-100 text-red-700 border-2 border-red-500' 
                    : 'bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100'
                }`}
              >
                <Image size={16} />
                {imageStats.without_image} sans image
              </button>
            )}
          </div>
        </div>
        )}

        {/* Product Form */}
        {showForm && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              {editingProduct ? <Edit2 size={20} /> : <Plus size={20} />}
              {editingProduct ? 'Modifier le produit' : 'Nouveau produit'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="lg:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nom du produit *</label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">SKU / Référence</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  />
                </div>
              </div>

              {/* Category */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Catégorie *</label>
                  <select
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.category_label}
                    onChange={(e) => setFormData({ ...formData, category_label: e.target.value, subcategory_label: '' })}
                  >
                    <option value="">Sélectionner...</option>
                    {categories.map(cat => (
                      <option key={cat.id} value={cat.label}>{cat.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sous-catégorie *</label>
                  <select
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.subcategory_label}
                    onChange={(e) => setFormData({ ...formData, subcategory_label: e.target.value })}
                    disabled={!formData.category_label}
                  >
                    <option value="">Sélectionner...</option>
                    {getSubcategories().map(sub => (
                      <option key={sub.id} value={sub.label}>{sub.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Brand, Price, Stock */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Marque</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.brand}
                    onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                    list="brand-list"
                  />
                  <datalist id="brand-list">
                    <option value="Dahua" />
                    <option value="Hikvision" />
                    <option value="ZKTeco" />
                    <option value="Somfy" />
                    <option value="SOMEF" />
                    <option value="Akuvox" />
                    <option value="Leelen" />
                  </datalist>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prix (DT)</label>
                  <input
                    type="number"
                    step="0.001"
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Stock</label>
                  <input
                    type="number"
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.stock_quantity}
                    onChange={(e) => setFormData({ ...formData, stock_quantity: e.target.value })}
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  rows="4"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              {/* Connectivity & Technologies */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Connectivité</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.connectivity}
                    onChange={(e) => setFormData({ ...formData, connectivity: e.target.value })}
                  >
                    <option value="">Non spécifié</option>
                    <option value="Sans fil">Sans fil</option>
                    <option value="Filaire">Filaire</option>
                    <option value="Hybride">Hybride</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Technologies</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    placeholder="WiFi, Bluetooth, Zigbee... (séparés par virgules)"
                    value={formData.technologies.join(', ')}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      technologies: e.target.value.split(',').map(t => t.trim()).filter(t => t) 
                    })}
                  />
                </div>
              </div>

              {/* Image principale */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Image principale</label>
                <div className="flex gap-4 items-start">
                  {/* Upload button */}
                  <label className={`flex items-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-cyan-500 hover:bg-cyan-50 transition-colors ${uploadingPrimary ? 'opacity-50' : ''}`}>
                    {uploadingPrimary ? (
                      <Loader2 size={18} className="animate-spin text-cyan-500" />
                    ) : (
                      <Upload size={18} className="text-gray-500" />
                    )}
                    <span className="text-sm text-gray-600">
                      {uploadingPrimary ? 'Upload...' : 'Choisir une image'}
                    </span>
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handlePrimaryImageUpload}
                      disabled={uploadingPrimary}
                    />
                  </label>
                  
                  {/* Preview */}
                  {formData.primary_image_url && (
                    <div className="relative">
                      <img
                        src={formData.primary_image_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${formData.primary_image_url}` : formData.primary_image_url}
                        alt="Preview"
                        className="w-24 h-24 object-contain rounded-lg border bg-white"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, primary_image_url: '' })}
                        className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                        title="Supprimer"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  )}
                </div>
                {formData.primary_image_url && (
                  <p className="text-xs text-gray-400 mt-1 truncate max-w-md">{formData.primary_image_url}</p>
                )}
              </div>

              {/* Gallery Images */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Galerie d'images</label>
                <div className="space-y-3">
                  {/* Existing gallery images */}
                  {formData.images && formData.images.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {formData.images.map((img, idx) => (
                        <div key={idx} className="relative group">
                          <img
                            src={img.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${img}` : img}
                            alt={`Gallery ${idx + 1}`}
                            className="w-20 h-20 object-contain rounded-lg border bg-white"
                            onError={(e) => { e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="gray" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>'; }}
                          />
                          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center gap-1">
                            <button
                              type="button"
                              onClick={() => setFormData({ ...formData, primary_image_url: img })}
                              className="p-1 bg-cyan-500 text-white rounded text-xs"
                              title="Définir comme principale"
                            >
                              ⭐
                            </button>
                            <button
                              type="button"
                              onClick={() => setFormData({ 
                                ...formData, 
                                images: formData.images.filter((_, i) => i !== idx) 
                              })}
                              className="p-1 bg-red-500 text-white rounded text-xs"
                              title="Supprimer"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Upload button for gallery */}
                  <label className={`inline-flex items-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-cyan-500 hover:bg-cyan-50 transition-colors ${uploadingGallery ? 'opacity-50' : ''}`}>
                    {uploadingGallery ? (
                      <Loader2 size={18} className="animate-spin text-cyan-500" />
                    ) : (
                      <Upload size={18} className="text-gray-500" />
                    )}
                    <span className="text-sm text-gray-600">
                      {uploadingGallery ? 'Upload...' : 'Ajouter des images à la galerie'}
                    </span>
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      className="hidden"
                      onChange={handleGalleryImageUpload}
                      disabled={uploadingGallery}
                    />
                  </label>
                  
                  <p className="text-xs text-gray-500">Cliquez sur ⭐ pour définir une image comme principale, ✕ pour la supprimer</p>
                </div>
              </div>

              {/* Options */}
              <div className="flex gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.featured}
                    onChange={(e) => setFormData({ ...formData, featured: e.target.checked })}
                    className="w-4 h-4 text-cyan-600 rounded focus:ring-cyan-500"
                  />
                  <span className="text-sm text-gray-700">Produit mis en avant</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.active}
                    onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                    className="w-4 h-4 text-cyan-600 rounded focus:ring-cyan-500"
                  />
                  <span className="text-sm text-gray-700">Produit actif (visible)</span>
                </label>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => { setShowForm(false); setEditingProduct(null); resetForm(); }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors disabled:opacity-50"
                >
                  <Save size={18} />
                  {saving ? 'Enregistrement...' : (editingProduct ? 'Mettre à jour' : 'Créer')}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Products Grid - Hidden when form is open */}
        {!showForm && (
          loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
            </div>
          ) : products.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <Image size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Aucun produit trouvé</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {products.map((product) => (
                  <div 
                    key={product.id} 
                    className={`bg-white rounded-xl shadow-sm overflow-hidden group transition-all hover:shadow-md ${
                      !product.active ? 'opacity-60' : ''
                    }`}
                  >
                    {/* Image */}
                    <div className="relative aspect-square bg-gray-50">
                      {product.primary_image_url || product.image_url ? (
                        <img
                          src={(product.primary_image_url || product.image_url).startsWith('/') 
                            ? `${process.env.REACT_APP_BACKEND_URL}${product.primary_image_url || product.image_url}` 
                            : (product.primary_image_url || product.image_url)}
                          alt={product.name}
                          className="w-full h-full object-contain p-2"
                          onError={(e) => { 
                            e.target.parentElement.innerHTML = '<div class="w-full h-full flex items-center justify-center text-gray-300"><svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg></div>';
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-300">
                          <Image size={48} />
                        </div>
                      )}
                      
                      {/* Badges */}
                      <div className="absolute top-2 left-2 flex flex-col gap-1">
                        {product.featured && (
                          <span className="px-2 py-0.5 text-xs bg-yellow-400 text-yellow-900 rounded-full">
                            ⭐ Vedette
                          </span>
                        )}
                        {!product.active && (
                          <span className="px-2 py-0.5 text-xs bg-gray-400 text-white rounded-full">
                            Inactif
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Info */}
                    <div className="p-3">
                      <h3 className="font-medium text-gray-900 text-sm line-clamp-2 mb-1" title={product.name}>
                        {product.name}
                      </h3>
                      <p className="text-xs text-gray-500 mb-2">
                        {product.sku && <span className="font-mono">{product.sku} • </span>}
                        {product.brand}
                      </p>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-400 truncate max-w-[60%]">
                          {product.category_label}
                      </span>
                      {product.price ? (
                        <span className="font-semibold text-cyan-600">{product.price} DT</span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 mt-3 pt-3 border-t">
                      <button
                        onClick={() => handleEdit(product)}
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs text-cyan-600 border border-cyan-200 rounded-lg hover:bg-cyan-50 transition-colors"
                      >
                        <Edit2 size={14} />
                        Modifier
                      </button>
                      <button
                        onClick={() => handleToggleActive(product)}
                        className={`px-2 py-1.5 rounded-lg transition-colors ${
                          product.active 
                            ? 'text-gray-600 border border-gray-200 hover:bg-gray-50' 
                            : 'text-green-600 border border-green-200 hover:bg-green-50'
                        }`}
                        title={product.active ? 'Désactiver' : 'Activer'}
                      >
                        {product.active ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                      <button
                        onClick={() => handleDelete(product.id)}
                        className="px-2 py-1.5 text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
                        title="Supprimer"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <button
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                  disabled={pagination.page === 1}
                  className="p-2 rounded-lg border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft size={18} />
                </button>
                
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                    let pageNum;
                    if (pagination.pages <= 5) {
                      pageNum = i + 1;
                    } else if (pagination.page <= 3) {
                      pageNum = i + 1;
                    } else if (pagination.page >= pagination.pages - 2) {
                      pageNum = pagination.pages - 4 + i;
                    } else {
                      pageNum = pagination.page - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPagination(prev => ({ ...prev, page: pageNum }))}
                        className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${
                          pagination.page === pageNum
                            ? 'bg-cyan-500 text-white'
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  disabled={pagination.page === pagination.pages}
                  className="p-2 rounded-lg border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight size={18} />
                </button>
                
                <span className="ml-4 text-sm text-gray-500">
                  Page {pagination.page} / {pagination.pages}
                </span>
              </div>
            )}
          </>
          )
        )}
      </div>
    </DashboardLayout>
  );
};

export default AdminProducts;
