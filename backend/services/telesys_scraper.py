"""
Telesys Product Scraper - Scrapes products from telesys.com.tn
Creates an API to import products into MyDar database
"""
import asyncio
import aiohttp
import re
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

BASE_URL = "https://telesys.com.tn"
PRODUCTS_URL = f"{BASE_URL}/produits-telesys/page/"

# Category mapping from Telesys to MyDar
CATEGORY_MAPPING = {
    "alarme-filaire": "Alarme Filaire",
    "alarme-radio-sans-fil": "Alarme Sans Fil",
    "alarme-mixte": "Alarme Mixte",
    "detection-interieur": "Détecteur Intérieur",
    "detection-exterieur": "Détecteur Extérieur",
    "transmission-telephonique": "Transmission",
    "sirene-antivol": "Sirène",
    "camera-de-surveillance-sans-fil": "Caméra Sans Fil",
    "camera-de-surveillance-hd": "Caméra HD",
    "camera-de-surveillance-ip": "Caméra IP",
    "controle-dacces": "Contrôle d'Accès",
    "detection-incendie-et-gaz": "Détection Incendie",
    "interphone-et-videophonie": "Interphone",
    "equipements-de-sonorisation": "Sonorisation",
    "gestion-de-leclairage": "Éclairage Connecté",
    "gestion-de-la-temperature": "Thermostat",
    "gestion-des-ouvrants": "Volets & Stores",
    "portails-automatiques": "Portail Automatique",
    "cables-electriques-speciaux": "Câblage",
    "eclairage-interieur": "Éclairage Intérieur",
    "eclairage-exterieur": "Éclairage Extérieur",
    "reseaux-wifi": "Réseau WiFi",
    "switches-administrables": "Switch Réseau",
    "switches-non-administrables": "Switch Réseau",
    "accessoires-reseau": "Accessoires Réseau",
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Fetch a page and return HTML content"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.text()
            else:
                logger.warning(f"Failed to fetch {url}: {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def parse_product_list(html: str) -> List[Dict]:
    """Parse product list from HTML and extract basic info"""
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    
    # Find all product items (Telesys uses div.product-grid-item)
    product_items = soup.select('div.product-grid-item, div.wd-product, li.product')
    
    for item in product_items:
        try:
            # Get product link
            link_elem = item.select_one('a.product-image-link, a[href*="/produit/"]')
            if not link_elem:
                link_elem = item.select_one('.product-element-top a, .wd-product-element a')
            if not link_elem:
                link_elem = item.select_one('h3 a, .wd-entities-title a')
            
            if not link_elem:
                continue
            
            product_url = link_elem.get('href', '')
            if not product_url or '/produit/' not in product_url:
                continue
            
            # Get product name
            name_elem = item.select_one('.wd-entities-title, h3.product-title, .woocommerce-loop-product__title')
            name = name_elem.get_text(strip=True) if name_elem else ''
            
            if not name:
                # Try getting from link title
                name = link_elem.get('title', '') or link_elem.get_text(strip=True)
            
            # Get image
            img_elem = item.select_one('img.attachment-woocommerce_thumbnail, img.wp-post-image, .product-image-link img')
            image_url = ''
            if img_elem:
                # Prefer larger image
                image_url = img_elem.get('data-large_image', '') or img_elem.get('data-src', '') or img_elem.get('src', '')
                # Get full size image (remove -WxH suffix)
                if image_url:
                    image_url = re.sub(r'-\d+x\d+\.', '.', image_url)
            
            # Get category from class
            item_classes = ' '.join(item.get('class', []))
            category = 'Domotique'
            
            # Extract category from class like "product_cat-alarme-filaire"
            cat_match = re.search(r'product_cat-([a-z0-9-]+)', item_classes)
            if cat_match:
                cat_slug = cat_match.group(1)
                # Map to friendly name
                for key, value in CATEGORY_MAPPING.items():
                    if key in cat_slug:
                        category = value
                        break
                else:
                    # Clean up the slug if no mapping found
                    category = cat_slug.replace('-', ' ').title()
            
            products.append({
                'name': name,
                'url': product_url,
                'image_url': image_url,
                'category': category,
                'source_category': cat_slug if cat_match else ''
            })
            
        except Exception as e:
            logger.error(f"Error parsing product item: {e}")
            continue
    
    return products


async def fetch_product_details(session: aiohttp.ClientSession, product: Dict) -> Dict:
    """Fetch detailed product information from product page"""
    html = await fetch_page(session, product['url'])
    if not html:
        return product
    
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        # Get full description
        desc_elem = soup.select_one('.woocommerce-product-details__short-description, .product-short-description')
        if desc_elem:
            product['short_description'] = desc_elem.get_text(strip=True)
        
        # Get long description from tab
        long_desc = soup.select_one('#tab-description .woocommerce-Tabs-panel, #tab-description')
        if long_desc:
            # Get text but remove "Description TELESYS" section
            desc_text = long_desc.get_text(separator=' ', strip=True)
            # Cut at "TELESYS, Tunisie Electro" if present
            if "TELESYS, Tunisie Electro" in desc_text:
                desc_text = desc_text.split("TELESYS, Tunisie Electro")[0]
            product['description'] = desc_text[:2000].strip()
        
        # Get technical specifications from additional info table
        specs_table = soup.select_one('#tab-additional_information table, .woocommerce-product-attributes')
        if specs_table:
            specs = {}
            rows = specs_table.select('tr')
            for row in rows:
                th = row.select_one('th, .woocommerce-product-attributes-item__label')
                td = row.select_one('td, .woocommerce-product-attributes-item__value')
                if th and td:
                    key = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    if key and value:
                        specs[key] = value
            product['specifications'] = specs
        
        # Get SKU/UGS
        sku_elem = soup.select_one('.sku, .sku_wrapper .sku')
        if sku_elem:
            product['sku'] = sku_elem.get_text(strip=True)
        
        # Get brand from product meta
        brand_elem = soup.select_one('.posted_in + span, .product_meta .tagged_as')
        if not brand_elem:
            # Try to find "Marque : XXX" pattern
            meta_text = soup.select_one('.product_meta')
            if meta_text:
                meta_str = meta_text.get_text()
                brand_match = re.search(r'Marque\s*:\s*(\w+)', meta_str)
                if brand_match:
                    product['brand'] = brand_match.group(1)
        
        # Get all images (gallery)
        gallery_images = []
        
        # Main product image
        main_img = soup.select_one('.woocommerce-product-gallery__image img, .product-image img')
        if main_img:
            src = main_img.get('data-large_image') or main_img.get('src', '')
            if src:
                gallery_images.append(src)
        
        # Gallery thumbnails
        gallery = soup.select('.woocommerce-product-gallery__image img, .flex-control-thumbs img')
        for img in gallery:
            src = img.get('data-large_image') or img.get('src', '') or img.get('data-src', '')
            if src and src not in gallery_images:
                # Get full size image
                src = re.sub(r'-\d+x\d+\.', '.', src)
                if src not in gallery_images:
                    gallery_images.append(src)
        
        if gallery_images:
            product['images'] = gallery_images
            product['image_url'] = gallery_images[0]
        
        # Get price if available
        price_elem = soup.select_one('.price .woocommerce-Price-amount bdi, .price ins .amount, .price .amount')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r'[\d\s,\.]+', price_text)
            if price_match:
                try:
                    price_str = price_match.group().replace(' ', '').replace(',', '.')
                    product['price'] = float(price_str)
                except:
                    pass
        
        # Extract brand from title if not found
        if not product.get('brand'):
            brand_patterns = ['INIM', 'AVS', 'EATON', 'COOPER', 'HIKVISION', 'DAHUA', 'AJAX', 'PARADOX', 'LEGRAND', 'SCHNEIDER', 'ABB', 'HAGER', 'UBIQUITI', 'TP-LINK', 'CISCO', 'COMELIT', 'FERMAX', 'AIPHONE', 'SOMFY', 'NICE', 'FAAC', 'BFT', 'CAME']
            for brand in brand_patterns:
                if brand.lower() in product.get('name', '').lower():
                    product['brand'] = brand
                    break
        
    except Exception as e:
        logger.error(f"Error fetching details for {product['url']}: {e}")
    
    return product


async def scrape_all_products(max_pages: int = None, with_details: bool = False) -> List[Dict]:
    """
    Scrape all products from Telesys website
    
    Args:
        max_pages: Maximum number of pages to scrape (None = all pages)
        with_details: Whether to fetch detailed product info (slower)
    
    Returns:
        List of product dictionaries
    """
    all_products = []
    
    async with aiohttp.ClientSession() as session:
        page = 1
        total_pages = None
        
        while True:
            if max_pages and page > max_pages:
                break
            
            url = f"{PRODUCTS_URL}{page}/"
            logger.info(f"Scraping page {page}...")
            
            html = await fetch_page(session, url)
            if not html:
                break
            
            # Get total pages from pagination on first page
            if total_pages is None:
                soup = BeautifulSoup(html, 'html.parser')
                # Find total count "Affichage de 1–12 sur 737 résultats"
                result_count = soup.select_one('.woocommerce-result-count')
                if result_count:
                    match = re.search(r'sur\s+(\d+)\s+résultats', result_count.get_text())
                    if match:
                        total = int(match.group(1))
                        total_pages = (total // 12) + 1
                        logger.info(f"Total products: {total}, Total pages: {total_pages}")
            
            products = parse_product_list(html)
            if not products:
                logger.info(f"No more products found on page {page}")
                break
            
            # Fetch details for each product if requested
            if with_details:
                logger.info(f"Fetching details for {len(products)} products...")
                tasks = [fetch_product_details(session, p) for p in products]
                products = await asyncio.gather(*tasks)
            
            all_products.extend(products)
            logger.info(f"Page {page}: Found {len(products)} products. Total: {len(all_products)}")
            
            page += 1
            
            # Rate limiting
            await asyncio.sleep(0.5)
            
            if total_pages and page > total_pages:
                break
    
    return all_products


def convert_to_mydar_product(telesys_product: Dict, source: str = "telesys", fournisseur: str = "Telesys") -> Dict:
    """Convert Telesys product to MyDar product format"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Clean up name
    name = telesys_product.get('name', '')
    # Remove brand suffix like "/ AVS" or "/ INIM"
    name = re.sub(r'\s*/\s*\w+$', '', name).strip()
    
    # Build description
    description = telesys_product.get('description', '') or telesys_product.get('short_description', '')
    if not description:
        description = f"Produit {telesys_product.get('category', 'domotique')} de qualité professionnelle."
    
    # Get main image - prefer high quality
    image = telesys_product.get('image_url', '')
    if image:
        # Remove size suffix to get full image
        image = re.sub(r'-\d+x\d+\.', '.', image)
    
    return {
        'id': str(uuid.uuid4()),
        'name': name,
        'slug': re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
        'description': description[:1000],  # Limit description
        'category': telesys_product.get('category', 'Domotique'),
        'brand': telesys_product.get('brand', 'TELESYS'),
        'price': telesys_product.get('price'),
        'currency': 'TND',
        'image': image,
        'images': telesys_product.get('images', [image] if image else []),
        'specifications': telesys_product.get('specifications', {}),
        'sku': telesys_product.get('sku', ''),
        'source': source,
        'source_url': telesys_product.get('url', ''),
        'fournisseur': fournisseur,  # Supplier field - hidden from users
        'in_stock': True,
        'featured': False,
        'active': True,
        'created_at': now,
        'updated_at': now
    }
