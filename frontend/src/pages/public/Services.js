import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import api from '../../services/api';
import { SEO } from '../../components/SEO';

const ServicesPage = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await api.get('/services');
        setServices(response.data);
      } catch (error) {
        console.error('Error fetching services:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchServices();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-600"></div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <SEO 
        title="Services Domotiques - SmartHome Tunisie"
        description="Découvrez nos services de domotique : vidéophone, vidéosurveillance, alarme, éclairage connecté, volets roulants, thermostat intelligent. Installation professionnelle en Tunisie."
        keywords="services domotique, installation domotique tunisie, vidéophone, vidéosurveillance, alarme connectée, éclairage intelligent"
        url="/services"
      />
      <Header />
      
      <section className="bg-gradient-to-r from-purple-600 to-cyan-500 text-white py-16">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold mb-4" data-testid="services-title">
            Nos Services Domotiques
          </h1>
          <p className="text-xl text-white/90">
            Des solutions complètes pour votre confort et votre sécurité
          </p>
        </div>
      </section>

      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((service) => (
              <div 
                key={service.id} 
                className="bg-white rounded-xl shadow-lg p-6 hover:shadow-2xl transition-all transform hover:-translate-y-2"
                data-testid={`service-${service.slug}`}
              >
                <div className="text-6xl mb-4">{service.icon}</div>
                <h3 className="text-2xl font-bold mb-3 text-gray-900">{service.name}</h3>
                <p className="text-gray-600 mb-4">{service.description}</p>
                
                {service.advantages && service.advantages.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Avantages clés :</h4>
                    <ul className="space-y-1">
                      {service.advantages.slice(0, 3).map((adv, i) => (
                        <li key={i} className="flex items-start text-sm text-gray-700">
                          <span className="text-cyan-600 mr-2">✔</span>
                          <span>{adv}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <Link
                  to="/rendez-vous"
                  className="inline-block px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-semibold hover:opacity-90 transition-all mt-4"
                >
                  En savoir plus
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-cyan-500 bg-clip-text text-transparent">
            Besoin de conseils personnalisés ?
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Nos experts sont à votre écoute pour vous accompagner dans votre projet
          </p>
          <Link
            to="/contact"
            className="inline-block px-8 py-4 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-semibold text-lg hover:opacity-90 transition-all shadow-lg"
          >
            Nous Contacter
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default ServicesPage;
