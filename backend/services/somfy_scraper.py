"""
Somfy Product Scraper - Scrapes products from somfy.tn
Products: Motorisation volets, stores, portails, garage, domotique
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

BASE_URL = "https://www.somfy.tn"

# Categories to scrape
CATEGORIES = [
    {"url": "/produits/volets-roulants", "name": "Volets Roulants", "type": "Motorisation"},
    {"url": "/produits/stores-d-interieur", "name": "Stores d'Intérieur", "type": "Motorisation"},
    {"url": "/produits/rideaux", "name": "Rideaux", "type": "Motorisation"},
    {"url": "/produits/stores-de-terrasse", "name": "Stores de Terrasse", "type": "Motorisation"},
    {"url": "/produits/pergolas", "name": "Pergolas", "type": "Motorisation"},
    {"url": "/produits/portails", "name": "Portails", "type": "Motorisation"},
    {"url": "/produits/portes-de-garage", "name": "Portes de Garage", "type": "Motorisation"},
    {"url": "/produits/alarmes-et-cameras", "name": "Alarmes et Caméras", "type": "Sécurité"},
    {"url": "/produits/eclairage", "name": "Éclairage", "type": "Domotique"},
    {"url": "/produits/chauffage", "name": "Chauffage", "type": "Domotique"},
    {"url": "/produits/visiophones", "name": "Visiophones", "type": "Communication"},
    {"url": "/produits", "name": "Tous Produits", "type": "Général"},  # Main listing
]

# Category mapping for MyDar
CATEGORY_MAPPING = {
    "Volets Roulants": "Volet",
    "Stores d'Intérieur": "Store",
    "Rideaux": "Rideau",
    "Stores de Terrasse": "Store",
    "Pergolas": "Pergola",
    "Portails": "Portail",
    "Portes de Garage": "Garage",
    "Alarmes et Caméras": "Alarme",
    "Éclairage": "Éclairage",
    "Chauffage": "Chauffage",
    "Visiophones": "Vidéophone",
    "Tous Produits": "Motorisation",
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Fetch a page and return HTML content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        }
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30), allow_redirects=True) as response:
            if response.status == 200:
                return await response.text()
            else:
                logger.warning(f"Failed to fetch {url}: {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def parse_product_list(html: str, category_info: Dict) -> List[Dict]:
    """Parse product list from category page HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    
    # Find product items - Somfy uses specific structure
    product_items = soup.select('.product-list-item, .plp-product-card, li.plp-product')
    
    # If no items found, try alternative selectors
    if not product_items:
        product_items = soup.select('a[href*="/produits/"][href*="/"]')
    
    seen_urls = set()
    
    for item in product_items:
        try:
            # Get product link
            if item.name == 'a':
                link_elem = item
            else:
                link_elem = item.select_one('a[href*="/produits/"]')
            
            if not link_elem:
                continue
            
            product_url = link_elem.get('href', '')
            if not product_url or '/produits/' not in product_url:
                continue
            
            # Skip category pages (they don't have product ID pattern)
            if not re.search(r'/produits/\d+/', product_url):
                continue
            
            # Ensure full URL
            if not product_url.startswith('http'):
                product_url = BASE_URL + product_url
            
            # Skip duplicates
            if product_url in seen_urls:
                continue
            seen_urls.add(product_url)
            
            # Get product name
            name_elem = item.select_one('.product-name, .plp-product-name, h3, h2, span')
            name = ''
            if name_elem:
                name = name_elem.get_text(strip=True)
            
            if not name:
                # Try to get from link text
                name = link_elem.get_text(strip=True)
            
            if not name or len(name) < 3:
                continue
            
            # Get image
            img_elem = item.select_one('img')
            image_url = ''
            if img_elem:
                image_url = (
                    img_elem.get('data-src') or 
                    img_elem.get('src', '')
                )
                # Get larger image
                if image_url:
                    image_url = re.sub(r'/\d+x\d+/', '/1200x1200/', image_url)
                    if not image_url.startswith('http'):
                        image_url = BASE_URL + image_url
            
            products.append({
                'name': name,
                'url': product_url,
                'image_url': image_url,
                'category': category_info['name'],
                'product_type': category_info.get('type', 'Général'),
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
        # Get product name (more accurate from detail page)
        title_elem = soup.select_one('h1, .product-title, .pdp-title')
        if title_elem:
            product['name'] = title_elem.get_text(strip=True)
        
        # Get description from meta or page content
        desc_elem = soup.select_one('meta[name="description"]')
        if desc_elem:
            product['description'] = desc_elem.get('content', '')[:500]
        
        # Get fuller description from page
        full_desc = soup.select_one('.product-description, .pdp-description, .description-content')
        if full_desc:
            product['description'] = full_desc.get_text(separator=' ', strip=True)[:1000]
        
        # Get main image (high quality)
        img_patterns = [
            'img[src*="library"]',
            '.product-image img',
            '.pdp-image img',
            'picture img'
        ]
        
        for pattern in img_patterns:
            main_img = soup.select_one(pattern)
            if main_img:
                large_img = main_img.get('data-src') or main_img.get('src', '')
                if large_img and 'library' in large_img:
                    # Get largest version
                    large_img = re.sub(r'/\d+x\d+/', '/1200x1200/', large_img)
                    if not large_img.startswith('http'):
                        large_img = BASE_URL + large_img
                    product['image_url'] = large_img
                    break
        
        # Get gallery images
        gallery_images = []
        gallery = soup.select('img[src*="library"]')
        for img in gallery:
            src = img.get('data-src') or img.get('src', '')
            if src and 'library' in src:
                src = re.sub(r'/\d+x\d+/', '/1200x1200/', src)
                if not src.startswith('http'):
                    src = BASE_URL + src
                if src not in gallery_images:
                    gallery_images.append(src)
        
        if gallery_images:
            product['images'] = gallery_images[:5]  # Limit to 5 images
            if not product.get('image_url'):
                product['image_url'] = gallery_images[0]
        
        # Get SKU from URL
        sku_match = re.search(r'/produits/(\d+)/', product['url'])
        if sku_match:
            product['sku'] = sku_match.group(1)
        
        # Get technology type (RTS, IO, WT)
        tech_patterns = ['RTS', 'IO', 'WT', 'io-homecontrol']
        page_text = soup.get_text()
        for tech in tech_patterns:
            if tech.upper() in page_text.upper():
                product['technology'] = tech.upper()
                break
        
        # Get features/specifications
        specs = {}
        
        # Look for spec lists
        spec_items = soup.select('.product-specs li, .pdp-features li, .features-list li')
        for item in spec_items:
            text = item.get_text(strip=True)
            if ':' in text:
                parts = text.split(':', 1)
                specs[parts[0].strip()] = parts[1].strip()
            elif text:
                specs[f"Feature_{len(specs)+1}"] = text
        
        if specs:
            product['specifications'] = specs
        
        # Look for YouTube video
        youtube_match = re.search(r'youtube\.com/embed/([a-zA-Z0-9_-]+)', html)
        if youtube_match:
            product['youtube_url'] = f"https://www.youtube.com/watch?v={youtube_match.group(1)}"
        
        # Get PDF documentation
        pdf_links = soup.select('a[href$=".pdf"]')
        for link in pdf_links:
            href = link.get('href', '')
            if href:
                if not href.startswith('http'):
                    href = BASE_URL + href
                product['datasheet_url'] = href
                break
        
    except Exception as e:
        logger.error(f"Error fetching details for {product['url']}: {e}")
    
    return product


def get_total_products(html: str) -> int:
    """Get total number of products from page"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for "X produit(s) trouvé"
    result_elem = soup.select_one('#productnbResults, .product-count, .results-count')
    if result_elem:
        text = result_elem.get_text(strip=True)
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
    
    return 0


async def scrape_all_products(with_details: bool = True) -> List[Dict]:
    """
    Scrape all products from Somfy website using sitemap
    
    Args:
        with_details: Whether to fetch detailed product info
    
    Returns:
        List of product dictionaries
    """
    all_products = []
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        # First, get product URLs from sitemap
        sitemap_url = f"{BASE_URL}/sitemap.xml"
        logger.info(f"Fetching product URLs from sitemap: {sitemap_url}")
        
        sitemap_html = await fetch_page(session, sitemap_url)
        if not sitemap_html:
            logger.error("Failed to fetch sitemap")
            return []
        
        # Extract all product URLs from sitemap
        import re
        product_urls = re.findall(r'https://www\.somfy\.tn/fr-ac/produits/(\d+)/([a-z0-9-]+)', sitemap_html)
        unique_products = list(set(product_urls))
        
        logger.info(f"Found {len(unique_products)} unique products in sitemap")
        
        # Create product list with URLs
        for sku, slug in unique_products:
            product_url = f"{BASE_URL}/produits/{sku}/{slug}"
            all_products.append({
                'url': product_url,
                'sku': sku,
                'name': slug.replace('-', ' ').title(),
                'category': 'Tous Produits',
                'product_type': 'Motorisation',
            })
        
        # Fetch details for each product
        if with_details and all_products:
            logger.info(f"Fetching details for {len(all_products)} products...")
            
            batch_size = 5
            detailed_products = []
            
            for i in range(0, len(all_products), batch_size):
                batch = all_products[i:i + batch_size]
                tasks = [fetch_product_details(session, p) for p in batch]
                results = await asyncio.gather(*tasks)
                detailed_products.extend(results)
                logger.info(f"Fetched details: {i + len(batch)}/{len(all_products)}")
                await asyncio.sleep(0.5)
            
            all_products = detailed_products
    
    logger.info(f"Total unique products scraped: {len(all_products)}")
    return all_products


def convert_to_mydar_product(somfy_product: Dict, source: str = "somfy", fournisseur: str = "Somfy") -> Dict:
    """Convert Somfy product to MyDar product format"""
    now = datetime.now(timezone.utc).isoformat()
    
    name = somfy_product.get('name', '')
    
    # Build description
    description = somfy_product.get('description', '')
    if not description:
        description = f"Produit Somfy - {name}. Leader mondial de la motorisation pour volets, stores et portails."
    
    # Map category
    category_name = somfy_product.get('category', 'Motorisation')
    mydar_category = CATEGORY_MAPPING.get(category_name, 'Motorisation')
    
    # Get image
    image = somfy_product.get('image_url', '')
    
    # Build product dict
    product = {
        'id': str(uuid.uuid4()),
        'name': name,
        'slug': re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
        'description': description[:1500],
        'category': mydar_category,
        'brand': 'Somfy',
        'price': None,  # Somfy doesn't display prices online
        'currency': 'TND',
        'image': image,
        'images': somfy_product.get('images', [image] if image else []),
        'specifications': somfy_product.get('specifications', {}),
        'sku': somfy_product.get('sku', ''),
        'source': source,
        'source_url': somfy_product.get('url', ''),
        'fournisseur': fournisseur,
        'technology': somfy_product.get('technology', ''),  # RTS, IO, WT
        'product_type': somfy_product.get('product_type', 'Motorisation'),
        'in_stock': True,
        'featured': False,
        'active': True,
        'created_at': now,
        'updated_at': now
    }
    
    # Add YouTube URL if present
    if somfy_product.get('youtube_url'):
        product['youtube_url'] = somfy_product['youtube_url']
    
    # Add datasheet URL if present
    if somfy_product.get('datasheet_url'):
        product['datasheet_url'] = somfy_product['datasheet_url']
    
    return product
