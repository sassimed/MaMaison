"""
SOMEF Product Scraper - Scrapes products from somef.tn
Extracts products with images and YouTube video links
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

BASE_URL = "https://www.somef.tn"

# All product categories to scrape
CATEGORIES = [
    # Système 43
    {"url": "/fr/267-plaques-murales", "name": "Plaques Murales", "system": "Système 43"},
    {"url": "/fr/268-prises", "name": "Prises", "system": "Système 43"},
    {"url": "/fr/269-interrupteurs", "name": "Interrupteurs", "system": "Système 43"},
    {"url": "/fr/272-gamme-etanche", "name": "Gamme Étanche", "system": "Système 43"},
    {"url": "/fr/270-boites-", "name": "Boîtes", "system": "Système 43"},
    {"url": "/fr/271-montures", "name": "Montures", "system": "Système 43"},
    
    # Système 44
    {"url": "/fr/315-smart-44", "name": "Smart 44", "system": "Système 44"},
    {"url": "/fr/312-plaques-serie-new-style-england-style", "name": "Plaques New Style", "system": "Système 44"},
    {"url": "/fr/313-appareillages-serie-new-style-england-style", "name": "Appareillages New Style", "system": "Système 44"},
    {"url": "/fr/310-plaques-serie-touch", "name": "Plaques Touch", "system": "Système 44"},
    {"url": "/fr/311-appareillages-serie-touch", "name": "Appareillages Touch", "system": "Système 44"},
    {"url": "/fr/308-plaques-serie-civili", "name": "Plaques Civili", "system": "Système 44"},
    {"url": "/fr/309-appareillages-serie-civili", "name": "Appareillages Civili", "system": "Système 44"},
    {"url": "/fr/145-boites-", "name": "Boîtes", "system": "Système 44"},
    {"url": "/fr/39-montures-", "name": "Montures", "system": "Système 44"},
    
    # Système 45
    {"url": "/fr/282-plaques-murales", "name": "Plaques Murales", "system": "Système 45"},
    {"url": "/fr/281-prises", "name": "Prises", "system": "Système 45"},
    {"url": "/fr/280-interrupteurs", "name": "Interrupteurs", "system": "Système 45"},
    {"url": "/fr/314-plaques-pour-profile-en-aluminium", "name": "Plaques Profilé Alu", "system": "Système 45"},
    {"url": "/fr/307-boites-d-encastrement-", "name": "Boîtes Encastrement", "system": "Système 45"},
    {"url": "/fr/141-boites-apparentes", "name": "Boîtes Apparentes", "system": "Système 45"},
    {"url": "/fr/142-boites-etanches-apparentes", "name": "Boîtes Étanches", "system": "Système 45"},
    {"url": "/fr/279-montures", "name": "Montures", "system": "Système 45"},
    
    # Gamme antibactérienne
    {"url": "/fr/286-interrupteurs-", "name": "Interrupteurs Antibactériens", "system": "Antibactérien"},
    {"url": "/fr/287-prises", "name": "Prises Antibactériennes", "system": "Antibactérien"},
    {"url": "/fr/285-plaques-murales-", "name": "Plaques Antibactériennes", "system": "Antibactérien"},
    
    # Interphone et Vidéophone
    {"url": "/fr/295-interphonie", "name": "Interphonie", "system": "Communication"},
    {"url": "/fr/213-visiosomef", "name": "VisioSOMEF", "system": "Communication"},
    {"url": "/fr/256-akuvox", "name": "AKUVOX", "system": "Communication"},
    
    # Maison Connectée
    {"url": "/fr/49-interrupteur-programmables-et-intelligents", "name": "Interrupteurs Programmables", "system": "Domotique"},
    {"url": "/fr/72-chronothermostat-et-thermostats", "name": "Thermostats", "system": "Domotique"},
    {"url": "/fr/54-centralisation-filaire", "name": "Centralisation Filaire", "system": "Domotique"},
    {"url": "/fr/64-centralisation-bus", "name": "Centralisation Bus", "system": "Domotique"},
    {"url": "/fr/294-domotique-wi-fi", "name": "Domotique Wi-Fi", "system": "Domotique"},
    
    # Coffrets et Disjoncteurs
    {"url": "/fr/223-systemes-modulaires-sur-rail-din", "name": "Systèmes Modulaires", "system": "Distribution"},
    {"url": "/fr/227-coffret", "name": "Coffrets", "system": "Distribution"},
    
    # Autres
    {"url": "/fr/217-detecteur-de-mouvement", "name": "Détecteurs de Mouvement", "system": "Capteurs"},
    {"url": "/fr/297-gestion-hoteliere-", "name": "Gestion Hôtelière", "system": "Professionnel"},
    {"url": "/fr/298-appel-infirmier-", "name": "Appel Infirmier", "system": "Médical"},
    {"url": "/fr/302-gamme-bureautique", "name": "Bureautique", "system": "Professionnel"},
    {"url": "/fr/7-coffrets", "name": "Coffrets Pro", "system": "Professionnel"},
]

# Category to MyDar category mapping
CATEGORY_MAPPING = {
    "Interrupteurs": "Interrupteur",
    "Prises": "Prise",
    "Plaques Murales": "Plaque",
    "Boîtes": "Boîte",
    "Montures": "Monture",
    "Gamme Étanche": "Étanche",
    "Thermostats": "Thermostat",
    "Détecteurs de Mouvement": "Détecteur",
    "Domotique Wi-Fi": "Domotique",
    "Interphonie": "Interphone",
    "VisioSOMEF": "Vidéophone",
    "AKUVOX": "Vidéophone",
    "Coffrets": "Coffret",
    "Coffrets Pro": "Coffret",
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Fetch a page and return HTML content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        }
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.text()
            else:
                logger.warning(f"Failed to fetch {url}: {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def extract_youtube_url(html: str) -> Optional[str]:
    """Extract YouTube video URL from page HTML"""
    # Look for YouTube embed URLs
    youtube_patterns = [
        r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'youtu\.be/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, html)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    
    return None


def parse_product_list(html: str, category_info: Dict) -> List[Dict]:
    """Parse product list from category page HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    
    # Find all product items
    product_items = soup.select('.product-miniature, .product-container, article.product-miniature')
    
    for item in product_items:
        try:
            # Get product link
            link_elem = item.select_one('a.thumbnail.product-thumbnail, a[href*=".html"]')
            if not link_elem:
                link_elem = item.select_one('h2 a, .product-title a')
            
            if not link_elem:
                continue
            
            product_url = link_elem.get('href', '')
            if not product_url:
                continue
            
            # Ensure full URL
            if not product_url.startswith('http'):
                product_url = BASE_URL + product_url
            
            # Get product name
            name_elem = item.select_one('h2.product-title a, .product-title a, h2 a')
            name = name_elem.get_text(strip=True) if name_elem else ''
            
            if not name:
                # Try getting from image alt
                img = item.select_one('img')
                if img:
                    name = img.get('alt', '') or img.get('title', '')
            
            if not name:
                continue
            
            # Get image
            img_elem = item.select_one('img.product-thumbnail-first, img[data-full-size-image-url], img')
            image_url = ''
            if img_elem:
                # Prefer larger image
                image_url = (
                    img_elem.get('data-full-size-image-url') or 
                    img_elem.get('data-src') or 
                    img_elem.get('src', '')
                )
                # Convert to large image URL
                if image_url:
                    image_url = image_url.replace('-home_default/', '-large_default/')
                    image_url = image_url.replace('-small_default/', '-large_default/')
                    if not image_url.startswith('http'):
                        image_url = BASE_URL + image_url
            
            products.append({
                'name': name,
                'url': product_url,
                'image_url': image_url,
                'category': category_info['name'],
                'system': category_info.get('system', ''),
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
        # Get reference/SKU
        ref_elem = soup.select_one('.product-reference span, [itemprop="sku"]')
        if ref_elem:
            product['sku'] = ref_elem.get_text(strip=True).replace('REF°', '').strip()
        
        # Get short description
        short_desc = soup.select_one('.product-description, #product-description-short')
        if short_desc:
            product['short_description'] = short_desc.get_text(strip=True)[:500]
        
        # Get full description
        full_desc = soup.select_one('#description .product-description, .tab-content #description')
        if full_desc:
            product['description'] = full_desc.get_text(separator=' ', strip=True)[:1000]
        
        # Get main image (high quality)
        main_img = soup.select_one('.product-cover img, .js-qv-product-cover img')
        if main_img:
            large_img = main_img.get('data-image-large-src') or main_img.get('src', '')
            if large_img:
                if not large_img.startswith('http'):
                    large_img = BASE_URL + large_img
                product['image_url'] = large_img
        
        # Get gallery images
        gallery_images = []
        gallery = soup.select('.product-images .thumb-container img, .images-container .thumb img')
        for img in gallery:
            src = img.get('data-image-large-src') or img.get('src', '')
            if src:
                if not src.startswith('http'):
                    src = BASE_URL + src
                # Get large version
                src = src.replace('-home_default/', '-large_default/')
                src = src.replace('-small_default/', '-large_default/')
                src = src.replace('-medium_default/', '-large_default/')
                if src not in gallery_images:
                    gallery_images.append(src)
        
        if gallery_images:
            product['images'] = gallery_images
            if not product.get('image_url'):
                product['image_url'] = gallery_images[0]
        
        # Look for YouTube video
        youtube_url = extract_youtube_url(html)
        if youtube_url:
            product['youtube_url'] = youtube_url
        
        # Get specifications from additional info
        specs = {}
        spec_table = soup.select_one('.product-features, #product-details .data-sheet')
        if spec_table:
            rows = spec_table.select('li, tr, dl')
            for row in rows:
                label = row.select_one('.name, dt, th')
                value = row.select_one('.value, dd, td')
                if label and value:
                    key = label.get_text(strip=True)
                    val = value.get_text(strip=True)
                    if key and val:
                        specs[key] = val
        
        if specs:
            product['specifications'] = specs
        
        # Get attachments/documentation
        attachments = []
        attach_links = soup.select('a[href*="attachment"], a[href$=".pdf"]')
        for link in attach_links:
            href = link.get('href', '')
            if href and '.pdf' in href.lower():
                if not href.startswith('http'):
                    href = BASE_URL + href
                attachments.append({
                    'name': link.get_text(strip=True) or 'Documentation',
                    'url': href
                })
        
        if attachments:
            product['attachments'] = attachments
        
    except Exception as e:
        logger.error(f"Error fetching details for {product['url']}: {e}")
    
    return product


def get_total_pages(html: str) -> int:
    """Get total number of pages from pagination"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for "Affichage X-Y de Z article(s)"
    result_text = soup.select_one('.showing, .total-products')
    if result_text:
        match = re.search(r'de\s+(\d+)\s+article', result_text.get_text())
        if match:
            total = int(match.group(1))
            return (total // 12) + (1 if total % 12 > 0 else 0)
    
    # Look for pagination
    pagination = soup.select('.pagination .page-item a, .pagination li a')
    max_page = 1
    for link in pagination:
        href = link.get('href', '')
        page_match = re.search(r'page=(\d+)', href)
        if page_match:
            page = int(page_match.group(1))
            if page > max_page:
                max_page = page
    
    return max_page


async def scrape_category(session: aiohttp.ClientSession, category: Dict, with_details: bool = True) -> List[Dict]:
    """Scrape all products from a category"""
    all_products = []
    page = 1
    
    while True:
        url = f"{BASE_URL}{category['url']}?page={page}"
        logger.info(f"Scraping {category['name']} page {page}...")
        
        html = await fetch_page(session, url)
        if not html:
            break
        
        products = parse_product_list(html, category)
        if not products:
            break
        
        all_products.extend(products)
        
        # Check if there are more pages
        if page == 1:
            total_pages = get_total_pages(html)
            logger.info(f"Category {category['name']}: {total_pages} pages")
        
        if page >= get_total_pages(html):
            break
        
        page += 1
        await asyncio.sleep(0.3)  # Rate limiting
    
    # Fetch details for each product
    if with_details and all_products:
        logger.info(f"Fetching details for {len(all_products)} products in {category['name']}...")
        
        # Process in batches to avoid overwhelming the server
        batch_size = 5
        detailed_products = []
        
        for i in range(0, len(all_products), batch_size):
            batch = all_products[i:i + batch_size]
            tasks = [fetch_product_details(session, p) for p in batch]
            results = await asyncio.gather(*tasks)
            detailed_products.extend(results)
            await asyncio.sleep(0.5)  # Rate limiting between batches
        
        return detailed_products
    
    return all_products


async def scrape_all_products(categories: List[Dict] = None, with_details: bool = True) -> List[Dict]:
    """
    Scrape all products from SOMEF website
    
    Args:
        categories: List of categories to scrape (None = all)
        with_details: Whether to fetch detailed product info
    
    Returns:
        List of product dictionaries
    """
    if categories is None:
        categories = CATEGORIES
    
    all_products = []
    
    async with aiohttp.ClientSession() as session:
        for category in categories:
            try:
                products = await scrape_category(session, category, with_details)
                all_products.extend(products)
                logger.info(f"Category {category['name']}: {len(products)} products")
                await asyncio.sleep(1)  # Rate limiting between categories
            except Exception as e:
                logger.error(f"Error scraping category {category['name']}: {e}")
                continue
    
    # Remove duplicates by URL
    seen_urls = set()
    unique_products = []
    for p in all_products:
        if p['url'] not in seen_urls:
            seen_urls.add(p['url'])
            unique_products.append(p)
    
    logger.info(f"Total unique products scraped: {len(unique_products)}")
    return unique_products


def convert_to_mydar_product(somef_product: Dict, source: str = "somef", fournisseur: str = "SOMEF") -> Dict:
    """Convert SOMEF product to MyDar product format"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Clean up name
    name = somef_product.get('name', '')
    
    # Build description
    description = somef_product.get('description', '') or somef_product.get('short_description', '')
    if not description:
        description = f"Produit {somef_product.get('category', 'électrique')} SOMEF de qualité professionnelle."
    
    # Map category
    category_name = somef_product.get('category', 'Électrique')
    mydar_category = CATEGORY_MAPPING.get(category_name, category_name)
    
    # Get image
    image = somef_product.get('image_url', '')
    
    # Build product dict
    product = {
        'id': str(uuid.uuid4()),
        'name': name,
        'slug': re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
        'description': description[:1000],
        'category': mydar_category,
        'brand': 'SOMEF',
        'price': None,  # SOMEF doesn't display prices online
        'currency': 'TND',
        'image': image,
        'images': somef_product.get('images', [image] if image else []),
        'specifications': somef_product.get('specifications', {}),
        'sku': somef_product.get('sku', ''),
        'source': source,
        'source_url': somef_product.get('url', ''),
        'fournisseur': fournisseur,
        'system': somef_product.get('system', ''),  # Système 43, 44, 45, etc.
        'in_stock': True,
        'featured': False,
        'active': True,
        'created_at': now,
        'updated_at': now
    }
    
    # Add YouTube URL if present
    if somef_product.get('youtube_url'):
        product['youtube_url'] = somef_product['youtube_url']
    
    # Add attachments if present
    if somef_product.get('attachments'):
        product['attachments'] = somef_product['attachments']
    
    return product
