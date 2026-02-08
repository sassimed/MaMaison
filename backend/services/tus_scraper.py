"""
TUS Product Scraper - Scrapes products from tus.com.tn (Tunisian United Solutions)
Products: Vidéosurveillance (Dahua), Contrôle d'accès (ZKTeco), Réseaux (Ruijie), Alarme, Smart Home
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

BASE_URL = "https://tus.com.tn"

# Main product categories to scrape
CATEGORIES = [
    # Vidéosurveillance
    {"url": "/product-category/videosurveillance/", "name": "Vidéosurveillance", "brand": "Dahua"},
    {"url": "/product-category/videosurveillance/cameras-ip/", "name": "Caméras IP", "brand": "Dahua"},
    {"url": "/product-category/videosurveillance/hdcvi/", "name": "HDCVI", "brand": "Dahua"},
    {"url": "/product-category/videosurveillance/ptz/", "name": "PTZ", "brand": "Dahua"},
    {"url": "/product-category/videosurveillance/cctv/", "name": "CCTV SCHUTZ", "brand": "SCHUTZ"},
    {"url": "/product-category/videosurveillance/accessoires/", "name": "Accessoires Vidéo", "brand": "Dahua"},
    
    # Contrôle d'accès
    {"url": "/product-category/controle-dacces/", "name": "Contrôle d'Accès", "brand": "ZKTeco"},
    {"url": "/product-category/controle-dacces/access-control/", "name": "Access Control", "brand": "ZKTeco"},
    
    # Réseaux
    {"url": "/product-category/reseaux/", "name": "Réseaux", "brand": "Ruijie"},
    {"url": "/product-category/reseaux/switches-ruijie/", "name": "Switches", "brand": "Ruijie"},
    {"url": "/product-category/reseaux/wireless-ruijie/", "name": "Wireless", "brand": "Ruijie"},
    {"url": "/product-category/reseaux/routers-ruijie/", "name": "Routers", "brand": "Ruijie"},
    {"url": "/product-category/reseaux/keystone-jack/", "name": "Keystone Jack", "brand": "Langbrug"},
    {"url": "/product-category/reseaux/armoire/", "name": "Armoire", "brand": "Langbrug"},
    
    # Alarme
    {"url": "/product-category/alarme/", "name": "Alarme", "brand": "SCHUTZ"},
    
    # Smart Home
    {"url": "/product-category/smart-home/", "name": "Smart Home", "brand": "SCHUTZ"},
    
    # Flat Panel
    {"url": "/product-category/flat-panel/", "name": "Flat Panel", "brand": "Swipe"},
    
    # New products
    {"url": "/product-category/new/", "name": "Nouveautés", "brand": "Mixed"},
]

# Category mapping for MyDar
CATEGORY_MAPPING = {
    "Vidéosurveillance": "Caméra",
    "Caméras IP": "Caméra",
    "HDCVI": "Caméra",
    "PTZ": "Caméra",
    "CCTV SCHUTZ": "Caméra",
    "Accessoires Vidéo": "Accessoire",
    "Contrôle d'Accès": "Contrôle d'Accès",
    "Access Control": "Contrôle d'Accès",
    "Réseaux": "Réseau",
    "Switches": "Switch",
    "Wireless": "WiFi",
    "Routers": "Routeur",
    "Keystone Jack": "Connectique",
    "Armoire": "Armoire",
    "Alarme": "Alarme",
    "Smart Home": "Domotique",
    "Flat Panel": "Écran",
    "Nouveautés": "Nouveauté",
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Fetch a page and return HTML content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        }
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30), ssl=False) as response:
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
    
    # Find all product items (WooCommerce structure)
    product_items = soup.select('.product, .products .product, li.product')
    
    for item in product_items:
        try:
            # Get product link
            link_elem = item.select_one('a.woocommerce-LoopProduct-link, a[href*="/produits/"]')
            if not link_elem:
                link_elem = item.select_one('h3 a, h2 a, .woocommerce-loop-product__title a')
            
            if not link_elem:
                continue
            
            product_url = link_elem.get('href', '')
            if not product_url or '/produits/' not in product_url:
                continue
            
            # Ensure full URL
            if not product_url.startswith('http'):
                product_url = BASE_URL + product_url
            
            # Get product name
            name_elem = item.select_one('.woocommerce-loop-product__title, h2.woocommerce-loop-product__title, h3, .product-title')
            name = name_elem.get_text(strip=True) if name_elem else ''
            
            if not name:
                # Try getting from title attribute or image alt
                title_elem = item.select_one('a[title], img[alt]')
                if title_elem:
                    name = title_elem.get('title') or title_elem.get('alt', '')
            
            if not name:
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
                if '-300x300' in image_url:
                    image_url = image_url.replace('-300x300', '')
                elif '-150x150' in image_url:
                    image_url = image_url.replace('-150x150', '')
                
                if image_url and not image_url.startswith('http'):
                    image_url = BASE_URL + image_url
            
            # Get short description if available
            desc_elem = item.select_one('.product-short-description, .woocommerce-product-details__short-description')
            short_desc = desc_elem.get_text(strip=True)[:300] if desc_elem else ''
            
            products.append({
                'name': name,
                'url': product_url,
                'image_url': image_url,
                'short_description': short_desc,
                'category': category_info['name'],
                'default_brand': category_info.get('brand', 'TUS'),
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
        desc_elem = soup.select_one('.woocommerce-product-details__short-description, .product-short-description, #tab-description')
        if desc_elem:
            # Clean up HTML tags and get text
            desc_text = desc_elem.get_text(separator=' ', strip=True)
            product['description'] = desc_text[:1500]
        
        # Get main image (high quality)
        main_img = soup.select_one('.woocommerce-product-gallery__image img, .wp-post-image')
        if main_img:
            large_img = (
                main_img.get('data-large_image') or
                main_img.get('data-src') or 
                main_img.get('src', '')
            )
            if large_img:
                # Remove size suffixes
                large_img = re.sub(r'-\d+x\d+\.', '.', large_img)
                if not large_img.startswith('http'):
                    large_img = BASE_URL + large_img
                product['image_url'] = large_img
        
        # Get gallery images
        gallery_images = []
        gallery = soup.select('.woocommerce-product-gallery__image img, .product-thumbnails img')
        for img in gallery:
            src = img.get('data-large_image') or img.get('data-src') or img.get('src', '')
            if src:
                src = re.sub(r'-\d+x\d+\.', '.', src)
                if not src.startswith('http'):
                    src = BASE_URL + src
                if src not in gallery_images:
                    gallery_images.append(src)
        
        if gallery_images:
            product['images'] = gallery_images
            if not product.get('image_url'):
                product['image_url'] = gallery_images[0]
        
        # Get SKU
        sku_elem = soup.select_one('.sku, .product_meta .sku')
        if sku_elem:
            product['sku'] = sku_elem.get_text(strip=True)
        
        # Get brand from tags
        brand_elem = soup.select_one('.tagged_as a, .product_meta a[href*="product-tag"]')
        if brand_elem:
            product['brand'] = brand_elem.get_text(strip=True)
        
        # Get specifications from table
        specs = {}
        spec_table = soup.select_one('.woocommerce-product-attributes, table.shop_attributes, .product-attributes')
        if spec_table:
            rows = spec_table.select('tr')
            for row in rows:
                label = row.select_one('th, .woocommerce-product-attributes-item__label')
                value = row.select_one('td, .woocommerce-product-attributes-item__value')
                if label and value:
                    key = label.get_text(strip=True)
                    val = value.get_text(strip=True)
                    if key and val:
                        specs[key] = val
        
        # Also get specs from description table
        desc_tables = soup.select('#tab-description table, .woocommerce-Tabs-panel--description table')
        for table in desc_tables:
            rows = table.select('tr')
            for row in rows:
                cells = row.select('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if key and val and key not in specs:
                        specs[key] = val
        
        if specs:
            product['specifications'] = specs
        
        # Look for YouTube video
        youtube_url = extract_youtube_url(html)
        if youtube_url:
            product['youtube_url'] = youtube_url
        
        # Get category breadcrumb for more accurate categorization
        breadcrumb = soup.select('.woocommerce-breadcrumb a, .breadcrumb a')
        if breadcrumb:
            # Get last category in breadcrumb (most specific)
            for crumb in reversed(breadcrumb):
                text = crumb.get_text(strip=True)
                if text and text not in ['Accueil', 'Produits', 'Home']:
                    product['sub_category'] = text
                    break
        
        # Get datasheet PDF link if available
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


def get_pagination_info(html: str) -> int:
    """Get total number of pages from pagination"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for page numbers
    pagination = soup.select('.woocommerce-pagination .page-numbers a, .pagination a')
    max_page = 1
    
    for link in pagination:
        text = link.get_text(strip=True)
        if text.isdigit():
            page = int(text)
            if page > max_page:
                max_page = page
    
    # Also check for "next" link page parameter
    next_link = soup.select_one('.woocommerce-pagination .next, .pagination .next')
    if next_link:
        href = next_link.get('href', '')
        page_match = re.search(r'/page/(\d+)', href)
        if page_match:
            next_page = int(page_match.group(1))
            if next_page > max_page:
                max_page = next_page - 1  # Current page is one less
    
    return max_page


