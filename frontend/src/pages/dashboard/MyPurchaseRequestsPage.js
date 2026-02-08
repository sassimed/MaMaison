import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { Package, Clock, CheckCircle, XCircle, AlertCircle, Download, FileText, Copy } from 'lucide-react';

function MyPurchaseRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [downloading, setDownloading] = useState(null);

  useEffect(function() {
    loadRequests();
  }, []);

  async function loadRequests() {
    try {
      var response = await api.get('/my-purchase-requests');
      setRequests(response.data);
    } catch (error) {
      console.error('Error loading requests:', error);
    }
    setLoading(false);
  }

  function getStatusIcon(status) {
    if (status === 'EN_ATTENTE') return Clock;
    if (status === 'EN_COURS') return AlertCircle;
    if (status === 'VALIDEE') return CheckCircle;
    if (status === 'REFUSEE') return XCircle;
    return Clock;
  }

  function getStatusStyle(status) {
    if (status === 'EN_ATTENTE') return 'bg-yellow-100 text-yellow-800';
    if (status === 'EN_COURS') return 'bg-blue-100 text-blue-800';
    if (status === 'VALIDEE') return 'bg-green-100 text-green-800';
    if (status === 'REFUSEE') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  }

  function getStatusLabel(status) {
    if (status === 'EN_ATTENTE') return 'En attente';
    if (status === 'EN_COURS') return 'En cours de traitement';
    if (status === 'VALIDEE') return 'Validée';
    if (status === 'REFUSEE') return 'Refusée';
    return status;
  }

  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric', month: 'long', year: 'numeric'
    });
  }

  function toggleExpand(id) {
    setExpandedId(expandedId === id ? null : id);
  }

  function copyOrderNumber(orderNum, e) {
    e.stopPropagation();
    var btn = e.currentTarget;
    var originalHtml = btn.innerHTML;
    
    // Try to copy to clipboard
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(orderNum).catch(function() {
        // Fallback for older browsers
        var textArea = document.createElement('textarea');
        textArea.value = orderNum;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      });
    }
    
    // Visual feedback - show checkmark
    btn.innerHTML = '<svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
    btn.classList.add('bg-green-100');
    btn.classList.remove('hover:bg-purple-100');
    setTimeout(function() {
      btn.innerHTML = originalHtml;
      btn.classList.remove('bg-green-100');
      btn.classList.add('hover:bg-purple-100');
    }, 1500);
  }

  async function handleDownloadInvoice(requestId, invoiceNumber) {
    setDownloading(requestId);
    try {
      var response = await api.get('/my-purchase-requests/' + requestId + '/invoice', {
        responseType: 'blob'
      });
      var blob = new Blob([response.data], { type: 'application/pdf' });
      var url = window.URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'facture_' + (invoiceNumber || requestId.slice(0, 8)) + '.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      if (error.response && error.response.status === 400) {
        alert('La facture n\'est pas encore disponible. Veuillez attendre la validation de votre commande.');
      } else {
        alert('Erreur lors du téléchargement de la facture');
      }
      console.error(error);
    }
    setDownloading(null);
  }

  function renderProductItem(item, idx) {
    return (
      <div key={idx} className="flex justify-between bg-white p-3 rounded-lg mb-2">
        <div>
          <p className="font-medium">{item.product_name}</p>
          <p className="text-sm text-gray-500">Qté: {item.quantity} × {item.product_price ? item.product_price.toFixed(3) + ' DT' : '—'}</p>
        </div>
        <span className="font-semibold">{item.product_price ? (item.product_price * item.quantity).toFixed(3) + ' DT' : '—'}</span>
      </div>
    );
  }

  function renderRequestItem(request) {
    var StatusIcon = getStatusIcon(request.status);
    var isExpanded = expandedId === request.id;
    var items = request.items || [];
    var canDownloadInvoice = request.status === 'VALIDEE' && request.invoice_number;
    var orderNumber = '#' + request.id.slice(0, 8).toUpperCase();

    return (
      <div key={request.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 cursor-pointer hover:bg-gray-50" onClick={function() { toggleExpand(request.id); }}>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-cyan-500 rounded-lg flex items-center justify-center">
                <Package className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">Commande {orderNumber}</h3>
                  <button 
                    onClick={function(e) { copyOrderNumber(orderNumber, e); }}
                    className="p-1.5 hover:bg-purple-100 rounded-lg text-purple-500 transition-colors"
                    title="Copier le numéro pour le chatbot"
                    data-testid={'copy-order-' + request.id}
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-sm text-gray-500">{formatDate(request.created_at)}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 flex-wrap">
              <span className="text-lg font-bold text-cyan-600">{request.total_estimated ? request.total_estimated.toFixed(3) : '—'} DT</span>
              <span className={'inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ' + getStatusStyle(request.status)}>
                <StatusIcon className="w-4 h-4" />
                {getStatusLabel(request.status)}
              </span>
              {request.invoice_number && (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                  <FileText className="w-4 h-4" />
                  {request.invoice_number}
                </span>
              )}
            </div>
          </div>
        </div>
        {isExpanded && (
          <div className="border-t bg-gray-50 p-4">
            <h4 className="font-medium mb-3">Détail de la commande</h4>
            {items.map(renderProductItem)}
            
            <div className="mt-4 pt-3 border-t">
              <div className="flex justify-between text-sm text-gray-600">
                <span>Sous-total HT</span>
                <span>{request.total_estimated ? request.total_estimated.toFixed(3) : '—'} DT</span>
              </div>
              {request.discount > 0 && (
                <div className="flex justify-between text-sm text-purple-600">
                  <span>Remise fidélité ({request.points_used} pts)</span>
                  <span>-{request.discount.toFixed(3)} DT</span>
                </div>
              )}
              <div className="flex justify-between text-sm text-gray-600">
                <span>TVA (19%)</span>
                <span>{request.total_estimated ? ((request.total_estimated - (request.discount || 0)) * 0.19).toFixed(3) : '—'} DT</span>
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>Timbre fiscal</span>
                <span>1.000 DT</span>
              </div>
              <div className="flex justify-between font-bold text-lg mt-2 pt-2 border-t">
                <span>Total TTC</span>
                <span className="text-purple-600">{request.total_estimated ? ((request.total_estimated - (request.discount || 0)) * 1.19 + 1).toFixed(3) : '—'} DT</span>
              </div>
              {request.points_earned > 0 && (
                <p className="text-sm text-green-600 mt-2">+{request.points_earned} points gagnés</p>
              )}
            </div>

            {request.admin_notes && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-900">Message de SmartHome :</p>
                <p className="text-sm text-blue-800">{request.admin_notes}</p>
              </div>
            )}

            {/* Invoice Download Button */}
            {canDownloadInvoice && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-green-800 font-medium">Commande validée</span>
                  </div>
                  <button
                    onClick={function(e) { e.stopPropagation(); handleDownloadInvoice(request.id, request.invoice_number); }}
                    disabled={downloading === request.id}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    data-testid={'download-invoice-' + request.id}
                  >
                    {downloading === request.id ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <Download className="w-4 h-4" />
                    )}
                    Télécharger ma facture
                  </button>
                </div>
              </div>
            )}

            {request.status === 'VALIDEE' && !request.invoice_number && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  Votre commande est validée. La facture sera bientôt disponible.
                </p>
              </div>
            )}

            {request.status === 'EN_ATTENTE' && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  Votre demande est en cours d'examen. Nous vous contacterons bientôt.
                </p>
              </div>
            )}

            {request.status === 'EN_COURS' && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  Votre commande est en cours de traitement. La facture sera disponible après validation.
                </p>
              </div>
            )}

            {request.status === 'REFUSEE' && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">
                  Votre demande n'a pas pu être acceptée. Contactez-nous pour plus d'informations.
                </p>
              </div>
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

  var requestList = requests || [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <Package className="w-7 h-7 text-cyan-500" />
          Mes Commandes
        </h1>

        {requestList.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Aucune commande</h2>
            <p className="text-gray-500">Vos demandes d'achat apparaîtront ici</p>
          </div>
        ) : (
          <div className="space-y-4">
            {requestList.map(renderRequestItem)}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default MyPurchaseRequestsPage;
