import React from 'react';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { Link } from 'react-router-dom';
import { SEO } from '../../components/SEO';

const GalleryPage = () => {
  // Mock data - in real app would come from API
  const categories = ['Tous', 'Éclairage', 'Volets', 'Sécurité', 'Vidéosurveillance'];
  const [selectedCategory, setSelectedCategory] = React.useState('Tous');

  const galleryItems = [
    {
      id: 1,
      title: 'Installation vidéosurveillance villa',
      category: 'Vidéosurveillance',
      image: 'https://images.unsplash.com/photo-1656057497463-37e68d6ff329?w=600',
      location: 'Paris 16ème'
    },
    {
      id: 2,
      title: 'Éclairage intelligent salon',
      category: 'Éclairage',
      image: 'https://images.unsplash.com/photo-1513510879358-71a1ac7df6d9?w=600',
      location: 'Neuilly-sur-Seine'
    },
    {
      id: 3,
      title: 'Système de sécurité complet',
      category: 'Sécurité',
      image: 'https://images.unsplash.com/photo-1589935447067-5531094415d1?w=600',
      location: 'Versailles'
    },
    {
      id: 4,
      title: 'Automatisation volets roulants',
      category: 'Volets',
      image: 'https://images.unsplash.com/photo-1528255671579-01b9e182ed1d?w=600',
      location: 'Boulogne'
    },
    {
      id: 5,
      title: 'Caméras IP extérieures',
      category: 'Vidéosurveillance',
      image: 'https://images.unsplash.com/photo-1528312635006-8ea0bc49ec63?w=600',
      location: 'Saint-Cloud'
    },
    {
      id: 6,
      title: 'Éclairage connecté jardin',
      category: 'Éclairage',
      image: 'https://images.unsplash.com/photo-1652117007700-08527f93cbec?w=600',
      location: 'Suresnes'
    }
  ];

  const filteredItems = selectedCategory === 'Tous' 
    ? galleryItems 
    : galleryItems.filter(item => item.category === selectedCategory);

  return (
    <div className="min-h-screen flex flex-col">
      <SEO 
        title="Nos Réalisations - SmartHome Tunisie"
        description="Découvrez nos projets d'installation smart home en Tunisie : vidéosurveillance, éclairage intelligent, volets connectés, systèmes de sécurité. Portfolio de nos réalisations."
        keywords="réalisations domotique, portfolio smart home, installations domotiques tunisie, projets vidéosurveillance, éclairage connecté"
        url="/realisations"
      />
      <Header />

      <section className="bg-gradient-to-r from-purple-600 to-cyan-500 text-white py-16">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold mb-4" data-testid="gallery-title">
            Nos Réalisations
          </h1>
          <p className="text-xl text-purple-100">
            Découvrez nos projets d'installation smart home
          </p>
        </div>
      </section>

      {/* Filters */}
      <section className="bg-white border-b sticky top-16 z-40">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-wrap gap-3">
            {categories.map((category) => (
              <button
                key={category}
                data-testid={`filter-${category.toLowerCase()}`}
                onClick={() => setSelectedCategory(category)}
                className={`px-6 py-2 rounded-full font-medium transition-all ${
                  selectedCategory === category
                    ? 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Gallery Grid */}
      <section className="py-12 bg-gray-50 flex-1">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                data-testid={`gallery-item-${item.id}`}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow"
              >
                <div className="h-64 overflow-hidden">
                  <img
                    src={item.image}
                    alt={item.title}
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                  />
                </div>
                <div className="p-4">
                  <span className="inline-block px-3 py-1 bg-cyan-100 text-cyan-800 text-xs font-semibold rounded-full mb-2">
                    {item.category}
                  </span>
                  <h3 className="text-lg font-bold text-gray-900 mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-500">📍 {item.location}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6 text-gray-900">
            Envie de voir votre projet ici ?
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Contactez-nous pour discuter de votre installation domotique
          </p>
          <Link
            to="/rendez-vous"
            className="inline-block px-8 py-4 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-semibold text-lg hover:opacity-90 transition-colors"
          >
            Demander un devis
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default GalleryPage;
