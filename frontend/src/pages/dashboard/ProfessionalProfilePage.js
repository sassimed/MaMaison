import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { User, Star, Briefcase, Phone, Mail, Building, ChevronLeft, MessageSquare, Award, TrendingUp } from 'lucide-react';
import { StarRating, RatingDistribution, ReviewCard, ReviewForm } from '../../components/reviews/StarRating';

function ProfessionalProfilePage() {
  const params = useParams();
  const navigate = useNavigate();
  const [professional, setProfessional] = useState(null);
  const [stats, setStats] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reviewCursor, setReviewCursor] = useState(null);
  const [hasMoreReviews, setHasMoreReviews] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [canReview, setCanReview] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  const [currentUserId, setCurrentUserId] = useState(null);

  useEffect(() => {
    loadData();
  }, [params.professionalId]);

  async function loadData() {
    setLoading(true);
    try {
      // Get reviews and professional info
      const res = await api.get('/reviews/professional/' + params.professionalId);
      setProfessional(res.data.professional);
      setStats(res.data.stats);
      setReviews(res.data.reviews);
      setReviewCursor(res.data.pagination.next_cursor);
      setHasMoreReviews(res.data.pagination.has_more);
      
      // Check if user can review
      await checkCanReview();
      
      // Get current user
      try {
        const userRes = await api.get('/user/profile');
        setCurrentUserId(userRes.data.id);
        
        // Check if user already reviewed
        const userReview = res.data.reviews.find(r => r.user_id === userRes.data.id);
        if (userReview) setHasReviewed(true);
      } catch (e) {
        // Not logged in
      }
    } catch (err) {
      console.error('Error loading professional:', err);
    }
    setLoading(false);
  }

  async function checkCanReview() {
    try {
      // Check if user has a completed annonce with this professional
      const res = await api.get('/annonces/my-annonces');
      const annonces = res.data || [];
      
      const hasWorkedWith = annonces.some(a => {
        if (!['ATTRIBUEE', 'CLOTUREE'].includes(a.status)) return false;
        const selectedResponse = (a.responses || []).find(r => r.id === a.selected_response_id);
        return selectedResponse && selectedResponse.professional_id === params.professionalId;
      });
      
      setCanReview(hasWorkedWith);
    } catch (err) {
      // Not logged in or error
      setCanReview(false);
    }
  }

  async function loadMoreReviews() {
    if (!reviewCursor || loadingMore) return;
    
    setLoadingMore(true);
    try {
      const res = await api.get('/reviews/professional/' + params.professionalId + '?cursor=' + reviewCursor);
      setReviews(prev => [...prev, ...res.data.reviews]);
      setReviewCursor(res.data.pagination.next_cursor);
      setHasMoreReviews(res.data.pagination.has_more);
    } catch (err) {
      console.error('Error loading more reviews:', err);
    }
    setLoadingMore(false);
  }

  async function handleSubmitReview(data) {
    setSubmittingReview(true);
    try {
      await api.post('/reviews', {
        target_type: 'professional',
        target_id: params.professionalId,
        rating: data.rating,
        comment: data.comment || null
      });
      
      // Refresh data
      await loadData();
      setShowReviewForm(false);
      setHasReviewed(true);
      alert('Merci pour votre avis !');
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'envoi');
    }
    setSubmittingReview(false);
  }

  async function handleDeleteReview(reviewId) {
    if (!window.confirm('Supprimer votre avis ?')) return;
    
    try {
      await api.delete('/reviews/' + reviewId);
      setReviews(reviews.filter(r => r.id !== reviewId));
      setHasReviewed(false);
      // Refresh stats
      const res = await api.get('/reviews/professional/' + params.professionalId + '/stats');
      setStats(res.data);
    } catch (err) {
      alert('Erreur lors de la suppression');
    }
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

  if (!professional) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">Professionnel non trouvé</p>
          <button onClick={() => navigate(-1)} className="text-cyan-600 hover:underline">
            Retour
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Profil Professionnel</h1>
        </div>

        {/* Profile Card */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Avatar and basic info */}
            <div className="flex-shrink-0">
              <div className="w-24 h-24 bg-gradient-to-r from-purple-600 to-cyan-500 rounded-full flex items-center justify-center text-white text-3xl font-bold">
                {professional.name?.charAt(0) || 'P'}
              </div>
            </div>
            
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-gray-900">{professional.name}</h2>
              
              {professional.company_name && (
                <p className="flex items-center gap-2 text-gray-600 mt-1">
                  <Building className="w-4 h-4" />
                  {professional.company_name}
                </p>
              )}
              
              <div className="flex items-center gap-4 mt-3">
                {stats && stats.total_reviews > 0 ? (
                  <div className="flex items-center gap-2">
                    <StarRating rating={stats.average_rating} size="md" />
                    <span className="font-medium">{stats.average_rating.toFixed(1)}</span>
                    <span className="text-gray-500">({stats.total_reviews} avis)</span>
                  </div>
                ) : (
                  <span className="text-gray-400">Aucun avis</span>
                )}
              </div>
              
              <div className="flex flex-wrap gap-4 mt-4">
                {stats && stats.intervention_count > 0 && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg">
                    <Briefcase className="w-5 h-5" />
                    <span className="font-medium">{stats.intervention_count} intervention{stats.intervention_count > 1 ? 's' : ''}</span>
                  </div>
                )}
                
                {professional.email && (
                  <a href={'mailto:' + professional.email}
                    className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                    <Mail className="w-5 h-5" />
                    {professional.email}
                  </a>
                )}
                
                {professional.phone && (
                  <a href={'tel:' + professional.phone}
                    className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                    <Phone className="w-5 h-5" />
                    {professional.phone}
                  </a>
                )}
              </div>
            </div>
            
            {/* Action */}
            {canReview && !hasReviewed && (
              <div>
                <button
                  onClick={() => setShowReviewForm(true)}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-medium hover:from-purple-700 hover:to-cyan-600"
                  data-testid="write-review-btn"
                >
                  Donner mon avis
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Review Form Modal */}
        {showReviewForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-md w-full p-6">
              <h3 className="text-xl font-bold mb-4">Votre avis sur {professional.name}</h3>
              <ReviewForm
                onSubmit={handleSubmitReview}
                isLoading={submittingReview}
                targetName={professional.name}
              />
              <button
                onClick={() => setShowReviewForm(false)}
                className="mt-4 w-full py-2 text-gray-600 hover:text-gray-800"
              >
                Annuler
              </button>
            </div>
          </div>
        )}

        {/* Reviews Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Stats */}
          <div className="lg:col-span-1">
            {stats && stats.total_reviews > 0 ? (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Star className="w-5 h-5 text-yellow-400" />
                  Note globale
                </h3>
                
                <div className="text-center mb-6">
                  <p className="text-5xl font-bold text-gray-900">{stats.average_rating.toFixed(1)}</p>
                  <StarRating rating={stats.average_rating} size="lg" className="justify-center mt-2" />
                  <p className="text-sm text-gray-500 mt-2">{stats.total_reviews} avis</p>
                </div>
                
                <RatingDistribution 
                  distribution={stats.rating_distribution} 
                  total={stats.total_reviews} 
                />
                
                {stats.intervention_count > 0 && (
                  <div className="mt-6 pt-6 border-t">
                    <div className="flex items-center justify-center gap-2 text-green-600">
                      <TrendingUp className="w-5 h-5" />
                      <span className="font-medium">{stats.intervention_count} missions réalisées</span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm p-6 text-center">
                <Star className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Aucun avis pour le moment</p>
              </div>
            )}
          </div>

          {/* Reviews List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-cyan-500" />
                Avis clients ({stats?.total_reviews || 0})
              </h3>
              
              {reviews.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>Aucun avis client</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {reviews.map(review => (
                    <ReviewCard
                      key={review.id}
                      review={review}
                      onDelete={handleDeleteReview}
                      currentUserId={currentUserId}
                    />
                  ))}
                  
                  {hasMoreReviews && (
                    <button
                      onClick={loadMoreReviews}
                      disabled={loadingMore}
                      className="w-full py-3 text-cyan-600 hover:text-cyan-700 font-medium disabled:opacity-50"
                    >
                      {loadingMore ? 'Chargement...' : 'Voir plus d\'avis'}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default ProfessionalProfilePage;
