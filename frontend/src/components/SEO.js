import React from 'react';
import { Helmet } from 'react-helmet-async';

/**
 * SEO Component - Gère les meta tags pour le SEO
 * Permet aux moteurs de recherche et ChatGPT de voir le contenu
 */
export function SEO({ 
  title = 'SmartHome - Maison Intelligente & Installateurs Professionnels | Tunisie',
  description = 'SmartHome : Achetez vos équipements de maison connectée et trouvez des installateurs qualifiés en Tunisie. Éclairage, sécurité, domotique - tout pour votre smart home.',
  keywords = 'smart home tunisie, maison connectée, domotique, installateur électricien, éclairage connecté, vidéosurveillance, alarme',
  image = '/smarthome-logo.png',
  url = '',
  type = 'website',
  noindex = false
}) {
  const siteUrl = process.env.REACT_APP_SITE_URL || 'https://smartshop-ai-19.preview.emergentagent.com';
  const fullUrl = url ? `${siteUrl}${url}` : siteUrl;
  const fullImage = image.startsWith('http') ? image : `${siteUrl}${image}`;

  return (
    <Helmet>
      {/* Titre */}
      <title>{title}</title>
      
      {/* Meta tags de base */}
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <meta name="author" content="SmartHome Tunisie" />
      <meta name="robots" content={noindex ? 'noindex, nofollow' : 'index, follow'} />
      
      {/* Canonical URL */}
      <link rel="canonical" href={fullUrl} />
      
      {/* Open Graph / Facebook */}
      <meta property="og:type" content={type} />
      <meta property="og:url" content={fullUrl} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={fullImage} />
      <meta property="og:locale" content="fr_TN" />
      <meta property="og:site_name" content="SmartHome" />
      
      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:url" content={fullUrl} />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={fullImage} />
      
      {/* Structured Data - Organization */}
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "Organization",
          "name": "SmartHome",
          "url": siteUrl,
          "logo": `${siteUrl}/smarthome-logo.png`,
          "description": "Votre partenaire pour la maison connectée en Tunisie - Équipements et installateurs professionnels",
          "address": {
            "@type": "PostalAddress",
            "addressCountry": "TN"
          },
          "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer service"
          }
        })}
      </script>
    </Helmet>
  );
}

/**
 * SEO pour les pages produits
 */
export function ProductSEO({ product }) {
  if (!product) return null;
  
  const title = `${product.name} - SmartHome`;
  const description = product.description?.substring(0, 160) || `Découvrez ${product.name} chez SmartHome. Équipement smart home de qualité.`;
  const price = product.price ? `${product.price.toFixed(3)} DT` : 'Prix sur demande';
  
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta property="og:type" content="product" />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      {product.image_url && <meta property="og:image" content={product.image_url} />}
      <meta property="product:price:amount" content={product.price || ''} />
      <meta property="product:price:currency" content="TND" />
      
      {/* Structured Data - Product */}
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "Product",
          "name": product.name,
          "description": description,
          "image": product.image_url,
          "brand": {
            "@type": "Brand",
            "name": product.brand || "SmartHome"
          },
          "category": product.category,
          "offers": {
            "@type": "Offer",
            "price": product.price,
            "priceCurrency": "TND",
            "availability": "https://schema.org/InStock"
          },
          ...(product.average_rating && {
            "aggregateRating": {
              "@type": "AggregateRating",
              "ratingValue": product.average_rating,
              "reviewCount": product.review_count || 0
            }
          })
        })}
      </script>
    </Helmet>
  );
}

/**
 * SEO pour les pages de service
 */
export function ServiceSEO({ service }) {
  if (!service) return null;
  
  const title = `${service.name} - SmartHome`;
  const description = service.description?.substring(0, 160) || `Service ${service.name} par SmartHome. Installation professionnelle en Tunisie.`;
  
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta property="og:type" content="service" />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      
      {/* Structured Data - Service */}
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "Service",
          "name": service.name,
          "description": description,
          "provider": {
            "@type": "Organization",
            "name": "SmartHome"
          },
          "areaServed": {
            "@type": "Country",
            "name": "Tunisia"
          }
        })}
      </script>
    </Helmet>
  );
}

export default SEO;
