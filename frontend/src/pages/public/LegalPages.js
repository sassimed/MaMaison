import React from 'react';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';

const LegalPages = () => {
  const [activePage, setActivePage] = React.useState('mentions');

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <section className="bg-gradient-to-r from-purple-600 to-cyan-500 text-white py-16">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            {activePage === 'mentions' ? 'Mentions Légales' : 'Politique de Confidentialité'}
          </h1>
        </div>
      </section>

      <section className="py-12 bg-gray-50 flex-1">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
            {activePage === 'mentions' ? (
              <div>
                <h2 className="text-2xl font-bold mb-4 text-gray-900">Mentions Légales</h2>
                
                <div className="space-y-6 text-gray-700">
                  <div>
                    <h3 className="font-bold text-lg mb-2">1. Éditeur du site</h3>
                    <p>
                      SmartHome<br />
                      Société par actions simplifiée<br />
                      Siège social : Tunis, Tunisie<br />
                      RCS : XXX XXX XXX
                    </p>
                  </div>

                  <div>
                    <h3 className="font-bold text-lg mb-2">2. Directeur de publication</h3>
                    <p>Directeur : [Nom du directeur]</p>
                  </div>

                  <div>
                    <h3 className="font-bold text-lg mb-2">3. Hébergement</h3>
                    <p>
                      Le site est hébergé par Emergent.sh<br />
                      Contact : support@emergent.sh
                    </p>
                  </div>

                  <div>
                    <h3 className="font-bold text-lg mb-2">4. Propriété intellectuelle</h3>
                    <p>
                      L'ensemble du contenu de ce site (textes, images, vidéos) est la propriété de SmartHome 
                      ou fait l'objet d'une autorisation d'utilisation. Toute reproduction, même partielle, 
                      est interdite sans autorisation préalable.
                    </p>
                  </div>

                  <div>
                    <h3 className="font-bold text-lg mb-2">5. Contact</h3>
                    <p>
                      Email : contact@smarthome.tn<br />
                      Téléphone : +216 XX XXX XXX
                    </p>
                  </div>
                </div>

                <div className="mt-8">
                  <button
                    onClick={() => setActivePage('privacy')}
                    className="text-cyan-600 hover:text-blue-700 font-medium"
                  >
                    → Voir la Politique de Confidentialité
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <h2 className="text-2xl font-bold mb-4 text-gray-900">Politique de Confidentialité (RGPD)</h2>
                
                <div className="space-y-6 text-gray-700">
                  <div>
                    <h3 className="font-bold text-lg mb-2">1. Collecte des données personnelles</h3>
                    <p>
                      Dans le cadre de l'utilisation de notre site, nous pouvons être amenés à collecter 
                      les données personnelles suivantes :
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Nom et prénom</li>
                      <li>Adresse email</li>
                      <li>Numéro de téléphone</li>
                      <li>Adresse postale</li>
                      <li>Informations relatives à votre projet domotique</li>
                    </ul>
                  </div>

                  <div>
                    <h3 className="font-bold text-lg mb-2">2. Finalité de la collecte</h3>
                    <p>
                      Vos données personnelles sont collectées pour les finalités suivantes :
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Traitement de vos demandes de devis et rendez-vous</li>
                      <li>Gestion de la relation client</li>
                      <li>Envoi d'informations sur nos services (avec votre consentement)</li>
                      <li>Amélioration de nos services</li>
                    </ul>
                  </div>

                  <div>
                    <h3 className="font-bold text-lg mb-2">3. Durée de conservation</h3>
                    <p>
                      Vos données personnelles sont conservées pendant la durée nécessaire aux finalités 
                      pour lesquelles elles ont été collectées, conformément à la réglementation en vigueur.
                    </p>
                  </div>

                  <div>
                    <h3 className="font-bold text-lg mb-2">4. Vos droits</h3>
                    <p>
                      Conformément au RGPD, vous disposez des droits suivants :
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Droit d'accès à vos données</li>
                      <li>Droit de rectification</li>
                      <li>Droit à l'effacement</li>
                      <li>Droit à la limitation du traitement</li>
                      <li>Droit à la portabilité</li>
                      <li>Droit d'opposition</li>
                    </ul>
                    <p className="mt-2">
                      Pour exercer ces droits, contactez-nous à : contact@smarthome.tn
                    </p>
                  </div>

                  <div>
                    <h3 className="font-bold text-lg mb-2">5. Sécurité</h3>
                    <p>
                      Nous mettons en œuvre toutes les mesures techniques et organisationnelles appropriées 
                      afin de garantir la sécurité de vos données personnelles.
                    </p>
                  </div>

                  <div>
                    <h3 className="font-bold text-lg mb-2">6. Cookies</h3>
                    <p>
                      Notre site peut utiliser des cookies pour améliorer votre expérience de navigation. 
                      Vous pouvez paramétrer votre navigateur pour refuser les cookies.
                    </p>
                  </div>
                </div>

                <div className="mt-8">
                  <button
                    onClick={() => setActivePage('mentions')}
                    className="text-cyan-600 hover:text-blue-700 font-medium"
                  >
                    → Voir les Mentions Légales
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default LegalPages;
