import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { Megaphone, Plus, Eye, Clock, CheckCircle, XCircle, Award, ChevronRight, MapPin, Star, Users, X, Phone, Mail, Building2, Loader2 } from 'lucide-react';

function MyAnnoncesPage() {
  var navigate = useNavigate();
  var [searchParams] = useSearchParams();
  var [annonces, setAnnonces] = useState([]);
  var [loading, setLoading] = useState(true);
  var [showForm, setShowForm] = useState(false);
  var [submitting, setSubmitting] = useState(false);
  var [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'Autre',
    city: '',
    address: ''
  });
  
  // Matched professionals state
  var [showMatchedPros, setShowMatchedPros] = useState(false);
  var [matchedPros, setMatchedPros] = useState([]);
  var [newAnnonceId, setNewAnnonceId] = useState(null);
  var [selectedPros, setSelectedPros] = useState([]);
  var [notifying, setNotifying] = useState(false);

  var categories = [
    'Installation Caméra',
    'Système d\'Alarme',
    'Domotique',
    'Éclairage Connecté',
    'Serrure Connectée',
    'Réseau WiFi/Câblage',
    'Autre'
  ];

  var tunisianCities = [
    'Tunis', 'Sfax', 'Sousse', 'Kairouan', 'Bizerte', 'Gabès', 'Ariana',
    'Gafsa', 'Monastir', 'Ben Arous', 'Kasserine', 'Médenine', 'Nabeul',
    'Tataouine', 'Béja', 'Jendouba', 'Mahdia', 'Sidi Bouzid', 'Tozeur',
    'Siliana', 'Kébili', 'Zaghouan', 'Manouba', 'La Manouba'
  ];

  useEffect(function() {
    loadAnnonces();
    // Auto-open form if action=create is in URL
    if (searchParams.get('action') === 'create') {
      setShowForm(true);
    }
  }, [searchParams]);

  async function loadAnnonces() {
    try {
      var response = await api.get('/annonces/my-annonces');
      setAnnonces(response.data);
    } catch (error) {
      console.error('Error loading annonces:', error);
    }
    setLoading(false);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      var response = await api.post('/annonces', formData);
      setShowForm(false);
      setFormData({ title: '', description: '', category: 'Autre', city: '', address: '' });
      
      // Show matched professionals
      if (response.data.matched_professionals && response.data.matched_professionals.length > 0) {
        setMatchedPros(response.data.matched_professionals);
        setNewAnnonceId(response.data.annonce_id);
        setShowMatchedPros(true);
      } else {
        alert('Annonce créée ! Elle sera visible après validation par l\'admin.');
      }
      
      loadAnnonces();
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la création');
    }
    setSubmitting(false);
  }

  function toggleProSelection(proId) {
    if (selectedPros.includes(proId)) {
      setSelectedPros(selectedPros.filter(function(id) { return id !== proId; }));
    } else if (selectedPros.length < 5) {
      setSelectedPros([...selectedPros, proId]);
    }
  }

  async function handleNotifyPros() {
    if (selectedPros.length === 0) {
      alert('Sélectionnez au moins un professionnel');
      return;
    }
    
    setNotifying(true);
    try {
      await api.post('/annonces/notify-professionals/' + newAnnonceId, {
        professional_ids: selectedPros
      });
      alert('Professionnels notifiés avec succès ! Ils recevront votre demande par email.');
      setShowMatchedPros(false);
      setSelectedPros([]);
      setMatchedPros([]);
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la notification');
    }
    setNotifying(false);
  }

  function closeMatchedPros() {
    setShowMatchedPros(false);
    setSelectedPros([]);
    setMatchedPros([]);
    alert('Annonce créée ! Elle sera visible après validation par l\'admin.');
  }

  function getStatusIcon(status) {
    if (status === 'EN_ATTENTE') return Clock;
    if (status === 'PUBLIEE') return CheckCircle;
    if (status === 'REFUSEE') return XCircle;
    if (status === 'ATTRIBUEE') return Award;
    if (status === 'CLOTUREE') return XCircle;
    return Clock;
  }

  function getStatusStyle(status) {
    if (status === 'EN_ATTENTE') return 'bg-yellow-100 text-yellow-800';
    if (status === 'PUBLIEE') return 'bg-green-100 text-green-800';
    if (status === 'REFUSEE') return 'bg-red-100 text-red-800';
    if (status === 'ATTRIBUEE') return 'bg-purple-100 text-purple-800';
    if (status === 'CLOTUREE') return 'bg-gray-100 text-gray-800';
    return 'bg-gray-100 text-gray-800';
  }

  function getStatusLabel(status) {
    if (status === 'EN_ATTENTE') return 'En attente de validation';
    if (status === 'PUBLIEE') return 'Publiée';
    if (status === 'REFUSEE') return 'Refusée';
    if (status === 'ATTRIBUEE') return 'Attribuée';
    if (status === 'CLOTUREE') return 'Clôturée';
    return status;
  }

  function formatDate(d) {
    return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  function renderAnnonceCard(annonce) {
    var StatusIcon = getStatusIcon(annonce.status);
    var responsesCount = (annonce.responses || []).length;
    
    return (
      <div key={annonce.id} className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 bg-cyan-100 text-cyan-700 text-xs rounded">{annonce.category}</span>
              <span className="flex items-center text-xs text-gray-500">
                <MapPin className="w-3 h-3 mr-1" />
                {annonce.city}
              </span>
            </div>
            <h3 className="font-semibold text-gray-900">{annonce.title}</h3>
            <p className="text-sm text-gray-500 mt-1">{formatDate(annonce.created_at)}</p>
          </div>
          <span className={'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ' + getStatusStyle(annonce.status)}>
            <StatusIcon className="w-3 h-3" />
            {getStatusLabel(annonce.status)}
          </span>
        </div>
        
        <p className="text-sm text-gray-600 line-clamp-2 mb-3">{annonce.description}</p>
        
        {annonce.status === 'REFUSEE' && annonce.admin_notes && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
            <p className="text-sm text-red-800"><strong>Raison du refus:</strong> {annonce.admin_notes}</p>
          </div>
        )}
        
        <div className="flex items-center justify-between pt-3 border-t">
          {annonce.status === 'PUBLIEE' || annonce.status === 'ATTRIBUEE' ? (
            <span className="text-sm text-purple-600 font-medium">
              {responsesCount} réponse(s) de professionnels
            </span>
          ) : (
            <span className="text-sm text-gray-400">—</span>
          )}
          <button
            onClick={function() { navigate('/dashboard/my-annonces/' + annonce.id); }}
            className="flex items-center gap-1 text-cyan-600 hover:text-cyan-700 text-sm font-medium"
          >
            Voir détails
            <ChevronRight className="w-4 h-4" />
          </button>
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

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Megaphone className="w-7 h-7 text-cyan-500" />
            Mes Annonces
          </h1>
          <button
            onClick={function() { setShowForm(true); }}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600"
            data-testid="create-annonce-btn"
          >
            <Plus className="w-5 h-5" />
            Nouvelle annonce
          </button>
        </div>

        {/* Info banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p className="text-blue-800 text-sm">
            <strong>Comment ça marche ?</strong> Publiez votre besoin, l'admin valide votre annonce, 
            puis les professionnels peuvent vous envoyer leurs offres. Vous choisissez celui qui vous convient !
          </p>
        </div>

        {annonces.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Megaphone className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Aucune annonce</h2>
            <p className="text-gray-500 mb-4">Créez votre première annonce pour trouver un professionnel</p>
            <button
              onClick={function() { setShowForm(true); }}
              className="px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600"
            >
              Créer une annonce
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {annonces.map(renderAnnonceCard)}
          </div>
        )}

        {/* Create Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b">
                <h2 className="text-xl font-bold">Nouvelle annonce</h2>
                <p className="text-sm text-gray-500">Décrivez votre besoin en détail</p>
              </div>
              
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Titre *</label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: Recherche technicien pour installation caméra"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.title}
                    onChange={function(e) { setFormData({...formData, title: e.target.value}); }}
                    data-testid="annonce-title-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Catégorie *</label>
                  <select
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.category}
                    onChange={function(e) { setFormData({...formData, category: e.target.value}); }}
                  >
                    {categories.map(function(cat) {
                      return <option key={cat} value={cat}>{cat}</option>;
                    })}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ville *</label>
                  <select
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.city}
                    onChange={function(e) { setFormData({...formData, city: e.target.value}); }}
                    data-testid="annonce-city-select"
                  >
                    <option value="">Sélectionner une ville</option>
                    {tunisianCities.map(function(city) {
                      return <option key={city} value={city}>{city}</option>;
                    })}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Adresse (optionnel)</label>
                  <input
                    type="text"
                    placeholder="Adresse précise pour l'intervention"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    value={formData.address}
                    onChange={function(e) { setFormData({...formData, address: e.target.value}); }}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                  <textarea
                    required
                    rows="4"
                    placeholder="Décrivez votre besoin en détail : type d'installation, nombre de caméras/appareils, configuration souhaitée..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500"
                    value={formData.description}
                    onChange={function(e) { setFormData({...formData, description: e.target.value}); }}
                    data-testid="annonce-description-input"
                  />
                </div>

                <div className="flex gap-3 pt-4 border-t">
                  <button
                    type="button"
                    onClick={function() { setShowForm(false); }}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="flex-1 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50"
                    data-testid="submit-annonce-btn"
                  >
                    {submitting ? 'Envoi...' : 'Publier l\'annonce'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Matched Professionals Modal */}
        {showMatchedPros && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b bg-gradient-to-r from-purple-600 to-cyan-500 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold flex items-center gap-2">
                      <Users className="w-6 h-6" />
                      Professionnels recommandés
                    </h2>
                    <p className="text-sm text-white/80 mt-1">
                      Basé sur votre besoin et votre localisation
                    </p>
                  </div>
                  <button
                    onClick={closeMatchedPros}
                    className="p-2 hover:bg-white/20 rounded-lg"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {matchedPros.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Users className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>Aucun professionnel trouvé pour le moment</p>
                  </div>
                ) : (
                  matchedPros.map(function(pro, index) {
                    var isSelected = selectedPros.includes(pro.id);
                    return (
                      <div
                        key={pro.id}
                        onClick={function() { toggleProSelection(pro.id); }}
                        className={'rounded-xl p-4 cursor-pointer transition-all border-2 ' + 
                          (isSelected 
                            ? 'border-purple-500 bg-purple-50' 
                            : 'border-gray-200 hover:border-gray-300 bg-white')}
                      >
                        <div className="flex items-start gap-4">
                          {/* Rank Badge */}
                          <div className={'w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0 ' +
                            (index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-gray-400' : index === 2 ? 'bg-orange-400' : 'bg-gray-300')}>
                            #{index + 1}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between">
                              <div>
                                <h3 className="font-semibold text-gray-900">
                                  {pro.company_name || pro.full_name}
                                </h3>
                                {pro.company_name && (
                                  <p className="text-sm text-gray-500">{pro.full_name}</p>
                                )}
                              </div>
                              
                              {/* Match Score */}
                              <div className="text-right flex-shrink-0">
                                <div className="text-lg font-bold text-purple-600">
                                  {pro.match_score}%
                                </div>
                                <div className="text-xs text-gray-500">compatibilité</div>
                              </div>
                            </div>
                            
                            {/* Location & Rating */}
                            <div className="flex items-center gap-4 mt-2 text-sm">
                              <span className={'flex items-center gap-1 ' + (pro.is_same_city ? 'text-green-600 font-medium' : 'text-gray-500')}>
                                <MapPin className="w-4 h-4" />
                                {pro.city || 'Non spécifié'}
                                {pro.is_same_city && ' ✓'}
                              </span>
                              
                              {pro.average_rating && (
                                <span className="flex items-center gap-1 text-yellow-600">
                                  <Star className="w-4 h-4 fill-current" />
                                  {pro.average_rating}/5
                                  <span className="text-gray-400">({pro.review_count} avis)</span>
                                </span>
                              )}
                              
                              {pro.completed_missions > 0 && (
                                <span className="text-gray-500">
                                  {pro.completed_missions} missions
                                </span>
                              )}
                            </div>
                            
                            {/* Match Reasons */}
                            {pro.match_reasons && pro.match_reasons.length > 0 && (
                              <div className="flex flex-wrap gap-2 mt-2">
                                {pro.match_reasons.map(function(reason, i) {
                                  return (
                                    <span key={i} className="px-2 py-1 bg-cyan-100 text-cyan-700 text-xs rounded-full">
                                      {reason}
                                    </span>
                                  );
                                })}
                              </div>
                            )}
                            
                            {/* Services */}
                            {pro.services && pro.services.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {pro.services.map(function(service, i) {
                                  return (
                                    <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                                      {service}
                                    </span>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                          
                          {/* Selection Checkbox */}
                          <div className={'w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 ' +
                            (isSelected ? 'border-purple-500 bg-purple-500' : 'border-gray-300')}>
                            {isSelected && <CheckCircle className="w-4 h-4 text-white" />}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
              
              <div className="p-4 border-t bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-600">
                    {selectedPros.length}/5 professionnels sélectionnés
                  </span>
                  {selectedPros.length > 0 && (
                    <button
                      onClick={function() { setSelectedPros([]); }}
                      className="text-sm text-red-600 hover:underline"
                    >
                      Tout désélectionner
                    </button>
                  )}
                </div>
                
                <div className="flex gap-3">
                  <button
                    onClick={closeMatchedPros}
                    className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-100"
                  >
                    Passer cette étape
                  </button>
                  <button
                    onClick={handleNotifyPros}
                    disabled={selectedPros.length === 0 || notifying}
                    className="flex-1 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {notifying ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Envoi...
                      </>
                    ) : (
                      <>
                        <Mail className="w-4 h-4" />
                        Notifier les pros sélectionnés
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default MyAnnoncesPage;