async def scrape_category(session: aiohttp.ClientSession, category: Dict, with_details: bool = True) -> List[Dict]:
    """Scrape all products from a category"""
    all_products = []
    page = 1
    
    while True:
        if page == 1:
            url = f"{BASE_URL}{category['url']}"
        else:
            url = f"{BASE_URL}{category['url']}page/{page}/"
        
        logger.info(f"Scraping {category['name']} page {page}...")
        
        html = await fetch_page(session, url)
        if not html:
            break
        
        products = parse_product_list(html, category)
        if not products:
            break
        
        all_products.extend(products)
        
        # Check pagination
        total_pages = get_pagination_info(html)
        logger.info(f"Category {category['name']}: page {page}/{total_pages}")
        
        if page >= total_pages:
            break
        
        page += 1
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Fetch details for each product
    if with_details and all_products:
        logger.info(f"Fetching details for {len(all_products)} products in {category['name']}...")
        
        batch_size = 5
        detailed_products = []
        
        for i in range(0, len(all_products), batch_size):
            batch = all_products[i:i + batch_size]
            tasks = [fetch_product_details(session, p) for p in batch]
            results = await asyncio.gather(*tasks)
            detailed_products.extend(results)
            await asyncio.sleep(0.5)
        
        return detailed_products
    
    return all_products


