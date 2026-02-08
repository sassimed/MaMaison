import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { 
  Search, Plus, Edit2, Trash2, X, Save, ChevronDown, ChevronRight, Upload, Loader2,
  // Icon library for selector
  Home, ShoppingCart, Package, Camera, Video, Shield, Bell, Lock, Key, Wifi,
  Smartphone, Tablet, Monitor, Tv, Speaker, Headphones, Radio, Mic, Phone,
  Sun, Moon, Lightbulb, Zap, Battery, Plug, Power, Settings, Wrench,
  Thermometer, Droplet, Wind, Cloud, Umbrella, Snowflake, Flame,
  Car, Bike, Bus, Train, Plane, Ship, Truck, MapPin, Navigation, Compass,
  Building, Building2, Factory, Warehouse, Store, GraduationCap, Briefcase,
  Heart, Star, Award, Gift, Tag, Bookmark, Flag, Target, Clock, Calendar,
  Mail, MessageSquare, Send, Inbox, Archive, Folder, File, FileText, Image,
  Music, Film, Play, Pause, Volume2, VolumeX, Eye, EyeOff, Search as SearchIcon,
  User, Users, UserPlus, UserCheck, Baby, Accessibility,
  Globe, Link, Signal, Bluetooth, Cast, Airplay, Rss,
  Database, Server, HardDrive, Cpu, CircuitBoard, Router,
  CreditCard, Wallet, DollarSign, Euro, Percent, Receipt, Calculator,
  AlertTriangle, AlertCircle, Info, HelpCircle, CheckCircle, XCircle,
  Layers, Layout, Grid, List, Menu, MoreHorizontal, MoreVertical,
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, RefreshCw, RotateCw,
  Maximize, Minimize, Move, Crop, Copy, Clipboard, Scissors, Trash,
  Download, ExternalLink, Share, Share2, QrCode, Scan, Fingerprint,
  Unlock, ShieldCheck, ShieldAlert, ShieldOff,
  DoorOpen, DoorClosed
} from 'lucide-react';

// Define available icons with their names
const AVAILABLE_ICONS = [
  { name: 'camera', icon: Camera, label: 'Caméra' },
  { name: 'video', icon: Video, label: 'Vidéo' },
  { name: 'shield', icon: Shield, label: 'Sécurité' },
  { name: 'shield-check', icon: ShieldCheck, label: 'Protection' },
  { name: 'bell', icon: Bell, label: 'Alarme' },
  { name: 'lock', icon: Lock, label: 'Serrure' },
  { name: 'key', icon: Key, label: 'Clé' },
  { name: 'unlock', icon: Unlock, label: 'Déverrouillé' },
  { name: 'door-open', icon: DoorOpen, label: 'Porte ouverte' },
  { name: 'door-closed', icon: DoorClosed, label: 'Porte fermée' },
  { name: 'home', icon: Home, label: 'Maison' },
  { name: 'building', icon: Building, label: 'Bâtiment' },
  { name: 'building2', icon: Building2, label: 'Immeuble' },
  { name: 'warehouse', icon: Warehouse, label: 'Entrepôt' },
  { name: 'store', icon: Store, label: 'Magasin' },
  { name: 'wifi', icon: Wifi, label: 'WiFi' },
  { name: 'bluetooth', icon: Bluetooth, label: 'Bluetooth' },
  { name: 'router', icon: Router, label: 'Routeur' },
  { name: 'signal', icon: Signal, label: 'Signal' },
  { name: 'smartphone', icon: Smartphone, label: 'Smartphone' },
  { name: 'tablet', icon: Tablet, label: 'Tablette' },
  { name: 'monitor', icon: Monitor, label: 'Moniteur' },
  { name: 'tv', icon: Tv, label: 'TV' },
  { name: 'speaker', icon: Speaker, label: 'Haut-parleur' },
  { name: 'phone', icon: Phone, label: 'Téléphone' },
  { name: 'mic', icon: Mic, label: 'Microphone' },
  { name: 'lightbulb', icon: Lightbulb, label: 'Ampoule' },
  { name: 'sun', icon: Sun, label: 'Soleil' },
  { name: 'moon', icon: Moon, label: 'Lune' },
  { name: 'zap', icon: Zap, label: 'Électricité' },
  { name: 'power', icon: Power, label: 'Alimentation' },
  { name: 'plug', icon: Plug, label: 'Prise' },
  { name: 'battery', icon: Battery, label: 'Batterie' },
  { name: 'thermometer', icon: Thermometer, label: 'Thermomètre' },
  { name: 'droplet', icon: Droplet, label: 'Eau' },
  { name: 'wind', icon: Wind, label: 'Vent' },
  { name: 'flame', icon: Flame, label: 'Feu' },
  { name: 'snowflake', icon: Snowflake, label: 'Climatisation' },
  { name: 'settings', icon: Settings, label: 'Paramètres' },
  { name: 'wrench', icon: Wrench, label: 'Outil' },
  { name: 'package', icon: Package, label: 'Colis' },
  { name: 'shopping-cart', icon: ShoppingCart, label: 'Panier' },
  { name: 'tag', icon: Tag, label: 'Étiquette' },
  { name: 'car', icon: Car, label: 'Voiture' },
  { name: 'map-pin', icon: MapPin, label: 'Position' },
  { name: 'navigation', icon: Navigation, label: 'Navigation' },
  { name: 'eye', icon: Eye, label: 'Vue' },
  { name: 'scan', icon: Scan, label: 'Scanner' },
  { name: 'fingerprint', icon: Fingerprint, label: 'Empreinte' },
  { name: 'qr-code', icon: QrCode, label: 'QR Code' },
  { name: 'cpu', icon: Cpu, label: 'Processeur' },
  { name: 'server', icon: Server, label: 'Serveur' },
  { name: 'hard-drive', icon: HardDrive, label: 'Stockage' },
  { name: 'database', icon: Database, label: 'Base de données' },
  { name: 'layers', icon: Layers, label: 'Couches' },
  { name: 'grid', icon: Grid, label: 'Grille' },
  { name: 'user', icon: User, label: 'Utilisateur' },
  { name: 'users', icon: Users, label: 'Utilisateurs' },
  { name: 'star', icon: Star, label: 'Étoile' },
  { name: 'heart', icon: Heart, label: 'Cœur' },
  { name: 'clock', icon: Clock, label: 'Horloge' },
  { name: 'calendar', icon: Calendar, label: 'Calendrier' },
];

