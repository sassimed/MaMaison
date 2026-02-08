"""
Unified Product Scraper - Scrapes all product data from 4 sites:
- tus.com.tn
- telesys.com.tn
- somfy.tn
- somef.tn

Extracts: All product info, all images, YouTube videos, specifications
Outputs: JSON file with all data + downloaded images
"""
import asyncio
import aiohttp
import os
import re
import json
import hashlib
import uuid
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Output directories
OUTPUT_DIR = Path("/app/scraped_data")
IMAGES_DIR = OUTPUT_DIR / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Site configurations
SITES = {
    "tus": {
        "base_url": "https://tus.com.tn",
        "name": "TUS - Tunisian United Solutions",
        "categories": [
            "/product-category/videosurveillance/",
            "/product-category/controle-dacces/",
            "/product-category/reseaux/",
            "/product-category/alarme/",
            "/product-category/smart-home/",
            "/product-category/flat-panel/",
        ]
    },
    "telesys": {
        "base_url": "https://telesys.com.tn",
        "name": "Telesys",
        "categories": [
            "/alarmes-tunisie/",
            "/cameras-surveillance/",
            "/controle-acces-tunisie/",
            "/detection-incendie-tunisie/",
            "/interphonie-tunisie/",
            "/domotique-tunisie/",
            "/eclairage-tunisie/",
            "/reseaux-informatiques/",
        ]
    },
    "somfy": {
        "base_url": "https://www.somfy.tn",
        "name": "Somfy Tunisie",
        "categories": [
            "/produits/volets-roulants",
            "/produits/stores-d-interieur",
            "/produits/portails",
            "/produits/portes-de-garage",
            "/produits/alarmes-et-cameras",
            "/produits/eclairage",
            "/produits",
        ]
    },
    "somef": {
        "base_url": "https://www.somef.tn",
        "name": "SOMEF",
        "categories": [
            "/fr/267-plaques-murales",
            "/fr/268-prises",
            "/fr/269-interrupteurs",
            "/fr/295-interphonie",
            "/fr/213-visiosomef",
            "/fr/294-domotique-wi-fi",
            "/fr/227-coffret",
        ]
    }
}

stats = {
    "total_products": 0,
    "total_images": 0,
    "total_videos": 0,
    "by_site": {}
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch page HTML with retry"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
    }
    
    for attempt in range(3):
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 404:
                    return None
        except Exception as e:
            if attempt == 2:
                logger.error(f"Failed to fetch {url}: {e}")
    return None


