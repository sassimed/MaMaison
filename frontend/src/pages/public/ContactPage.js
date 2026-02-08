import React, { useState } from 'react';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import api from '../../services/api';
import { SEO } from '../../components/SEO';

const ContactPage = () => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    subject: '',
    message: '',
  });
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/contacts', formData);
      setSuccess(true);
      setFormData({
        full_name: '',
        email: '',
        phone: '',
        subject: '',
        message: '',
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'envoi du message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <SEO 
        title="Contact - SmartHome Tunisie"
        description="Contactez SmartHome pour vos projets de maison connectée en Tunisie. Devis gratuit, conseil personnalisé, installation professionnelle."
        keywords="contact smart home tunisie, devis maison connectée, installation domotique, conseil sécurité connectée"
        url="/contact"
      />
      <Header />

      <section className="bg-gradient-to-r from-purple-600 to-cyan-500 text-white py-16">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold mb-4" data-testid="contact-title">
            Nous Contacter
          </h1>
          <p className="text-xl text-blue-100">
            Une question ? Un projet ? N'hésitez pas à nous contacter
          </p>
        </div>
      </section>

      <section className="py-16 bg-gray-50 flex-1">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Contact Info */}
            <div>
              <h2 className="text-2xl font-bold mb-6 text-gray-900">Nos Coordonnées</h2>
              <div className="space-y-4 mb-8">
                <div className="flex items-start">
                  <span className="text-2xl mr-3">📍</span>
                  <div>
                    <div className="font-semibold text-gray-900">Adresse</div>
                    <div className="text-gray-600">Île-de-France</div>
                  </div>
                </div>
                <div className="flex items-start">
                  <span className="text-2xl mr-3">📞</span>
                  <div>
                    <div className="font-semibold text-gray-900">Téléphone</div>
                    <div className="text-gray-600">01 23 45 67 89</div>
                  </div>
                </div>
                <div className="flex items-start">
                  <span className="text-2xl mr-3">📧</span>
                  <div>
                    <div className="font-semibold text-gray-900">Email</div>
                    <div className="text-gray-600">contact@smarthome.tn</div>
                  </div>
                </div>
                <div className="flex items-start">
                  <span className="text-2xl mr-3">🕑</span>
                  <div>
                    <div className="font-semibold text-gray-900">Horaires</div>
                    <div className="text-gray-600">Lundi - Vendredi : 9h - 18h</div>
                    <div className="text-gray-600">Samedi : 9h - 12h</div>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-xl font-bold mb-4 text-gray-900">Zone d'intervention</h3>
                <p className="text-gray-600">
                  Nous intervenons principalement en Île-de-France et régions limitrophes. 
                  Pour toute demande hors zone, contactez-nous pour étudier la faisabilité.
                </p>
              </div>
            </div>

            {/* Contact Form */}
            <div>
              <div className="bg-white rounded-2xl shadow-lg p-8">
                {success ? (
                  <div className="text-center py-8" data-testid="contact-success">
                    <div className="text-6xl mb-4">✅</div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      Message envoyé !
                    </h2>
                    <p className="text-gray-600 mb-6">
                      Nous vous répondrons dans les plus brefs délais.
                    </p>
                    <button
                      onClick={() => setSuccess(false)}
                      className="px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg hover:opacity-90 transition-colors"
                    >
                      Envoyer un autre message
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-6">
                    {error && (
                      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded" data-testid="contact-error">
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
                        data-testid="contact-name-input"
                        value={formData.full_name}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
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
                          data-testid="contact-email-input"
                          value={formData.email}
                          onChange={handleChange}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                        />
                      </div>
                      <div>
                        <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                          Téléphone
                        </label>
                        <input
                          type="tel"
                          id="phone"
                          name="phone"
                          data-testid="contact-phone-input"
                          value={formData.phone}
                          onChange={handleChange}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-1">
                        Sujet *
                      </label>
                      <input
                        type="text"
                        id="subject"
                        name="subject"
                        required
                        data-testid="contact-subject-input"
                        value={formData.subject}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                      />
                    </div>

                    <div>
                      <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
                        Message *
                      </label>
                      <textarea
                        id="message"
                        name="message"
                        rows="5"
                        required
                        data-testid="contact-message-input"
                        value={formData.message}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={loading}
                      data-testid="contact-submit-button"
                      className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-semibold hover:opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Envoi...' : 'Envoyer le message'}
                    </button>
                  </form>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default ContactPage;
