import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { Package, Filter, Eye, XCircle, Mail, Phone, FileText, Download, CheckCircle, Search, Copy } from 'lucide-react';

function AdminPurchaseRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [updating, setUpdating] = useState(false);
  const [generatingInvoice, setGeneratingInvoice] = useState(false);
  const [stats, setStats] = useState(null);
  const [newStatus, setNewStatus] = useState('');
  const [adminNotes, setAdminNotes] = useState('');

  useEffect(function() {
    loadData();
  }, [filterStatus]);

  async function loadData() {
    try {
      var url = filterStatus ? '/admin/purchase-requests?status=' + filterStatus : '/admin/purchase-requests';
      var requestsRes = await api.get(url);
      var statsRes = await api.get('/admin/purchase-requests/stats/summary');
      setRequests(requestsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
    setLoading(false);
  }

  function openDetail(req) {
    setSelectedRequest(req);
    setNewStatus(req.status);
    setAdminNotes(req.admin_notes || '');
  }

  function closeDetail() {
    setSelectedRequest(null);
  }

  async function handleUpdate() {
    if (!selectedRequest) return;
    setUpdating(true);
    try {
      await api.patch('/admin/purchase-requests/' + selectedRequest.id, {
        status: newStatus,
        admin_notes: adminNotes
      });
      loadData();
      closeDetail();
    } catch (error) {
      alert('Erreur lors de la mise à jour');
    }
    setUpdating(false);
  }

  async function handleDelete(rid) {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette demande ?')) return;
    try {
      await api.delete('/admin/purchase-requests/' + rid);
      loadData();
      closeDetail();
    } catch (e) {
      alert('Erreur lors de la suppression');
    }
  }

  async function handleGenerateInvoice() {
    if (!selectedRequest) return;
    setGeneratingInvoice(true);
    try {
      var response = await api.post('/admin/purchase-requests/' + selectedRequest.id + '/generate-invoice');
      alert('Facture générée avec succès ! N°' + response.data.invoice_number);
      // Reload to get updated invoice_number
      loadData();
      // Update selected request with invoice info
      setSelectedRequest({
        ...selectedRequest,
        invoice_number: response.data.invoice_number,
        invoice_id: response.data.invoice_id
      });
    } catch (error) {
      alert('Erreur lors de la génération de la facture');
      console.error(error);
    }
    setGeneratingInvoice(false);
  }

  async function handleDownloadInvoice() {
    if (!selectedRequest) return;
    try {
      var response = await api.get('/admin/purchase-requests/' + selectedRequest.id + '/invoice', {
        responseType: 'blob'
      });
      var blob = new Blob([response.data], { type: 'application/pdf' });
      var url = window.URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'facture_' + (selectedRequest.invoice_number || selectedRequest.id.slice(0, 8)) + '.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('Erreur lors du téléchargement de la facture');
      console.error(error);
    }
  }

  function getStatusStyle(status) {
    if (status === 'EN_ATTENTE') return 'bg-yellow-100 text-yellow-800';
    if (status === 'EN_COURS') return 'bg-blue-100 text-blue-800';
    if (status === 'VALIDEE') return 'bg-green-100 text-green-800';
    if (status === 'REFUSEE') return 'bg-red-100 text-red-800';
    return 'bg-gray-100';
  }

  function getStatusLabel(s) {
    if (s === 'EN_ATTENTE') return 'En attente';
    if (s === 'EN_COURS') return 'En cours';
    if (s === 'VALIDEE') return 'Validée';
    if (s === 'REFUSEE') return 'Refusée';
    return s;
  }

  function formatDate(d) {
    return new Date(d).toLocaleDateString('fr-FR');
  }

  function copyToClipboard(text, e) {
    e.stopPropagation();
    var btn = e.currentTarget;
    var originalHtml = btn.innerHTML;
    
    // Try to copy to clipboard
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(function() {
        // Fallback for older browsers
        var textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      });
    }
    
    // Visual feedback - show checkmark
    btn.innerHTML = '<svg class="w-3.5 h-3.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
    btn.classList.add('bg-green-100');
    setTimeout(function() {
      btn.innerHTML = originalHtml;
      btn.classList.remove('bg-green-100');
    }, 1500);
  }

  // Filter requests by search query
  var filteredRequests = (requests || []).filter(function(req) {
    if (!searchQuery) return true;
    var query = searchQuery.toLowerCase();
    var orderNum = req.id.slice(0, 8).toLowerCase();
    return orderNum.includes(query) || 
           req.user_name.toLowerCase().includes(query) ||
           req.user_email.toLowerCase().includes(query) ||
           (req.user_phone && req.user_phone.includes(query));
  });

  function renderRequestRow(req) {
    var orderNumber = '#' + req.id.slice(0, 8).toUpperCase();
    return (
      <tr key={req.id} className="hover:bg-gray-50">
        <td className="px-4 py-4">
          <div className="flex items-center gap-2">
            <span className="font-mono font-bold text-purple-600">{orderNumber}</span>
            <button 
              onClick={function(e) { copyToClipboard(orderNumber, e); }}
              className="p-1 hover:bg-purple-100 rounded text-purple-500 transition-colors"
              title="Copier le numéro"
            >
              <Copy className="w-3.5 h-3.5" />
            </button>
          </div>
        </td>
        <td className="px-4 py-4">
          <p className="font-medium">{req.user_name}</p>
          <p className="text-sm text-gray-500">{req.user_email}</p>
        </td>
        <td className="px-4 py-4 text-sm">{formatDate(req.created_at)}</td>
        <td className="px-4 py-4 text-sm">{req.items.length} article(s)</td>
        <td className="px-4 py-4 font-semibold text-cyan-600">{req.total_estimated ? req.total_estimated.toFixed(3) : '—'} DT</td>
        <td className="px-4 py-4">
          <span className={'px-2 py-1 rounded-full text-xs font-medium ' + getStatusStyle(req.status)}>
            {getStatusLabel(req.status)}
          </span>
          {req.invoice_number && (
            <span className="ml-2 px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              {req.invoice_number}
            </span>
          )}
        </td>
        <td className="px-4 py-4 text-right">
          <button onClick={function() { openDetail(req); }} className="text-cyan-600 hover:text-cyan-700 p-2" data-testid={'view-request-' + req.id}>
            <Eye className="w-5 h-5" />
          </button>
        </td>
      </tr>
    );
  }

  function renderProductItem(item, idx) {
    return (
      <div key={idx} className="flex justify-between bg-gray-50 p-3 rounded-lg mb-2">
        <div>
          <p className="font-medium">{item.product_name}</p>
          <p className="text-sm text-gray-500">Qté: {item.quantity} × {item.product_price ? item.product_price.toFixed(3) + ' DT' : '—'}</p>
        </div>
        <span className="font-semibold">{item.product_price ? (item.product_price * item.quantity).toFixed(3) + ' DT' : '—'}</span>
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
        <h1 className="text-2xl font-bold text-gray-900">Demandes d'Achat</h1>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-xl shadow-sm p-4">
              <p className="text-sm text-gray-500">Total</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
            <div className="bg-yellow-50 rounded-xl p-4">
              <p className="text-sm text-yellow-700">En attente</p>
              <p className="text-2xl font-bold text-yellow-800">{stats.pending}</p>
            </div>
            <div className="bg-blue-50 rounded-xl p-4">
              <p className="text-sm text-blue-700">En cours</p>
              <p className="text-2xl font-bold text-blue-800">{stats.in_progress}</p>
            </div>
            <div className="bg-green-50 rounded-xl p-4">
              <p className="text-sm text-green-700">Validées</p>
              <p className="text-2xl font-bold text-green-800">{stats.validated}</p>
            </div>
            <div className="bg-red-50 rounded-xl p-4">
              <p className="text-sm text-red-700">Refusées</p>
              <p className="text-2xl font-bold text-red-800">{stats.refused}</p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm p-4 flex gap-4 items-center flex-wrap">
          <div className="flex items-center gap-2 flex-1 min-w-[200px]">
            <Search className="w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher par n° commande, nom, email..."
              value={searchQuery}
              onChange={function(e) { setSearchQuery(e.target.value); }}
              className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              data-testid="search-orders"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select value={filterStatus} onChange={function(e) { setFilterStatus(e.target.value); }} className="px-3 py-2 border rounded-lg">
              <option value="">Tous</option>
              <option value="EN_ATTENTE">En attente</option>
              <option value="EN_COURS">En cours</option>
              <option value="VALIDEE">Validée</option>
              <option value="REFUSEE">Refusée</option>
            </select>
          </div>
          <span className="text-sm text-gray-500">{filteredRequests.length} demande(s)</span>
        </div>

        {filteredRequests.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold">Aucune demande</h2>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">N° Commande</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Produits</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredRequests.map(renderRequestRow)}
              </tbody>
            </table>
          </div>
        )}

        {selectedRequest && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b flex justify-between items-start">
                <div>
                  <h2 className="text-xl font-bold">Demande #{selectedRequest.id.slice(0, 8).toUpperCase()}</h2>
                  <p className="text-sm text-gray-500">{formatDate(selectedRequest.created_at)}</p>
                  {selectedRequest.invoice_number && (
                    <p className="text-sm text-purple-600 font-medium mt-1">
                      Facture: {selectedRequest.invoice_number}
                    </p>
                  )}
                </div>
                <button onClick={closeDetail} className="text-gray-400 hover:text-gray-600">
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="p-6 space-y-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold mb-2">Client</h3>
                  <p><strong>Nom:</strong> {selectedRequest.user_name}</p>
                  <p className="flex items-center gap-2"><Mail className="w-4 h-4" /> {selectedRequest.user_email}</p>
                  {selectedRequest.user_phone && <p className="flex items-center gap-2"><Phone className="w-4 h-4" /> {selectedRequest.user_phone}</p>}
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Produits</h3>
                  {selectedRequest.items.map(renderProductItem)}
                  <div className="flex justify-between pt-3 border-t mt-3">
                    <span className="font-semibold">Total HT</span>
                    <span className="text-xl font-bold text-cyan-600">{selectedRequest.total_estimated ? selectedRequest.total_estimated.toFixed(3) : '—'} DT</span>
                  </div>
                  {selectedRequest.discount > 0 && (
                    <div className="flex justify-between text-sm text-purple-600">
                      <span>Remise fidélité</span>
                      <span>-{selectedRequest.discount.toFixed(3)} DT</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>TVA (19%)</span>
                    <span>{selectedRequest.total_estimated ? ((selectedRequest.total_estimated - (selectedRequest.discount || 0)) * 0.19).toFixed(3) : '—'} DT</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Timbre fiscal</span>
                    <span>1.000 DT</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t">
                    <span className="font-bold">Total TTC</span>
                    <span className="text-xl font-bold text-purple-600">{selectedRequest.total_estimated ? ((selectedRequest.total_estimated - (selectedRequest.discount || 0)) * 1.19 + 1).toFixed(3) : '—'} DT</span>
                  </div>
                </div>

                {/* Invoice Section */}
                <div className="bg-purple-50 rounded-lg p-4">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-purple-600" />
                    Facture
                  </h3>
                  <div className="flex gap-3 flex-wrap">
                    <button
                      onClick={handleGenerateInvoice}
                      disabled={generatingInvoice}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                      data-testid="generate-invoice-btn"
                    >
                      {generatingInvoice ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <FileText className="w-4 h-4" />
                      )}
                      {selectedRequest.invoice_number ? 'Regénérer la facture' : 'Générer la facture'}
                    </button>
                    
                    {selectedRequest.invoice_number && (
                      <button
                        onClick={handleDownloadInvoice}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                        data-testid="download-invoice-btn"
                      >
                        <Download className="w-4 h-4" />
                        Télécharger PDF
                      </button>
                    )}
                  </div>
                  {selectedRequest.invoice_number && (
                    <p className="text-sm text-purple-700 mt-2 flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      Facture {selectedRequest.invoice_number} générée
                    </p>
                  )}
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold mb-2">Statut</h3>
                  <select value={newStatus} onChange={function(e) { setNewStatus(e.target.value); }} className="w-full px-3 py-2 border rounded-lg mb-3">
                    <option value="EN_ATTENTE">En attente</option>
                    <option value="EN_COURS">En cours</option>
                    <option value="VALIDEE">Validée</option>
                    <option value="REFUSEE">Refusée</option>
                  </select>
                  <label className="block text-sm font-medium mb-1">Notes admin</label>
                  <textarea value={adminNotes} onChange={function(e) { setAdminNotes(e.target.value); }} rows="3" placeholder="Notes internes..." className="w-full px-3 py-2 border rounded-lg" />
                </div>
              </div>

              <div className="p-6 border-t bg-gray-50 flex justify-between flex-wrap gap-3">
                <button onClick={function() { handleDelete(selectedRequest.id); }} className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg">
                  Supprimer
                </button>
                <div className="flex gap-3">
                  <button onClick={closeDetail} className="px-4 py-2 border rounded-lg hover:bg-gray-100">Annuler</button>
                  <button onClick={handleUpdate} disabled={updating} className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50">
                    {updating ? 'Enregistrement...' : 'Enregistrer'}
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

export default AdminPurchaseRequests;
