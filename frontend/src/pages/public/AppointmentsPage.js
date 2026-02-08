import React, { useState, useEffect } from 'react';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import api from '../../services/api';
import { SEO } from '../../components/SEO';

const AppointmentsPage = () => {
  const [services, setServices] = useState([]);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    service_type: '',
    preferred_date: '',
    preferred_time: '',
    message: '',
  });
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await api.get('/services');
        setServices(response.data);
      } catch (error) {
        console.error('Error fetching services:', error);
      }
    };
    fetchServices();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/appointments', formData);
      setSuccess(true);
      setFormData({
        full_name: '',
        email: '',
        phone: '',
        service_type: '',
        preferred_date: '',
        preferred_time: '',
        message: '',
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la création du rendez-vous');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <SEO 
        title="Prendre Rendez-vous - SmartHome Tunisie"
        description="Réservez une consultation gratuite avec nos experts en smart home. Installation vidéophone, alarme, vidéosurveillance, éclairage connecté en Tunisie."
        keywords="rendez-vous domotique, consultation gratuite, installation smart home tunisie, devis domotique"
        url="/rendez-vous"
      />
      <Header />

      <section className="bg-gradient-to-r from-purple-600 to-cyan-500 text-white py-16">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold mb-4" data-testid="appointments-title">
            Prendre Rendez-vous
          </h1>
          <p className="text-xl text-purple-100">
            Réservez votre consultation gratuite avec nos experts
          </p>
        </div>
      </section>

      <section className="py-16 bg-gray-50 flex-1">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg p-8">
            {success ? (
              <div className="text-center py-12" data-testid="appointment-success">
                <div className="text-6xl mb-4">✅</div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  Demande de rendez-vous envoyée !
                </h2>
                <p className="text-gray-600 mb-6">
                  Nous vous contacterons rapidement pour confirmer votre rendez-vous.
                </p>
                <button
                  onClick={() => setSuccess(false)}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 transition-colors"
                >
                  Prendre un autre rendez-vous
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded" data-testid="appointment-error">
                    {error}
                  </div>
                )}

                <div>
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
                    Nom complet *
                  </label>
                  <input
                    type="text"
                    id="full_name"
                    name="full_name"
                    required
                    data-testid="appointment-name-input"
                    value={formData.full_name}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    placeholder="Jean Dupont"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                      Email *
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      required
                      data-testid="appointment-email-input"
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                      placeholder="jean@exemple.com"
                    />
                  </div>
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                      Téléphone *
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      required
                      data-testid="appointment-phone-input"
                      value={formData.phone}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                      placeholder="0123456789"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="service_type" className="block text-sm font-medium text-gray-700 mb-1">
                    Type de service *
                  </label>
                  <select
                    id="service_type"
                    name="service_type"
                    required
                    data-testid="appointment-service-select"
                    value={formData.service_type}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                  >
                    <option value="">Sélectionnez un service</option>
                    {services.map((service) => (
                      <option key={service.id} value={service.name}>
                        {service.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="preferred_date" className="block text-sm font-medium text-gray-700 mb-1">
                      Date souhaitée *
                    </label>
                    <input
                      type="date"
                      id="preferred_date"
                      name="preferred_date"
                      required
                      data-testid="appointment-date-input"
                      value={formData.preferred_date}
                      onChange={handleChange}
                      min={new Date().toISOString().split('T')[0]}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="preferred_time" className="block text-sm font-medium text-gray-700 mb-1">
                      Heure souhaitée *
                    </label>
                    <input
                      type="time"
                      id="preferred_time"
                      name="preferred_time"
                      required
                      data-testid="appointment-time-input"
                      value={formData.preferred_time}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
                    Message (optionnel)
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    rows="4"
                    data-testid="appointment-message-input"
                    value={formData.message}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    placeholder="Décrivez brièvement votre projet..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  data-testid="appointment-submit-button"
                  className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-semibold hover:opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Envoi...' : 'Demander un rendez-vous'}
                </button>
              </form>
            )}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default AppointmentsPage;
