import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { Send, MapPin, Clock, CheckCircle, Award, ChevronLeft, User, DollarSign, Calendar, Eye } from 'lucide-react';

function MyResponsesPage() {
  var navigate = useNavigate();
  var [annonces, setAnnonces] = useState([]);
  var [loading, setLoading] = useState(true);

  useEffect(function() {
    loadMyResponses();
  }, []);

  async function loadMyResponses() {
    try {
      var response = await api.get('/annonces/my-responses');
      setAnnonces(response.data);
    } catch (error) {
      console.error('Error loading responses:', error);
      if (error.response?.status === 403) {
        alert('Accès réservé aux professionnels');
        navigate('/dashboard');
      }
    }
    setLoading(false);
  }

  function formatDate(d) {
    return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  function getStatusStyle(status, isSelected) {
    if (isSelected) return 'bg-green-100 text-green-800';
    if (status === 'PUBLIEE') return 'bg-blue-100 text-blue-800';
    if (status === 'ATTRIBUEE') return 'bg-purple-100 text-purple-800';
    if (status === 'CLOTUREE') return 'bg-gray-100 text-gray-800';
    return 'bg-gray-100 text-gray-800';
  }

  function getStatusLabel(status, isSelected) {
    if (isSelected) return 'Vous êtes sélectionné !';
    if (status === 'PUBLIEE') return 'En attente de décision';
    if (status === 'ATTRIBUEE') return 'Attribué à un autre';
    if (status === 'CLOTUREE') return 'Annonce clôturée';
    return status;
  }

  function renderAnnonceCard(annonce) {
    var myResponse = annonce.my_response;
    var isSelected = annonce.is_selected;
    
    return (
      <div key={annonce.id} className={'bg-white rounded-xl shadow-sm p-6 border-2 transition-shadow ' + (isSelected ? 'border-green-400' : 'border-transparent hover:shadow-md')}>
        {isSelected && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-green-600" />
            <span className="text-green-800 font-medium">Félicitations ! Le client vous a sélectionné pour cette mission.</span>
          </div>
        )}
        
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="px-3 py-1 bg-gradient-to-r from-purple-100 to-cyan-100 text-purple-700 text-xs font-medium rounded-full">
                {annonce.category}
              </span>
              <span className="flex items-center text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                <MapPin className="w-3 h-3 mr-1" />
                {annonce.city}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">{annonce.title}</h3>
          </div>
          <span className={'px-3 py-1 rounded-full text-xs font-medium ' + getStatusStyle(annonce.status, isSelected)}>
            {getStatusLabel(annonce.status, isSelected)}
          </span>
        </div>
        
        <p className="text-gray-600 mb-4 line-clamp-2">{annonce.description}</p>
        
        <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
          <span className="flex items-center gap-1">
            <User className="w-4 h-4" />
            {annonce.client_name}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {formatDate(annonce.created_at)}
          </span>
        </div>
        
        {/* My Response */}
        {myResponse && (
          <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-cyan-500">
            <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Send className="w-4 h-4" />
              Ma réponse
            </h4>
            <p className="text-sm text-gray-600 mb-2">{myResponse.message}</p>
            <div className="flex flex-wrap gap-4 text-xs text-gray-500">
              {myResponse.price_estimate && (
                <span className="flex items-center gap-1">
                  <DollarSign className="w-3 h-3" />
                  {myResponse.price_estimate.toFixed(2)} DT
                </span>
              )}
              {myResponse.availability && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {myResponse.availability}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Envoyé le {formatDate(myResponse.created_at)}
              </span>
            </div>
          </div>
        )}
        
        {/* Contact info if selected */}
        {isSelected && (
          <div className="mt-4 bg-green-50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-green-800 mb-2">Coordonnées du client</h4>
            <p className="text-sm text-green-700">Email : {annonce.client_email}</p>
            {annonce.client_phone && (
              <p className="text-sm text-green-700">Téléphone : {annonce.client_phone}</p>
            )}
            {annonce.address && (
              <p className="text-sm text-green-700">Adresse : {annonce.address}</p>
            )}
          </div>
        )}
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
        {/* Header */}
        <div className="flex items-center gap-4">
          <button
            onClick={function() { navigate('/dashboard/annonces'); }}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <Send className="w-7 h-7 text-cyan-500" />
              Mes réponses aux annonces
            </h1>
            <p className="text-gray-500 mt-1">Suivez le statut de vos candidatures</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl shadow-sm p-4 flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Send className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{annonces.length}</p>
              <p className="text-sm text-gray-500">Réponses envoyées</p>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-4 flex items-center gap-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{annonces.filter(function(a) { return a.status === 'PUBLIEE'; }).length}</p>
              <p className="text-sm text-gray-500">En attente</p>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-4 flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <Award className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{annonces.filter(function(a) { return a.is_selected; }).length}</p>
              <p className="text-sm text-gray-500">Missions obtenues</p>
            </div>
          </div>
        </div>

        {/* List */}
        {annonces.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Send className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Aucune réponse envoyée</h2>
            <p className="text-gray-500 mb-4">Parcourez les annonces disponibles et envoyez vos premières propositions</p>
            <button
              onClick={function() { navigate('/dashboard/annonces'); }}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:from-purple-700 hover:to-cyan-600"
            >
              Voir les annonces
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {annonces.map(renderAnnonceCard)}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default MyResponsesPage;
