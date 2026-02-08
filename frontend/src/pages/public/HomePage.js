import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { SEO } from '../../components/SEO';
import { 
  ShoppingBag, 
  Users, 
  Wifi, 
  Shield, 
  Lightbulb, 
  ThermometerSun,
  Camera,
  Lock,
  Zap,
  CheckCircle,
  ArrowRight,
  Star,
  Home,
  Wrench
} from 'lucide-react';

const HomePage = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const handleFindInstaller = () => {
    if (isAuthenticated()) {
      navigate('/dashboard/my-annonces?action=create');
    } else {
      navigate('/login?redirect=/dashboard/my-annonces?action=create');
    }
  };

  const productCategories = [
    { icon: <Lightbulb className="w-8 h-8" />, name: 'Éclairage Connecté', count: '50+ produits' },
    { icon: <Camera className="w-8 h-8" />, name: 'Vidéosurveillance', count: '30+ produits' },
    { icon: <Shield className="w-8 h-8" />, name: 'Sécurité', count: '40+ produits' },
    { icon: <ThermometerSun className="w-8 h-8" />, name: 'Climatisation', count: '20+ produits' },
    { icon: <Lock className="w-8 h-8" />, name: 'Serrures Connectées', count: '15+ produits' },
    { icon: <Wifi className="w-8 h-8" />, name: 'Capteurs & Détecteurs', count: '35+ produits' },
  ];

  const installerServices = [
    { icon: <Zap className="w-6 h-6" />, title: 'Électricité', desc: 'Installation électrique, tableaux, câblage' },
    { icon: <Wifi className="w-6 h-6" />, title: 'Domotique', desc: 'Configuration et installation smart home' },
    { icon: <Camera className="w-6 h-6" />, title: 'Vidéosurveillance', desc: 'Caméras, DVR, NVR, systèmes IP' },
    { icon: <Shield className="w-6 h-6" />, title: 'Alarmes', desc: 'Systèmes d\'alarme et détection' },
  ];

  const benefits = [
    { icon: <CheckCircle className="w-5 h-5" />, text: 'Produits certifiés et garantis' },
    { icon: <CheckCircle className="w-5 h-5" />, text: 'Installateurs professionnels vérifiés' },
    { icon: <CheckCircle className="w-5 h-5" />, text: 'Support technique disponible' },
    { icon: <CheckCircle className="w-5 h-5" />, text: 'Livraison partout en Tunisie' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <SEO 
        title="SmartHome - Maison Intelligente & Installateurs Professionnels | Tunisie"
        description="SmartHome : Achetez vos équipements de maison connectée et trouvez des installateurs qualifiés en Tunisie. Éclairage, sécurité, domotique - tout pour votre smart home."
        keywords="smart home tunisie, maison connectée, domotique, installateur électricien, éclairage connecté, vidéosurveillance, alarme"
        url="/"
      />
      <Header />

      {/* Hero Section - Clear Value Proposition */}
      <section className="relative bg-gradient-to-br from-purple-600 via-purple-700 to-cyan-600 text-white overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }} />
        </div>

        <div className="container mx-auto px-4 py-16 md:py-24 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-sm mb-6">
              <Wifi className="w-4 h-4" />
              <span>Votre plateforme Smart Home en Tunisie</span>
            </div>

            {/* Main Heading */}
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
              Votre maison intelligente,<br />
              <span className="text-cyan-300">de l'achat à l'installation.</span>
            </h1>

            {/* Subheading - Clear Value Prop */}
            <p className="text-xl md:text-2xl text-purple-100 mb-8 max-w-2xl mx-auto">
              Achetez vos équipements smart et faites-les installer par des professionnels vérifiés, partout en Tunisie.
            </p>

            {/* Two Main CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Link
                to="/catalog"
                className="group inline-flex items-center justify-center gap-3 px-8 py-4 bg-white text-purple-700 rounded-xl font-semibold text-lg hover:bg-gray-100 transition-all shadow-xl hover:shadow-2xl"
                data-testid="hero-shop-btn"
              >
                <ShoppingBag className="w-6 h-6" />
                Acheter des produits
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <button
                onClick={handleFindInstaller}
                className="group inline-flex items-center justify-center gap-3 px-8 py-4 bg-transparent border-2 border-white text-white rounded-xl font-semibold text-lg hover:bg-white/10 transition-all"
                data-testid="hero-installers-btn"
              >
                <Users className="w-6 h-6" />
                Trouver un installateur
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>

            {/* Trust Badges */}
            <div className="flex flex-wrap justify-center gap-6 text-sm text-purple-200">
              {benefits.map((benefit, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-cyan-300">{benefit.icon}</span>
                  <span>{benefit.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Wave Bottom */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 50L48 45.7C96 41.3 192 32.7 288 30.8C384 29 480 34 576 41.5C672 49 768 59 864 59.5C960 60 1056 51 1152 46.2C1248 41.3 1344 40.7 1392 40.3L1440 40V100H1392C1344 100 1248 100 1152 100C1056 100 960 100 864 100C768 100 672 100 576 100C480 100 384 100 288 100C192 100 96 100 48 100H0V50Z" fill="white"/>
          </svg>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Comment ça marche ?
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Deux façons simples de transformer votre maison en smart home
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* Option 1: Buy Products */}
            <div className="bg-gradient-to-br from-purple-50 to-cyan-50 rounded-2xl p-8 border border-purple-100">
              <div className="w-14 h-14 bg-gradient-to-br from-purple-600 to-cyan-500 rounded-xl flex items-center justify-center text-white mb-6">
                <ShoppingBag className="w-7 h-7" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Achetez vos produits
              </h3>
              <p className="text-gray-600 mb-6">
                Parcourez notre catalogue de produits smart home sélectionnés pour leur qualité et compatibilité.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3 text-gray-700">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>Produits certifiés et garantis</span>
                </li>
                <li className="flex items-center gap-3 text-gray-700">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>Guides d'installation inclus</span>
                </li>
                <li className="flex items-center gap-3 text-gray-700">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>Livraison partout en Tunisie</span>
                </li>
              </ul>
              <Link
                to="/catalog"
                className="inline-flex items-center gap-2 text-purple-600 font-semibold hover:text-purple-700"
              >
                Voir la boutique <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Option 2: Find Installer */}
            <div className="bg-gradient-to-br from-cyan-50 to-purple-50 rounded-2xl p-8 border border-cyan-100">
              <div className="w-14 h-14 bg-gradient-to-br from-cyan-500 to-purple-600 rounded-xl flex items-center justify-center text-white mb-6">
                <Users className="w-7 h-7" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Trouvez un installateur
              </h3>
              <p className="text-gray-600 mb-6">
                Publiez votre projet et recevez des devis de professionnels qualifiés près de chez vous.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3 text-gray-700">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>Installateurs vérifiés</span>
                </li>
                <li className="flex items-center gap-3 text-gray-700">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>Devis gratuits et sans engagement</span>
                </li>
                <li className="flex items-center gap-3 text-gray-700">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>Avis clients vérifiés</span>
                </li>
              </ul>
              <Link
                to="/annonces"
                className="inline-flex items-center gap-2 text-cyan-600 font-semibold hover:text-cyan-700"
              >
                Publier une demande <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Product Categories */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <span className="inline-block px-4 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium mb-4">
              Notre Catalogue
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Tout pour votre maison connectée
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Des produits sélectionnés pour leur qualité, compatibilité et facilité d'installation
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {productCategories.map((cat, i) => (
              <Link
                key={i}
                to={`/catalog?category=${encodeURIComponent(cat.name)}`}
                className="group bg-white rounded-xl p-6 text-center border border-gray-100 hover:border-purple-200 hover:shadow-lg transition-all"
              >
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-purple-100 to-cyan-100 rounded-xl flex items-center justify-center text-purple-600 group-hover:scale-110 transition-transform">
                  {cat.icon}
                </div>
                <h3 className="font-semibold text-gray-900 mb-1 text-sm">{cat.name}</h3>
                <p className="text-xs text-gray-500">{cat.count}</p>
              </Link>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link
              to="/catalog"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
            >
              Voir tous les produits <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Installer Services */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="inline-block px-4 py-1 bg-cyan-100 text-cyan-700 rounded-full text-sm font-medium mb-4">
                Réseau d'Installateurs
              </span>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Des professionnels qualifiés pour vos installations
              </h2>
              <p className="text-gray-600 mb-8">
                Trouvez des électriciens et installateurs smart home certifiés. 
                Publiez votre projet et comparez les devis en toute transparence.
              </p>

              <div className="grid sm:grid-cols-2 gap-4 mb-8">
                {installerServices.map((service, i) => (
                  <div key={i} className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl">
                    <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-purple-600 rounded-lg flex items-center justify-center text-white flex-shrink-0">
                      {service.icon}
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">{service.title}</h4>
                      <p className="text-sm text-gray-500">{service.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <Link
                to="/annonces"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
              >
                Trouver un installateur <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="relative">
              <div className="bg-gradient-to-br from-purple-100 to-cyan-100 rounded-2xl p-8">
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-cyan-500 rounded-full flex items-center justify-center text-white">
                      <Wrench className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="font-semibold">Installation Domotique</h4>
                      <p className="text-sm text-gray-500">Tunis, Ariana, Ben Arous</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Réponses reçues</span>
                      <span className="font-semibold text-purple-600">5 professionnels</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Meilleure offre</span>
                      <span className="font-semibold text-green-600">À partir de 150 DT</span>
                    </div>
                    <div className="flex items-center gap-1">
                      {[1,2,3,4,5].map(i => (
                        <Star key={i} className="w-4 h-4 text-yellow-400 fill-current" />
                      ))}
                      <span className="text-sm text-gray-500 ml-2">4.8 (120 avis)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-16 bg-gradient-to-br from-purple-600 to-cyan-600 text-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Pourquoi MyDar ?
            </h2>
            <p className="text-purple-100 max-w-2xl mx-auto">
              Votre partenaire de confiance pour une maison connectée, de A à Z
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* Pourquoi acheter ici */}
            <div className="bg-white/10 backdrop-blur rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <ShoppingBag className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold">Pourquoi acheter chez nous ?</h3>
              </div>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-cyan-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Produits sélectionnés</span>
                    <p className="text-sm text-purple-100">Uniquement des marques fiables : Tuya, Sonoff, Aqara, Shelly...</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-cyan-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Prix transparents en Dinar</span>
                    <p className="text-sm text-purple-100">Pas de mauvaises surprises, TVA incluse</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-cyan-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Garantie & SAV local</span>
                    <p className="text-sm text-purple-100">Support technique en Tunisie, pas à l'étranger</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-cyan-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Livraison rapide</span>
                    <p className="text-sm text-purple-100">Partout en Tunisie sous 24-72h</p>
                  </div>
                </li>
              </ul>
            </div>

            {/* Pourquoi trouver un installateur ici */}
            <div className="bg-white/10 backdrop-blur rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <Users className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold">Pourquoi trouver un pro ici ?</h3>
              </div>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-cyan-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Installateurs vérifiés</span>
                    <p className="text-sm text-purple-100">Profils validés, avis clients authentiques</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-cyan-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Devis gratuits</span>
                    <p className="text-sm text-purple-100">Comparez plusieurs offres sans engagement</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-cyan-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Proximité garantie</span>
                    <p className="text-sm text-purple-100">Des professionnels près de chez vous, dans toute la Tunisie</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-cyan-300 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Spécialistes domotique</span>
                    <p className="text-sm text-purple-100">Des experts formés aux dernières technologies smart home</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12 text-center max-w-4xl mx-auto border border-gray-100">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Prêt à rendre votre maison plus intelligente ?
            </h2>
            <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
              Commencez dès maintenant - parcourez nos produits ou publiez votre projet pour recevoir des devis.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/catalog"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
              >
                <ShoppingBag className="w-5 h-5" />
                Voir la Boutique
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-purple-600 text-purple-600 rounded-xl font-semibold hover:bg-purple-50 transition-all"
              >
                Créer un compte gratuit
              </Link>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default HomePage;