async def download_image(session: aiohttp.ClientSession, url: str, site: str, product_id: str) -> dict:
    """Download image and return local path"""
    if not url or url.startswith('data:'):
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/*',
        }
        
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                return None
            
            content = await response.read()
            if len(content) < 500:  # Skip tiny/placeholder images
                return None
            
            # Determine extension
            ext = Path(urlparse(url).path).suffix.lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                content_type = response.headers.get('Content-Type', '')
                if 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'
            
            # Generate filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{site}_{product_id}_{url_hash}{ext}"
            filepath = IMAGES_DIR / filename
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            stats["total_images"] += 1
            
            return {
                "original_url": url,
                "local_path": str(filepath),
                "filename": filename,
                "size": len(content)
            }
    except Exception as e:
        logger.debug(f"Failed to download image {url}: {e}")
        return None


def extract_youtube_urls(html: str) -> list:
    """Extract all YouTube video URLs from HTML"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'data-video-id=["\']([a-zA-Z0-9_-]{11})["\']',
    ]
    
    video_ids = set()
    for pattern in youtube_patterns:
        matches = re.findall(pattern, html)
        video_ids.update(matches)
    
    videos = []
    for vid in video_ids:
        videos.append({
            "video_id": vid,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "embed_url": f"https://www.youtube.com/embed/{vid}",
            "thumbnail": f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"
        })
    
    if videos:
        stats["total_videos"] += len(videos)
    
    return videos


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\[email[^\]]*\]', '', text)
    return text.strip()


# ============= TUS SCRAPER =============
def parse_tus_product(html: str, url: str) -> dict:
    """Parse TUS product page"""
    soup = BeautifulSoup(html, 'html.parser')
    product = {"source": "tus", "source_url": url}
    
    # Name
    title = soup.select_one('h1.product_title, h1.entry-title')
    product["name"] = clean_text(title.get_text()) if title else ""
    
    # SKU
    sku = soup.select_one('.sku')
    product["sku"] = clean_text(sku.get_text()) if sku else ""
    
    # Price
    price = soup.select_one('.price .amount, .woocommerce-Price-amount')
    if price:
        price_text = price.get_text()
        price_match = re.search(r'[\d\s,\.]+', price_text)
        if price_match:
            product["price"] = price_match.group().replace(' ', '').replace(',', '.')
    
    # Description
    desc = soup.select_one('.woocommerce-product-details__short-description')
    product["short_description"] = clean_text(desc.get_text()) if desc else ""
    
    full_desc = soup.select_one('#tab-description')
    product["full_description"] = clean_text(full_desc.get_text()) if full_desc else ""
    
    # Meta description
    meta = soup.select_one('meta[name="description"]')
    product["meta_description"] = meta.get('content', '') if meta else ""
    
    # Category
    breadcrumb = soup.select('.woocommerce-breadcrumb a')
    product["categories"] = [clean_text(b.get_text()) for b in breadcrumb[1:]] if breadcrumb else []
    
    # Brand
    brand = soup.select_one('.tagged_as a, .brand a, .product_meta a[href*="marque"]')
    product["brand"] = clean_text(brand.get_text()) if brand else ""
    
    # Images
    product["images"] = []
    
    # Main image from og:image
    og_img = soup.select_one('meta[property="og:image"]')
    if og_img:
        product["images"].append(og_img.get('content', ''))
    
    # Gallery images
    gallery = soup.select('.woocommerce-product-gallery__image a, .woocommerce-product-gallery__image img')
    for img in gallery:
        img_url = img.get('href') or img.get('data-large_image') or img.get('data-src') or img.get('src', '')
        if img_url and 'wp-content/uploads' in img_url and img_url not in product["images"]:
            product["images"].append(img_url)
    
    # Specifications table
    product["specifications"] = []
    spec_table = soup.select_one('#tab-description table')
    if spec_table:
        current_section = None
        current_specs = []
        
        for row in spec_table.select('tr'):
            cells = row.select('td')
            if len(cells) == 1:
                if current_section and current_specs:
                    product["specifications"].append({"name": current_section, "specs": current_specs})
                current_section = clean_text(cells[0].get_text())
                current_specs = []
            elif len(cells) >= 2:
                key = clean_text(cells[0].get_text())
                value = clean_text(cells[-1].get_text())
                if key and value and key != value:
                    current_specs.append({"key": key, "value": value})
        
        if current_section and current_specs:
            product["specifications"].append({"name": current_section, "specs": current_specs})
    
    # Additional attributes
    product["attributes"] = {}
    attr_table = soup.select_one('.woocommerce-product-attributes')
    if attr_table:
        for row in attr_table.select('tr'):
            th = row.select_one('th')
            td = row.select_one('td')
            if th and td:
                product["attributes"][clean_text(th.get_text())] = clean_text(td.get_text())
    
    # Datasheet PDF
    datasheet = soup.select_one('a[href*=".pdf"]')
    if datasheet:
        product["datasheet_url"] = datasheet.get('href', '')
    
    return product


async def get_tus_product_urls(session: aiohttp.ClientSession) -> list:
    """Get all TUS product URLs"""
    base_url = SITES["tus"]["base_url"]
    product_urls = set()
    
    for cat_url in SITES["tus"]["categories"]:
        page = 1
        while True:
            url = f"{base_url}{cat_url}page/{page}/" if page > 1 else f"{base_url}{cat_url}"
            html = await fetch_page(session, url)
            if not html:
                break
            
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.select('a.woocommerce-LoopProduct-link, a[href*="/produits/"]')
            
            found = 0
            for link in links:
                href = link.get('href', '')
                if '/produits/' in href and href not in product_urls:
                    product_urls.add(href)
                    found += 1
            
            if found == 0:
                break
            
            page += 1
            if page > 50:  # Safety limit
                break
            
            await asyncio.sleep(0.2)
    
    logger.info(f"TUS: Found {len(product_urls)} product URLs")
    return list(product_urls)


# ============= TELESYS SCRAPER =============
def parse_telesys_product(html: str, url: str) -> dict:
    """Parse Telesys product page"""
    soup = BeautifulSoup(html, 'html.parser')
    product = {"source": "telesys", "source_url": url}
    
    # Name
    title = soup.select_one('h1.product_title, h1.entry-title, h1')
    product["name"] = clean_text(title.get_text()) if title else ""
    
    # SKU/Reference
    sku = soup.select_one('.sku, .product_meta .sku')
    product["sku"] = clean_text(sku.get_text()) if sku else ""
    
    # Price
    price = soup.select_one('.price ins .amount, .price .amount')
    if price:
        price_text = re.sub(r'[^\d,\.]', '', price.get_text())
        product["price"] = price_text.replace(',', '.')
    
    # Description
    desc = soup.select_one('.woocommerce-product-details__short-description, .product-short-description')
    product["short_description"] = clean_text(desc.get_text()) if desc else ""
    
    full_desc = soup.select_one('#tab-description, .product-description')
    product["full_description"] = clean_text(full_desc.get_text()) if full_desc else ""
    
    # Meta
    meta = soup.select_one('meta[name="description"]')
    product["meta_description"] = meta.get('content', '') if meta else ""
    
    # Category
    breadcrumb = soup.select('.woocommerce-breadcrumb a, .breadcrumb a')
    product["categories"] = [clean_text(b.get_text()) for b in breadcrumb[1:]] if breadcrumb else []
    
    # Brand
    brand = soup.select_one('.product_meta a[href*="marque"], .brand')
    product["brand"] = clean_text(brand.get_text()) if brand else ""
    
    # Images
    product["images"] = []
    
    og_img = soup.select_one('meta[property="og:image"]')
    if og_img:
        product["images"].append(og_img.get('content', ''))
    
    gallery = soup.select('.woocommerce-product-gallery__image img, .product-gallery img')
    for img in gallery:
        img_url = img.get('data-large_image') or img.get('data-src') or img.get('src', '')
        if img_url and not img_url.startswith('data:') and img_url not in product["images"]:
            product["images"].append(img_url)
    
    # Specifications
    product["specifications"] = []
    spec_table = soup.select_one('.woocommerce-product-attributes, #tab-additional_information table')
    if spec_table:
        specs = []
        for row in spec_table.select('tr'):
            th = row.select_one('th')
            td = row.select_one('td')
            if th and td:
                specs.append({"key": clean_text(th.get_text()), "value": clean_text(td.get_text())})
        if specs:
            product["specifications"].append({"name": "Caractéristiques", "specs": specs})
    
    # Attributes
    product["attributes"] = {}
    attrs = soup.select('.product_meta span')
    for attr in attrs:
        text = attr.get_text()
        if ':' in text:
            key, value = text.split(':', 1)
            product["attributes"][clean_text(key)] = clean_text(value)
    
    return product


async def get_telesys_product_urls(session: aiohttp.ClientSession) -> list:
    """Get all Telesys product URLs"""
    base_url = SITES["telesys"]["base_url"]
    product_urls = set()
    
    # Telesys has paginated product listing
    for page in range(1, 100):
        url = f"{base_url}/produits-telesys/page/{page}/"
        html = await fetch_page(session, url)
        if not html:
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.select('a.product-image-link, a[href*="tunisie-prix"]')
        
        found = 0
        for link in links:
            href = link.get('href', '')
            if href and 'telesys.com.tn' in href and href not in product_urls:
                product_urls.add(href)
                found += 1
        
        if found == 0:
            break
        
        await asyncio.sleep(0.2)
    
    logger.info(f"Telesys: Found {len(product_urls)} product URLs")
    return list(product_urls)


# ============= SOMFY SCRAPER =============
def parse_somfy_product(html: str, url: str) -> dict:
    """Parse Somfy product page"""
    soup = BeautifulSoup(html, 'html.parser')
    product = {"source": "somfy", "source_url": url}
    
    # Name
    title = soup.select_one('h1.pdp-title, h1')
    product["name"] = clean_text(title.get_text()) if title else ""
    
    # SKU
    sku = soup.select_one('.pdp-sku, [data-sku]')
    product["sku"] = clean_text(sku.get_text()) if sku else ""
    if not product["sku"]:
        sku_match = re.search(r'ref[:\s]*([A-Z0-9-]+)', html, re.I)
        if sku_match:
            product["sku"] = sku_match.group(1)
    
    # Description
    desc = soup.select_one('.pdp-description, .product-description')
    product["short_description"] = clean_text(desc.get_text()) if desc else ""
    
    # Features
    features = soup.select('.pdp-features li, .product-features li')
    product["features"] = [clean_text(f.get_text()) for f in features]
    
    # Meta
    meta = soup.select_one('meta[name="description"]')
    product["meta_description"] = meta.get('content', '') if meta else ""
    
    # Category
    breadcrumb = soup.select('.breadcrumb a, nav a')
    product["categories"] = [clean_text(b.get_text()) for b in breadcrumb if 'somfy' not in b.get_text().lower()]
    
    product["brand"] = "Somfy"
    
    # Images
    product["images"] = []
    
    og_img = soup.select_one('meta[property="og:image"]')
    if og_img:
        product["images"].append(og_img.get('content', ''))
    
    gallery = soup.select('.pdp-gallery img, .product-image img, img[src*="somfy"]')
    for img in gallery:
        img_url = img.get('data-src') or img.get('src', '')
        if img_url and not img_url.startswith('data:') and img_url not in product["images"]:
            if not img_url.startswith('http'):
                img_url = urljoin(SITES["somfy"]["base_url"], img_url)
            product["images"].append(img_url)
    
    # Specifications
    product["specifications"] = []
    specs_section = soup.select('.pdp-specifications tr, .product-specs tr')
    specs = []
    for row in specs_section:
        cells = row.select('td, th')
        if len(cells) >= 2:
            specs.append({"key": clean_text(cells[0].get_text()), "value": clean_text(cells[-1].get_text())})
    if specs:
        product["specifications"].append({"name": "Spécifications", "specs": specs})
    
    return product


async def get_somfy_product_urls(session: aiohttp.ClientSession) -> list:
    """Get all Somfy product URLs"""
    base_url = SITES["somfy"]["base_url"]
    product_urls = set()
    
    for cat_url in SITES["somfy"]["categories"]:
        url = f"{base_url}{cat_url}"
        html = await fetch_page(session, url)
        if not html:
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.select('a[href*="/produits/"]')
        
        for link in links:
            href = link.get('href', '')
            if href and '/produits/' in href:
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                # Check if it's a product page (has more path segments)
                path = urlparse(href).path
                if path.count('/') >= 3:
                    product_urls.add(href)
        
        await asyncio.sleep(0.2)
    
    logger.info(f"Somfy: Found {len(product_urls)} product URLs")
    return list(product_urls)


# ============= SOMEF SCRAPER =============
def parse_somef_product(html: str, url: str) -> dict:
    """Parse SOMEF product page - Enhanced version to extract all data"""
    soup = BeautifulSoup(html, 'html.parser')
    product = {"source": "somef", "source_url": url}
    
    # Name
    title = soup.select_one('h1.product-title, h1[itemprop="name"], h1.h1')
    product["name"] = clean_text(title.get_text()) if title else ""
    
    # SKU/Reference
    sku = soup.select_one('.product-reference span[itemprop="sku"], .product-reference, [itemprop="sku"]')
    product["sku"] = clean_text(sku.get_text().replace('Référence', '').replace('REF°', '').replace(':', '').strip()) if sku else ""
    
    # Price
    price = soup.select_one('.product-price, [itemprop="price"]')
    if price:
        price_text = price.get('content', '') or price.get_text()
        price_match = re.search(r'[\d,\.]+', price_text)
        if price_match:
            product["price"] = price_match.group().replace(',', '.')
    
    # Short Description (from the product info section)
    short_desc = soup.select_one('.product-description[itemprop="description"]')
    if not short_desc:
        short_desc = soup.select_one('[itemprop="description"]')
    if not short_desc:
        # Try to find description by id pattern
        for div in soup.select('div.product-description'):
            if div.get('id', '').startswith('product-description-short-'):
                short_desc = div
                break
    product["short_description"] = clean_text(short_desc.get_text()) if short_desc else ""
    
    # Full Description - from the details section
    full_desc = soup.select_one('.descriptionpdt .product-description, #details .product-description')
    if full_desc:
        product["full_description"] = clean_text(full_desc.get_text())
    
    # Meta
    meta = soup.select_one('meta[name="description"]')
    product["meta_description"] = meta.get('content', '') if meta else ""
    
    # Category
    breadcrumb = soup.select('.breadcrumb a, ol.breadcrumb li a')
    product["categories"] = [clean_text(b.get_text()) for b in breadcrumb if clean_text(b.get_text())]
    
    product["brand"] = "SOMEF"
    
    # Images - Enhanced extraction
    product["images"] = []
    
    # Main image from product cover
    main_img = soup.select_one('.product-cover img.js-qv-product-cover')
    if main_img:
        img_url = main_img.get('src', '')
        if img_url and not img_url.startswith('data:'):
            # Try to get large version
            img_url = img_url.replace('-medium_default/', '-large_default/').replace('-home_default/', '-large_default/')
            if not img_url.startswith('http'):
                img_url = urljoin(SITES["somef"]["base_url"], img_url)
            product["images"].append(img_url)
    
    # Gallery thumbnails - get large versions
    gallery = soup.select('.product-images img.thumb, .js-qv-product-images img')
    for img in gallery:
        img_url = img.get('data-image-large-src') or img.get('src', '')
        if img_url and not img_url.startswith('data:'):
            if not img_url.startswith('http'):
                img_url = urljoin(SITES["somef"]["base_url"], img_url)
            if img_url not in product["images"]:
                product["images"].append(img_url)
    
    # Extract images from description content (promotional/marketing images)
    desc_imgs = soup.select('.descriptionpdt img, .product-description img, #details img')
    for img in desc_imgs:
        img_url = img.get('src', '')
        if img_url and not img_url.startswith('data:') and 'youtube' not in img_url.lower():
            if not img_url.startswith('http'):
                img_url = urljoin(SITES["somef"]["base_url"], img_url)
            if img_url not in product["images"]:
                product["images"].append(img_url)
    
    # Specifications/Features - Enhanced to extract from lists in description
    product["specifications"] = []
    specs = []
    
    # Method 1: Extract from structured product-features
    features = soup.select('.product-features li, .data-sheet tr')
    for f in features:
        name_elem = f.select_one('.name, td:first-child')
        value_elem = f.select_one('.value, td:last-child')
        if name_elem and value_elem:
            specs.append({"key": clean_text(name_elem.get_text()), "value": clean_text(value_elem.get_text())})
    
    # Method 2: Extract from description lists (ul > li) - Common in SOMEF pages
    desc_lists = soup.select('.descriptionpdt ul, .product-description ul, #details ul')
    for ul in desc_lists:
        list_items = ul.select('li')
        for li in list_items:
            item_text = clean_text(li.get_text())
            if item_text and len(item_text) > 3:  # Skip empty or too short items
                # Try to split key:value format
                if ':' in item_text:
                    parts = item_text.split(':', 1)
                    specs.append({"key": parts[0].strip(), "value": parts[1].strip()})
                else:
                    # Single value specification (feature without key)
                    specs.append({"key": "Caractéristique", "value": item_text})
    
    if specs:
        product["specifications"].append({"name": "Caractéristiques techniques", "specs": specs})
    
    # Extract PDF attachments
    attachments = soup.select('.product-attachments a[href*=".pdf"], a[href*="attachment"]')
    product["attachments"] = []
    for att in attachments:
        att_url = att.get('href', '')
        att_name = clean_text(att.get_text())
        if att_url:
            if not att_url.startswith('http'):
                att_url = urljoin(SITES["somef"]["base_url"], att_url)
            product["attachments"].append({"name": att_name, "url": att_url})
    
    # YouTube videos - Enhanced extraction from iframes and links
    product["videos"] = []
    
    # From iframes
    iframes = soup.select('iframe[src*="youtube"]')
    for iframe in iframes:
        src = iframe.get('src', '')
        video_id_match = re.search(r'youtube\.com/embed/([a-zA-Z0-9_-]{11})', src)
        if video_id_match:
            vid = video_id_match.group(1)
            product["videos"].append({
                "video_id": vid,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "embed_url": f"https://www.youtube.com/embed/{vid}",
                "thumbnail": f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"
            })
    
    # From links
    youtube_links = soup.select('a[href*="youtube.com"], a[href*="youtu.be"]')
    for link in youtube_links:
        href = link.get('href', '')
        video_id_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', href)
        if video_id_match:
            vid = video_id_match.group(1)
            # Avoid duplicates
            if not any(v.get('video_id') == vid for v in product["videos"]):
                product["videos"].append({
                    "video_id": vid,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "embed_url": f"https://www.youtube.com/embed/{vid}",
                    "thumbnail": f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"
                })
    
    return product


async def get_somef_product_urls(session: aiohttp.ClientSession) -> list:
    """Get all SOMEF product URLs"""
    base_url = SITES["somef"]["base_url"]
    product_urls = set()
    
    for cat_url in SITES["somef"]["categories"]:
        page = 1
        while True:
            url = f"{base_url}{cat_url}?page={page}" if page > 1 else f"{base_url}{cat_url}"
            html = await fetch_page(session, url)
            if not html:
                break
            
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.select('a.thumbnail.product-thumbnail, a[href*=".html"]')
            
            found = 0
            for link in links:
                href = link.get('href', '')
                if href and '.html' in href:
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    if href not in product_urls:
                        product_urls.add(href)
                        found += 1
            
            if found == 0:
                break
            
            page += 1
            if page > 50:
                break
            
            await asyncio.sleep(0.2)
    
    logger.info(f"SOMEF: Found {len(product_urls)} product URLs")
    return list(product_urls)


# ============= MAIN SCRAPER =============
async def scrape_site(session: aiohttp.ClientSession, site_key: str, limit: int = None) -> list:
    """Scrape all products from a site"""
    site = SITES[site_key]
    products = []
    
    # Get product URLs
    if site_key == "tus":
        urls = await get_tus_product_urls(session)
        parser = parse_tus_product
    elif site_key == "telesys":
        urls = await get_telesys_product_urls(session)
        parser = parse_telesys_product
    elif site_key == "somfy":
        urls = await get_somfy_product_urls(session)
        parser = parse_somfy_product
    elif site_key == "somef":
        urls = await get_somef_product_urls(session)
        parser = parse_somef_product
    else:
        return []
    
    if limit:
        urls = urls[:limit]
    
    logger.info(f"Scraping {len(urls)} products from {site['name']}...")
    
    for i, url in enumerate(urls):
        try:
            html = await fetch_page(session, url)
            if not html:
                continue
            
            # Parse product
            product = parser(html, url)
            product["id"] = str(uuid.uuid4())
            product["scraped_at"] = datetime.now(timezone.utc).isoformat()
            
            # Extract YouTube videos
            product["videos"] = extract_youtube_urls(html)
            
            # Download images
            downloaded_images = []
            for img_url in product.get("images", [])[:10]:  # Limit to 10 images per product
                img_data = await download_image(session, img_url, site_key, product["id"])
                if img_data:
                    downloaded_images.append(img_data)
            product["downloaded_images"] = downloaded_images
            
            products.append(product)
            stats["total_products"] += 1
            
            if (i + 1) % 20 == 0:
                logger.info(f"  {site_key}: {i + 1}/{len(urls)} products scraped")
            
            await asyncio.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
    
    stats["by_site"][site_key] = len(products)
    return products


async def run_full_scrape(sites: list = None, limit_per_site: int = None):
    """Run full scrape for all or specified sites"""
    if sites is None:
        sites = list(SITES.keys())
    
    all_products = {}
    
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        for site_key in sites:
            if site_key in SITES:
                logger.info(f"\n{'='*50}")
                logger.info(f"Starting scrape: {SITES[site_key]['name']}")
                logger.info(f"{'='*50}")
                
                products = await scrape_site(session, site_key, limit=limit_per_site)
                all_products[site_key] = products
                
                logger.info(f"Completed {site_key}: {len(products)} products")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save combined JSON
    output_file = OUTPUT_DIR / f"all_products_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "stats": stats,
                "sites": list(all_products.keys())
            },
            "products": all_products
        }, f, ensure_ascii=False, indent=2)
    
    # Save per-site JSON files
    for site_key, products in all_products.items():
        site_file = OUTPUT_DIR / f"{site_key}_products_{timestamp}.json"
        with open(site_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n{'='*50}")
    logger.info("SCRAPE COMPLETE")
    logger.info(f"{'='*50}")
    logger.info(f"Total products: {stats['total_products']}")
    logger.info(f"Total images: {stats['total_images']}")
    logger.info(f"Total videos: {stats['total_videos']}")
    logger.info(f"By site: {stats['by_site']}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Images: {IMAGES_DIR}")
    
    return output_file


if __name__ == "__main__":
    import sys
    
    # Parse arguments
    sites = None
    limit = None
    
    if len(sys.argv) > 1:
        if sys.argv[1].isdigit():
            limit = int(sys.argv[1])
        else:
            sites = sys.argv[1].split(',')
    
    if len(sys.argv) > 2:
        limit = int(sys.argv[2])
    
    asyncio.run(run_full_scrape(sites=sites, limit_per_site=limit))
