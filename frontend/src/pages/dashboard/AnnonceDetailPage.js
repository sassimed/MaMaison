import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { ArrowLeft, MapPin, Calendar, User, Mail, Phone, Star, CheckCircle, Clock, XCircle, MessageSquare, ExternalLink, Users, X, Building2, Loader2 } from 'lucide-react';
import { ReviewForm } from '../../components/reviews/StarRating';

// Separate component for response card to avoid Babel issues
const ResponseCard = ({ response, annonce, reviewedProfessionals, selecting, onSelect, onOpenReview, onContact }) => {
  const isSelected = annonce.selected_response_id === response.id;
  const hasReviewed = reviewedProfessionals.indexOf(response.professional_id) !== -1;
  const canReview = isSelected && (annonce.status === 'ATTRIBUEE' || annonce.status === 'CLOTUREE');
  
  const formatDate = (d) => {
    return new Date(d).toLocaleDateString('fr-FR', { 
      day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' 
    });
  };
  
  return (
    <div 
      className={'bg-white rounded-xl shadow-sm p-5 border-2 ' + (isSelected ? 'border-purple-500' : 'border-transparent')}
      data-testid={'response-card-' + response.id}
    >
      {isSelected && (
        <div className="flex items-center gap-2 text-purple-600 mb-3">
          <Star className="w-5 h-5 fill-current" />
          <span className="font-semibold">Professionnel sélectionné</span>
        </div>
      )}
      
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-bold">
            {response.professional_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <Link 
              to={'/dashboard/professional/' + response.professional_id}
              className="font-semibold hover:text-cyan-600 flex items-center gap-1"
            >
              {response.professional_name}
              <ExternalLink className="w-4 h-4" />
            </Link>
            <p className="text-sm text-gray-500">{formatDate(response.created_at)}</p>
          </div>
        </div>
        {response.price_estimate && (
          <span className="text-xl font-bold text-cyan-600">{response.price_estimate.toFixed(3)} DT</span>
        )}
      </div>

      <p className="text-gray-700 mb-3">{response.message}</p>

      {response.availability && (
        <p className="text-sm text-gray-600 mb-3">
          <Calendar className="w-4 h-4 inline mr-1" />
          <strong>Disponibilité:</strong> {response.availability}
        </p>
      )}

      {(isSelected || annonce.status === 'ATTRIBUEE') && (
        <div className="bg-gray-50 rounded-lg p-3 mt-3 space-y-2">
          <p className="text-sm flex items-center gap-2">
            <Mail className="w-4 h-4 text-gray-400" />
            {response.professional_email}
          </p>
          {response.professional_phone && (
            <p className="text-sm flex items-center gap-2">
              <Phone className="w-4 h-4 text-gray-400" />
              {response.professional_phone}
            </p>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="mt-4 flex flex-wrap gap-2">
        {/* Contact button - always visible */}
        <button
          onClick={() => onContact(response.professional_id, response.professional_name)}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg font-medium hover:bg-cyan-600"
          data-testid="contact-professional-btn"
        >
          <MessageSquare className="w-4 h-4" />
          Contacter
        </button>

        {/* Select button */}
        {annonce.status === 'PUBLIEE' && !isSelected && (
          <button
            onClick={() => onSelect(response.id)}
            disabled={selecting === response.id}
            className="flex-1 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50"
            data-testid="select-professional-btn"
          >
            {selecting === response.id ? 'Sélection...' : 'Choisir ce professionnel'}
          </button>
        )}
      </div>

      {canReview && (
        <div className="mt-4 pt-4 border-t">
          {hasReviewed ? (
            <div className="flex items-center gap-2 text-green-600 text-sm">
              <CheckCircle className="w-4 h-4" />
              <span>Vous avez déjà laissé un avis</span>
              <Link 
                to={'/dashboard/professional/' + response.professional_id}
                className="text-cyan-600 hover:underline ml-2"
              >
                Voir le profil
              </Link>
            </div>
          ) : (
            <button
              onClick={() => onOpenReview(response.professional_id, response.professional_name)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-medium hover:from-purple-700 hover:to-cyan-600"
              data-testid="review-professional-btn"
            >
              <Star className="w-4 h-4" />
              Donner mon avis
            </button>
          )}
        </div>
      )}
    </div>
  );
};

function AnnonceDetailPage() {
  const params = useParams();
  const navigate = useNavigate();
  const [annonce, setAnnonce] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selecting, setSelecting] = useState(null);
  const [closing, setClosing] = useState(false);
  const [reviewModalData, setReviewModalData] = useState(null);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewedProfessionals, setReviewedProfessionals] = useState([]);
  
  // Matched professionals state
  const [showMatchedPros, setShowMatchedPros] = useState(false);
  const [matchedPros, setMatchedPros] = useState([]);
  const [loadingPros, setLoadingPros] = useState(false);
  const [selectedPros, setSelectedPros] = useState([]);
  const [notifying, setNotifying] = useState(false);

  useEffect(() => {
    loadAnnonce();
  }, [params.annonceId]);

  const loadAnnonce = async () => {
    try {
      const response = await api.get('/annonces/my-annonces/' + params.annonceId);
      setAnnonce(response.data);
      
      if (response.data.selected_response_id) {
        const responses = response.data.responses || [];
        for (let i = 0; i < responses.length; i++) {
          if (responses[i].id === response.data.selected_response_id) {
            await checkIfReviewed();
            break;
          }
        }
      }
    } catch (error) {
      console.error('Error loading annonce:', error);
    }
    setLoading(false);
  };

  const checkIfReviewed = async () => {
    try {
      const response = await api.get('/reviews/my-reviews');
      const reviews = response.data || [];
      const reviewed = reviews
        .filter(r => r.target_type === 'professional')
        .map(r => r.target_id);
      setReviewedProfessionals(reviewed);
    } catch (error) {
      console.error('Error checking reviews:', error);
    }
  };

  const openReviewModal = (professionalId, professionalName) => {
    setReviewModalData({ id: professionalId, name: professionalName });
  };

  const closeReviewModal = () => {
    setReviewModalData(null);
  };

  const handleSubmitReview = async (data) => {
    if (!reviewModalData) return;
    setSubmittingReview(true);
    try {
      await api.post('/reviews', {
        target_type: 'professional',
        target_id: reviewModalData.id,
        rating: data.rating,
        comment: data.comment || null
      });
      
      setReviewedProfessionals([...reviewedProfessionals, reviewModalData.id]);
      alert('Merci pour votre avis sur ' + reviewModalData.name + ' !');
      closeReviewModal();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'envoi');
    }
    setSubmittingReview(false);
  };

  const handleSelectProfessional = async (responseId) => {
    if (!window.confirm('Voulez-vous sélectionner ce professionnel ?')) return;
    setSelecting(responseId);
    try {
      await api.post('/annonces/my-annonces/' + params.annonceId + '/select-response/' + responseId);
      loadAnnonce();
      alert('Professionnel sélectionné ! Ses coordonnées sont maintenant visibles.');
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur');
    }
    setSelecting(null);
  };

  const handleCloseAnnonce = async () => {
    if (!window.confirm('Voulez-vous clôturer cette annonce ?')) return;
    setClosing(true);
    try {
      await api.post('/annonces/my-annonces/' + params.annonceId + '/close');
      loadAnnonce();
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur');
    }
    setClosing(false);
  };

  const handleContactProfessional = async (professionalId, professionalName) => {
    // Start a conversation with this professional about this annonce
    try {
      const response = await api.post('/direct-messages/start', {
        recipient_id: professionalId,
        initial_message: `Bonjour ${professionalName}, je souhaite discuter de mon annonce "${annonce.title}". Pouvez-vous me donner plus de détails sur votre offre ?`,
        annonce_id: params.annonceId
      });
      
      // Navigate to messages with the new conversation
      navigate('/dashboard/messages?conversation=' + response.data.conversation_id);
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors du démarrage de la conversation');
    }
  };

  // Load matched professionals for this annonce
  const loadMatchedProfessionals = async () => {
    setLoadingPros(true);
    try {
      const response = await api.get(`/annonces/matched-professionals/${params.annonceId}`);
      // API returns 'professionals' not 'matched_professionals'
      setMatchedPros(response.data.professionals || response.data.matched_professionals || []);
      setShowMatchedPros(true);
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors du chargement des professionnels');
    }
    setLoadingPros(false);
  };

  // Toggle professional selection
  const toggleProSelection = (proId) => {
    setSelectedPros(prev => 
      prev.includes(proId) 
        ? prev.filter(id => id !== proId) 
        : [...prev, proId]
    );
  };

  // Notify selected professionals
  const notifySelectedPros = async () => {
    if (selectedPros.length === 0) {
      alert('Sélectionnez au moins un professionnel');
      return;
    }
    
    setNotifying(true);
    try {
      await api.post(`/annonces/notify-professionals/${params.annonceId}`, {
        professional_ids: selectedPros
      });
      alert(`✅ ${selectedPros.length} professionnel(s) notifié(s) par email et notification !`);
      setShowMatchedPros(false);
      setSelectedPros([]);
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la notification');
    }
    setNotifying(false);
  };

  const formatDate = (d) => {
    return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const getStatusStyle = (status) => {
    const styles = {
      'EN_ATTENTE': 'bg-yellow-100 text-yellow-800',
      'PUBLIEE': 'bg-green-100 text-green-800',
      'REFUSEE': 'bg-red-100 text-red-800',
      'ATTRIBUEE': 'bg-purple-100 text-purple-800',
      'CLOTUREE': 'bg-gray-100 text-gray-800'
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusLabel = (status) => {
    const labels = {
      'EN_ATTENTE': 'En attente de validation',
      'PUBLIEE': 'Publiée',
      'REFUSEE': 'Refusée',
      'ATTRIBUEE': 'Attribuée',
      'CLOTUREE': 'Clôturée'
    };
    return labels[status] || status;
  };

  const goToMyAnnonces = () => navigate('/dashboard/my-annonces');

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!annonce) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">Annonce non trouvée</p>
          <button onClick={goToMyAnnonces} className="mt-4 text-cyan-600">
            Retour aux annonces
          </button>
        </div>
      </DashboardLayout>
    );
  }

  const responses = annonce.responses || [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button onClick={goToMyAnnonces} className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">{annonce.title}</h1>
            <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {annonce.city}
              </span>
              <span>{annonce.category}</span>
            </div>
          </div>
          <span className={'px-3 py-1 rounded-full text-sm font-medium ' + getStatusStyle(annonce.status)}>
            {getStatusLabel(annonce.status)}
          </span>
        </div>

        {/* Main content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Annonce details */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm p-5 sticky top-6">
              <h3 className="font-semibold mb-3">Détails de l'annonce</h3>
              <p className="text-gray-700 mb-4">{annonce.description}</p>
              
              {annonce.address && (
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Adresse:</strong> {annonce.address}
                </p>
              )}
              
              <p className="text-sm text-gray-500">
                Publiée le {formatDate(annonce.created_at)}
              </p>

              {annonce.status === 'REFUSEE' && annonce.admin_notes && (
                <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-800">
                    <strong>Raison du refus:</strong> {annonce.admin_notes}
                  </p>
                </div>
              )}

              {(annonce.status === 'PUBLIEE' || annonce.status === 'ATTRIBUEE') && (
                <button
                  onClick={handleCloseAnnonce}
                  disabled={closing}
                  className="mt-4 w-full py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  {closing ? 'Fermeture...' : 'Clôturer l\'annonce'}
                </button>
              )}

              {/* Button to see matched professionals */}
              {(annonce.status === 'EN_ATTENTE' || annonce.status === 'PUBLIEE') && (
                <button
                  onClick={loadMatchedProfessionals}
                  disabled={loadingPros}
                  className="mt-3 w-full py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:from-purple-700 hover:to-cyan-600 disabled:opacity-50 flex items-center justify-center gap-2"
                  data-testid="view-matched-pros-btn"
                >
                  {loadingPros ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Users className="w-4 h-4" />
                  )}
                  Voir les pros recommandés
                </button>
              )}
            </div>
          </div>

          {/* Responses */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="font-semibold text-lg">
              Réponses des professionnels ({responses.length})
            </h3>

            {responses.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm p-8 text-center">
                {annonce.status === 'EN_ATTENTE' ? (
                  <>
                    <Clock className="w-12 h-12 text-yellow-400 mx-auto mb-3" />
                    <p className="text-gray-600">Votre annonce est en attente de validation par l'admin.</p>
                  </>
                ) : annonce.status === 'PUBLIEE' ? (
                  <>
                    <User className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-600">Aucune réponse pour le moment. Les professionnels peuvent voir votre annonce.</p>
                  </>
                ) : (
                  <p className="text-gray-500">Aucune réponse</p>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {responses.map((response) => (
                  <ResponseCard
                    key={response.id}
                    response={response}
                    annonce={annonce}
                    reviewedProfessionals={reviewedProfessionals}
                    selecting={selecting}
                    onSelect={handleSelectProfessional}
                    onOpenReview={openReviewModal}
                    onContact={handleContactProfessional}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Review Modal */}
      {reviewModalData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold mb-4">Votre avis sur {reviewModalData.name}</h3>
            <ReviewForm
              onSubmit={handleSubmitReview}
              isLoading={submittingReview}
              targetName={reviewModalData.name}
            />
            <button
              onClick={closeReviewModal}
              className="mt-4 w-full py-2 text-gray-600 hover:text-gray-800"
            >
              Annuler
            </button>
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
                  onClick={() => { setShowMatchedPros(false); setSelectedPros([]); }}
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
                  <p className="text-sm mt-1">Revenez plus tard ou modifiez votre annonce</p>
                </div>
              ) : (
                matchedPros.map((pro, index) => {
                  const isSelected = selectedPros.includes(pro.id);
                  return (
                    <div
                      key={pro.id}
                      onClick={() => toggleProSelection(pro.id)}
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
                          <div className="flex items-center gap-4 mt-2 text-sm flex-wrap">
                            <span className={'flex items-center gap-1 ' + (pro.is_same_city ? 'text-green-600 font-medium' : 'text-gray-500')}>
                              <MapPin className="w-4 h-4" />
                              {pro.city || 'Non spécifié'}
                              {pro.is_same_city && ' ✓'}
                            </span>
                            
                            {pro.average_rating && (
                              <span className="flex items-center gap-1 text-yellow-600">
                                <Star className="w-4 h-4 fill-current" />
                                {pro.average_rating}/5
                              </span>
                            )}
                          </div>
                          
                          {/* Match Reasons */}
                          {pro.match_reasons && pro.match_reasons.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {pro.match_reasons.slice(0, 3).map((reason, i) => (
                                <span key={i} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                                  {reason}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        
                        {/* Checkbox */}
                        <div className={'w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 ' +
                          (isSelected ? 'bg-purple-500 border-purple-500 text-white' : 'border-gray-300')}>
                          {isSelected && <CheckCircle className="w-4 h-4" />}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
            
            {/* Footer with action buttons */}
            {matchedPros.length > 0 && (
              <div className="p-4 border-t bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-600">
                    {selectedPros.length} professionnel(s) sélectionné(s)
                  </span>
                  <button
                    onClick={() => setSelectedPros(matchedPros.map(p => p.id))}
                    className="text-sm text-purple-600 hover:text-purple-700"
                  >
                    Tout sélectionner
                  </button>
                </div>
                <button
                  onClick={notifySelectedPros}
                  disabled={selectedPros.length === 0 || notifying}
                  className="w-full py-3 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-medium hover:from-purple-700 hover:to-cyan-600 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {notifying ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Mail className="w-5 h-5" />
                  )}
                  {notifying ? 'Envoi en cours...' : 'Notifier les professionnels sélectionnés'}
                </button>
                <p className="text-xs text-gray-500 text-center mt-2">
                  Ils recevront un email et une notification avec votre annonce
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

export default AnnonceDetailPage;