const DEFAULT_ICON = 'shield';

// Icon component renderer
const IconRenderer = ({ iconName, size = 24, className = '' }) => {
  const iconDef = AVAILABLE_ICONS.find(i => i.name === iconName);
  if (iconDef) {
    const IconComponent = iconDef.icon;
    return <IconComponent size={size} className={className} />;
  }
  // Fallback to default
  return <Shield size={size} className={className} />;
};

const AdminCategories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [expandedCategories, setExpandedCategories] = useState({});
  const [showIconPicker, setShowIconPicker] = useState(false);
  const [editingSubcatIndex, setEditingSubcatIndex] = useState(null);
  const [showSubcatIconPicker, setShowSubcatIconPicker] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [iconSearch, setIconSearch] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    icon: DEFAULT_ICON,
    image_url: '',
    subcategories: []
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await api.get('/admin/categories');
      setCategories(response.data);
    } catch (err) {
      console.error('Error loading categories:', err);
    }
    setLoading(false);
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const uploadData = new FormData();
    uploadData.append('file', file);

    try {
      const response = await api.post('/upload/image', uploadData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setFormData({ ...formData, image_url: response.data.url });
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'upload');
    }
    setUploading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const dataToSend = {
        name: formData.name,
        label: formData.name,
        description: formData.description,
        icon: formData.icon || DEFAULT_ICON,
        image_url: formData.image_url,
        subcategories: formData.subcategories.map(sub => ({
          name: sub.name,
          label: sub.name,
          icon: sub.icon || DEFAULT_ICON
        }))
      };

      if (editingCategory) {
        await api.put('/admin/categories/' + editingCategory.id, dataToSend);
      } else {
        await api.post('/admin/categories', dataToSend);
      }
      setShowForm(false);
      setEditingCategory(null);
      resetForm();
      loadCategories();
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Erreur';
      alert(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
    }
    setSaving(false);
  };

  const handleEdit = (category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name || category.label,
      description: category.description || '',
      icon: category.icon || DEFAULT_ICON,
      image_url: category.image_url || '',
      subcategories: (category.subcategories || []).map(sub => ({
        id: sub.id,
        name: sub.name || sub.label,
        icon: sub.icon || DEFAULT_ICON,
        product_count: sub.product_count || 0
      }))
    });
    setShowForm(true);
  };

  const handleDelete = async (categoryId) => {
    if (!window.confirm('Supprimer cette catégorie et toutes ses sous-catégories ?')) return;
    try {
      await api.delete('/admin/categories/' + categoryId);
      loadCategories();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      icon: DEFAULT_ICON,
      image_url: '',
      subcategories: []
    });
    setEditingSubcatIndex(null);
  };

  const toggleExpand = (categoryId) => {
    setExpandedCategories(prev => ({
      ...prev,
      [categoryId]: !prev[categoryId]
    }));
  };

  // Subcategory management
  const addSubcategory = () => {
    setFormData({
      ...formData,
      subcategories: [...formData.subcategories, { name: '', icon: DEFAULT_ICON, product_count: 0 }]
    });
    setEditingSubcatIndex(formData.subcategories.length);
  };

  const updateSubcategory = (index, field, value) => {
    const updated = [...formData.subcategories];
    updated[index] = { ...updated[index], [field]: value };
    setFormData({ ...formData, subcategories: updated });
  };

  const removeSubcategory = (index) => {
    const subcat = formData.subcategories[index];
    if (subcat.product_count > 0) {
      alert(`Impossible de supprimer: ${subcat.product_count} produits dans cette sous-catégorie`);
      return;
    }
    const updated = formData.subcategories.filter((_, i) => i !== index);
    setFormData({ ...formData, subcategories: updated });
  };

  // Filter icons based on search
  const filteredIcons = AVAILABLE_ICONS.filter(icon => 
    icon.label.toLowerCase().includes(iconSearch.toLowerCase()) ||
    icon.name.toLowerCase().includes(iconSearch.toLowerCase())
  );

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-12 h-12 animate-spin text-cyan-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Gestion des Catégories</h1>
            <p className="text-sm text-gray-500 mt-1">{categories.length} catégories principales</p>
          </div>
          <button
            onClick={() => { setShowForm(!showForm); setEditingCategory(null); resetForm(); }}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            {showForm ? <X size={18} /> : <Plus size={18} />}
            {showForm ? 'Annuler' : 'Nouvelle catégorie'}
          </button>
        </div>

        {/* Form */}
        {showForm && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              {editingCategory ? <Edit2 size={20} /> : <Plus size={20} />}
              {editingCategory ? 'Modifier la catégorie' : 'Nouvelle catégorie'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    placeholder="Nom de la catégorie"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                
                {/* Icon selector */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Icône</label>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setShowIconPicker(!showIconPicker)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg flex items-center gap-3 hover:bg-gray-50 transition-colors"
                    >
                      <div className="w-8 h-8 bg-cyan-100 rounded-lg flex items-center justify-center">
                        <IconRenderer iconName={formData.icon} size={20} className="text-cyan-600" />
                      </div>
                      <span className="text-gray-700 flex-1 text-left">
                        {AVAILABLE_ICONS.find(i => i.name === formData.icon)?.label || 'Sélectionner'}
                      </span>
                      <ChevronDown size={18} className="text-gray-400" />
                    </button>
                    
                    {/* Icon picker dropdown */}
                    {showIconPicker && (
                      <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-hidden">
                        <div className="p-2 border-b sticky top-0 bg-white">
                          <div className="relative">
                            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                              type="text"
                              placeholder="Rechercher une icône..."
                              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg"
                              value={iconSearch}
                              onChange={(e) => setIconSearch(e.target.value)}
                            />
                          </div>
                        </div>
                        <div className="p-2 max-h-60 overflow-y-auto grid grid-cols-4 gap-1">
                          {filteredIcons.map((iconDef) => (
                            <button
                              key={iconDef.name}
                              type="button"
                              onClick={() => {
                                setFormData({ ...formData, icon: iconDef.name });
                                setShowIconPicker(false);
                                setIconSearch('');
                              }}
                              className={`p-2 rounded-lg flex flex-col items-center gap-1 hover:bg-cyan-50 transition-colors ${
                                formData.icon === iconDef.name ? 'bg-cyan-100 ring-2 ring-cyan-500' : ''
                              }`}
                              title={iconDef.label}
                            >
                              <iconDef.icon size={20} className="text-gray-700" />
                              <span className="text-xs text-gray-500 truncate w-full text-center">{iconDef.label}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  rows="2"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                  placeholder="Description de la catégorie (optionnel)"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              {/* Image */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Image de couverture</label>
                <div className="flex items-center gap-4">
                  <label className={`flex items-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-cyan-500 hover:bg-cyan-50 transition-colors ${uploading ? 'opacity-50' : ''}`}>
                    {uploading ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
                    <span className="text-sm text-gray-600">{uploading ? 'Upload...' : 'Choisir une image'}</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                      disabled={uploading}
                    />
                  </label>
                  {formData.image_url && (
                    <div className="relative">
                      <img
                        src={formData.image_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${formData.image_url}` : formData.image_url}
                        alt="Preview"
                        className="w-20 h-20 object-cover rounded-lg"
                      />
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, image_url: '' })}
                        className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Subcategories */}
              <div className="border-t pt-4">
                <div className="flex justify-between items-center mb-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Sous-catégories ({formData.subcategories.length})
                  </label>
                  <button
                    type="button"
                    onClick={addSubcategory}
                    className="flex items-center gap-1 px-3 py-1 text-sm text-cyan-600 hover:bg-cyan-50 rounded-lg transition-colors"
                  >
                    <Plus size={16} />
                    Ajouter
                  </button>
                </div>
                
                {formData.subcategories.length === 0 ? (
                  <p className="text-sm text-gray-400 italic">Aucune sous-catégorie</p>
                ) : (
                  <div className="space-y-2">
                    {formData.subcategories.map((subcat, index) => (
                      <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                        {/* Subcategory icon selector */}
                        <div className="relative">
                          <button
                            type="button"
                            onClick={() => setShowSubcatIconPicker(showSubcatIconPicker === index ? null : index)}
                            className="w-10 h-10 bg-white border border-gray-200 rounded-lg flex items-center justify-center hover:border-cyan-500 transition-colors"
                            title="Changer l'icône"
                          >
                            <IconRenderer iconName={subcat.icon} size={18} className="text-gray-600" />
                          </button>
                          
                          {/* Subcategory icon picker */}
                          {showSubcatIconPicker === index && (
                            <div className="absolute z-50 mt-1 left-0 bg-white border border-gray-200 rounded-lg shadow-lg p-2 w-64 max-h-48 overflow-y-auto grid grid-cols-5 gap-1">
                              {AVAILABLE_ICONS.slice(0, 30).map((iconDef) => (
                                <button
                                  key={iconDef.name}
                                  type="button"
                                  onClick={() => {
                                    updateSubcategory(index, 'icon', iconDef.name);
                                    setShowSubcatIconPicker(null);
                                  }}
                                  className={`p-2 rounded hover:bg-cyan-50 ${subcat.icon === iconDef.name ? 'bg-cyan-100' : ''}`}
                                  title={iconDef.label}
                                >
                                  <iconDef.icon size={18} />
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                        
                        {/* Subcategory name */}
                        <input
                          type="text"
                          className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
                          placeholder="Nom de la sous-catégorie"
                          value={subcat.name}
                          onChange={(e) => updateSubcategory(index, 'name', e.target.value)}
                        />
                        
                        {/* Product count badge */}
                        {subcat.product_count > 0 && (
                          <span className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded-full">
                            {subcat.product_count} produits
                          </span>
                        )}
                        
                        {/* Delete button */}
                        <button
                          type="button"
                          onClick={() => removeSubcategory(index)}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                          title={subcat.product_count > 0 ? "Impossible: contient des produits" : "Supprimer"}
                          disabled={subcat.product_count > 0}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => { setShowForm(false); setEditingCategory(null); resetForm(); }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors disabled:opacity-50"
                >
                  {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                  {editingCategory ? 'Mettre à jour' : 'Créer'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Categories list */}
        <div className="space-y-4">
          {categories.map((category) => (
            <div key={category.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
              {/* Category header */}
              <div 
                className="flex items-center gap-4 p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => toggleExpand(category.id)}
              >
                {/* Expand/collapse icon */}
                <button className="p-1 text-gray-400">
                  {expandedCategories[category.id] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                </button>
                
                {/* Category icon */}
                <div className="w-12 h-12 bg-gradient-to-br from-purple-100 to-cyan-100 rounded-xl flex items-center justify-center">
                  <IconRenderer iconName={category.icon} size={24} className="text-cyan-600" />
                </div>
                
                {/* Category info */}
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{category.name || category.label}</h3>
                  <p className="text-sm text-gray-500">
                    {category.subcategories?.length || 0} sous-catégories • {category.product_count || 0} produits
                  </p>
                </div>
                
                {/* Actions */}
                <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => handleEdit(category)}
                    className="p-2 text-cyan-600 hover:bg-cyan-50 rounded-lg transition-colors"
                    title="Modifier"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button
                    onClick={() => handleDelete(category.id)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                    title={category.product_count > 0 ? "Contient des produits" : "Supprimer"}
                    disabled={category.product_count > 0}
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
              
              {/* Subcategories */}
              {expandedCategories[category.id] && category.subcategories && category.subcategories.length > 0 && (
                <div className="border-t bg-gray-50 p-4">
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {category.subcategories.map((subcat) => (
                      <div
                        key={subcat.id}
                        className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200"
                      >
                        <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                          <IconRenderer iconName={subcat.icon} size={16} className="text-gray-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{subcat.name || subcat.label}</p>
                          <p className="text-xs text-gray-500">{subcat.product_count || 0} produits</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Empty state */}
        {categories.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm p-8 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Package size={32} className="text-gray-400" />
            </div>
            <p className="text-gray-500 mb-4">Aucune catégorie créée</p>
            <button
              onClick={() => setShowForm(true)}
              className="text-cyan-600 hover:text-cyan-500 font-medium"
            >
              Créer votre première catégorie
            </button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AdminCategories;
