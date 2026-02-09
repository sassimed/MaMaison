from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from datetime import datetime, timezone
import os
from utils.dependencies import get_db

router = APIRouter(tags=["SEO"])

SITE_URL = os.environ.get("SITE_URL", "https://metricshub-7.preview.emergentagent.com")

@router.get("/sitemap.xml", response_class=PlainTextResponse)
async def get_sitemap():
    """
    Génère le sitemap XML pour les moteurs de recherche
    """
    database = get_db()
    
    # Pages statiques
    static_pages = [
        {"url": "/", "priority": "1.0", "changefreq": "weekly"},
        {"url": "/services", "priority": "0.9", "changefreq": "monthly"},
        {"url": "/catalog", "priority": "0.9", "changefreq": "daily"},
        {"url": "/realisations", "priority": "0.8", "changefreq": "monthly"},
        {"url": "/rendez-vous", "priority": "0.8", "changefreq": "monthly"},
        {"url": "/contact", "priority": "0.7", "changefreq": "monthly"},
        {"url": "/annonces", "priority": "0.8", "changefreq": "daily"},
    ]
    
    # Récupérer tous les produits
    products = await database.products.find(
        {"is_active": {"$ne": False}}, 
        {"id": 1, "updated_at": 1}
    ).to_list(1000)
    
    # Générer le XML
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Pages statiques
    for page in static_pages:
        xml_content += f'''  <url>
    <loc>{SITE_URL}{page["url"]}</loc>
    <lastmod>{now}</lastmod>
    <changefreq>{page["changefreq"]}</changefreq>
    <priority>{page["priority"]}</priority>
  </url>\n'''
    
    # Pages produits
    for product in products:
        updated = product.get("updated_at", datetime.now(timezone.utc))
        if isinstance(updated, datetime):
            lastmod = updated.strftime("%Y-%m-%d")
        else:
            lastmod = now
        xml_content += f'''  <url>
    <loc>{SITE_URL}/catalog/{product["id"]}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>\n'''
    
    xml_content += '</urlset>'
    
    return Response(
        content=xml_content,
        media_type="application/xml"
    )


@router.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots():
    """
    Génère le fichier robots.txt
    """
    robots_content = f"""# Smart Life - Robots.txt
User-agent: *
Allow: /
Allow: /catalog
Allow: /services
Allow: /realisations
Allow: /contact
Allow: /rendez-vous
Allow: /annonces

# Disallow private/admin pages
Disallow: /dashboard
Disallow: /admin
Disallow: /login
Disallow: /register
Disallow: /api/

# Sitemap
Sitemap: {SITE_URL}/api/sitemap.xml
"""
    return PlainTextResponse(content=robots_content)


@router.get("/seo/page-content/{page_path:path}")
async def get_page_content(page_path: str):
    """
    Retourne le contenu textuel d'une page pour les crawlers sans JS
    Utile pour ChatGPT et autres AI qui ne peuvent pas exécuter JavaScript
    """
    database = get_db()
    
    content = {
        "url": f"{SITE_URL}/{page_path}",
        "title": "",
        "description": "",
        "content": "",
        "links": []
    }
    
    if page_path == "" or page_path == "/":
        content["title"] = "Smart Life - Expert Domotique & Sécurité Connectée en Tunisie"
        content["description"] = "Smart Life, votre expert en domotique et sécurité connectée en Tunisie. Solutions professionnelles pour votre maison intelligente."
        content["content"] = """
Smart Life - Votre Expert en Domotique

Services proposés:
- Vidéophone et interphone connecté
- Vidéosurveillance et caméras IP
- Systèmes d'alarme intelligents
- Éclairage connecté (LED, ampoules WiFi)
- Volets roulants automatisés
- Thermostat intelligent
- Serrures connectées
- Détecteurs et capteurs

Pourquoi choisir Smart Life?
- Expertise professionnelle
- Installation certifiée
- Service après-vente réactif
- Produits de qualité
- Conseils personnalisés
        """
        content["links"] = [
            {"text": "Nos Services", "url": "/services"},
            {"text": "Boutique", "url": "/catalog"},
            {"text": "Nos Réalisations", "url": "/realisations"},
            {"text": "Contact", "url": "/contact"},
        ]
    
    elif page_path == "catalog" or page_path.startswith("catalog"):
        if "/" in page_path and page_path != "catalog":
            # Page produit spécifique
            product_id = page_path.split("/")[-1]
            product = await database.products.find_one({"id": product_id}, {"_id": 0})
            if product:
                content["title"] = f"{product['name']} - Smart Life"
                content["description"] = product.get("description", "")[:160]
                content["content"] = f"""
Produit: {product['name']}
Catégorie: {product.get('category', 'N/A')}
Marque: {product.get('brand', 'N/A')}
Technologie: {product.get('technology', 'N/A')}
Prix: {product.get('price', 'Sur demande')} DT

Description:
{product.get('description', '')}

Usage recommandé:
{product.get('usage', 'N/A')}
                """
        else:
            # Page catalogue
            content["title"] = "Boutique Domotique - Smart Life"
            content["description"] = "Découvrez notre catalogue de produits domotiques"
            
            products = await database.products.find(
                {"is_active": {"$ne": False}},
                {"_id": 0, "id": 1, "name": 1, "category": 1, "price": 1}
            ).to_list(100)
            
            products_text = "\n".join([
                f"- {p['name']} ({p.get('category', 'N/A')}) - {p.get('price', 'Prix sur demande')} DT"
                for p in products
            ])
            
            content["content"] = f"""
Boutique Smart Life - Produits Domotiques

Nos produits:
{products_text}
            """
    
    elif page_path == "services":
        services = await database.services.find({}, {"_id": 0, "name": 1, "description": 1}).to_list(20)
        
        services_text = "\n".join([
            f"- {s['name']}: {s.get('description', '')[:100]}"
            for s in services
        ])
        
        content["title"] = "Services Domotiques - Smart Life"
        content["description"] = "Découvrez nos services d'installation domotique professionnelle"
        content["content"] = f"""
Services Smart Life

{services_text if services else '''
- Installation vidéophone et interphone
- Vidéosurveillance et caméras de sécurité
- Systèmes d'alarme connectés
- Éclairage intelligent
- Volets roulants automatisés
- Thermostat connecté
'''}
        """
    
    elif page_path == "contact":
        content["title"] = "Contact - Smart Life"
        content["description"] = "Contactez Smart Life pour vos projets domotiques"
        content["content"] = """
Contactez Smart Life

Nous sommes disponibles pour répondre à toutes vos questions concernant:
- Devis gratuit
- Conseil personnalisé
- Installation domotique
- Service après-vente

Formulaire de contact disponible sur le site.
        """
    
    return content