async def scrape_all_products(categories: List[Dict] = None, with_details: bool = True) -> List[Dict]:
    """
    Scrape all products from TUS website
    
    Args:
        categories: List of categories to scrape (None = all)
        with_details: Whether to fetch detailed product info
    
    Returns:
        List of product dictionaries
    """
    if categories is None:
        categories = CATEGORIES
    
    all_products = []
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for category in categories:
            try:
                products = await scrape_category(session, category, with_details)
                all_products.extend(products)
                logger.info(f"Category {category['name']}: {len(products)} products")
                await asyncio.sleep(1)
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


def convert_to_mydar_product(tus_product: Dict, source: str = "tus", fournisseur: str = "TUS") -> Dict:
    """Convert TUS product to MyDar product format"""
    now = datetime.now(timezone.utc).isoformat()
    
    name = tus_product.get('name', '')
    
    # Build description
    description = tus_product.get('description', '') or tus_product.get('short_description', '')
    if not description:
        description = f"Produit {tus_product.get('category', '')} - {name}"
    
    # Map category
    category_name = tus_product.get('category', '')
    mydar_category = CATEGORY_MAPPING.get(category_name, category_name)
    
    # Determine brand
    brand = tus_product.get('brand') or tus_product.get('default_brand', 'TUS')
    
    # Get image
    image = tus_product.get('image_url', '')
    
    # Build product dict
    product = {
        'id': str(uuid.uuid4()),
        'name': name,
        'slug': re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
        'description': description[:1500],
        'category': mydar_category,
        'brand': brand,
        'price': None,  # TUS is B2B, no public prices
        'currency': 'TND',
        'image': image,
        'images': tus_product.get('images', [image] if image else []),
        'specifications': tus_product.get('specifications', {}),
        'sku': tus_product.get('sku', ''),
        'source': source,
        'source_url': tus_product.get('url', ''),
        'fournisseur': fournisseur,
        'sub_category': tus_product.get('sub_category', ''),
        'in_stock': True,
        'featured': False,
        'active': True,
        'created_at': now,
        'updated_at': now
    }
    
    # Add YouTube URL if present
    if tus_product.get('youtube_url'):
        product['youtube_url'] = tus_product['youtube_url']
    
    # Add datasheet URL if present
    if tus_product.get('datasheet_url'):
        product['datasheet_url'] = tus_product['datasheet_url']
    
    return product
