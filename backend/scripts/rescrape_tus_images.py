"""
Script pour re-scraper les images des produits TUS
Visite chaque page produit et récupère la vraie URL d'image
"""
import asyncio
import aiohttp
import os
import re
import hashlib
from pathlib import Path
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
PRODUCTS_DIR = Path("/app/uploads/products")
PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://tus.com.tn"

stats = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "no_image_found": 0
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch page HTML"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        }
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
    return None


def extract_real_image_url(html: str, product_url: str) -> str:
    """Extract real image URL from product page HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Strategy 1: PRIORITY - Look for og:image meta tag (most reliable)
    og_image = soup.select_one('meta[property="og:image"]')
    if og_image:
        content = og_image.get('content', '')
        if content and 'wp-content/uploads' in content and not content.startswith('data:') and 'animation' not in content.lower():
            return content
    
    # Strategy 2: Look for twitter:image meta tag
    twitter_image = soup.select_one('meta[name="twitter:image"]')
    if twitter_image:
        content = twitter_image.get('content', '')
        if content and 'wp-content/uploads' in content and not content.startswith('data:') and 'animation' not in content.lower():
            return content
    
    # Strategy 3: Look in woocommerce gallery link (href usually has full image)
    gallery_link = soup.select_one('.woocommerce-product-gallery__image a')
    if gallery_link:
        href = gallery_link.get('href', '')
        if href and 'wp-content/uploads' in href and not href.startswith('data:') and 'animation' not in href.lower():
            return href
    
    # Strategy 4: Look for data-large_image attribute (WooCommerce)
    for img in soup.select('.woocommerce-product-gallery img, .product-images img'):
        large_img = img.get('data-large_image', '')
        if large_img and 'wp-content/uploads' in large_img and not large_img.startswith('data:') and 'animation' not in large_img.lower():
            return large_img
    
    # Strategy 5: Look for any image with product model name pattern
    slug_match = re.search(r'/produits/([^/]+)/', product_url)
    if slug_match:
        slug = slug_match.group(1).upper().replace('-', '')
        for img in soup.select('img'):
            src = img.get('src', '') or img.get('data-src', '') or img.get('data-lzl-src', '')
            if src and slug in src.upper().replace('-', '') and 'wp-content/uploads' in src:
                if not src.startswith('data:') and 'animation' not in src.lower():
                    src = re.sub(r'-\d+x\d+\.', '.', src)
                    if not src.startswith('http'):
                        src = BASE_URL + src
                    return src
    
    # Strategy 6: Look for wp-content/uploads in any image (excluding animations/loaders)
    for img in soup.select('img'):
        src = img.get('data-large_image') or img.get('data-lzl-src') or img.get('data-src') or img.get('src', '')
        if src and 'wp-content/uploads' in src and not src.startswith('data:'):
            # Skip animation/loader images
            if 'animation' in src.lower() or 'loader' in src.lower() or 'loading' in src.lower():
                continue
            # Skip tiny placeholder images
            if 'placeholder' in src.lower():
                continue
            # Clean up size suffixes
            src = re.sub(r'-\d+x\d+\.', '.', src)
            if not src.startswith('http'):
                src = BASE_URL + src
            return src
    
    return None


async def download_image(session: aiohttp.ClientSession, url: str, product_id: str) -> dict:
    """Download image and save locally"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/*',
            'Referer': BASE_URL
        }
        
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                return {"status": "error", "error": f"HTTP {response.status}"}
            
            content = await response.read()
            
            if len(content) < 1000:  # Minimum 1KB for real image
                return {"status": "error", "error": "Image too small"}
            
            # Determine extension
            ext = Path(url.split('?')[0]).suffix.lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = '.jpg'
            
            # Generate filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{product_id}_{url_hash}{ext}"
            file_path = PRODUCTS_DIR / filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(content)
            
            local_url = f"/api/upload/products/{filename}"
            return {"status": "success", "local_url": local_url, "size": len(content)}
            
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


async def process_product(session: aiohttp.ClientSession, db, product: dict) -> bool:
    """Process a single product: fetch page, extract image, download, update DB"""
    product_id = product.get('id')
    source_url = product.get('source_url')
    
    if not source_url:
        stats["failed"] += 1
        return False
    
    # Fetch product page
    html = await fetch_page(session, source_url)
    if not html:
        stats["failed"] += 1
        return False
    
    # Extract real image URL
    image_url = extract_real_image_url(html, source_url)
    
    if not image_url:
        logger.warning(f"No image found for {product.get('name', product_id)[:50]}")
        stats["no_image_found"] += 1
        return False
    
    # Download image
    result = await download_image(session, image_url, product_id)
    
    if result["status"] != "success":
        logger.warning(f"Failed to download image for {product_id}: {result.get('error')}")
        stats["failed"] += 1
        return False
    
    # Update database
    db.products.update_one(
        {"id": product_id},
        {"$set": {
            "primary_image_url": result["local_url"],
            "image_url": result["local_url"],
            "image": result["local_url"],
            "original_image_url": image_url,
            "image_missing": False,
            "image_placeholder": False,
            "image_migrated_at": datetime.now(timezone.utc).isoformat(),
            "image_rescrape": True
        }}
    )
    
    stats["success"] += 1
    return True


async def rescrape_tus_images(limit: int = None):
    """Main function to re-scrape TUS product images"""
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find TUS products with placeholder images
    query = {"fournisseur": "TUS", "image_placeholder": True}
    products = list(db.products.find(query, {
        "id": 1, "name": 1, "source_url": 1
    }))
    
    if limit:
        products = products[:limit]
    
    stats["total"] = len(products)
    logger.info(f"🚀 Re-scraping images for {len(products)} TUS products")
    
    connector = aiohttp.TCPConnector(limit=5, limit_per_host=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i, product in enumerate(products):
            await process_product(session, db, product)
            
            if (i + 1) % 20 == 0:
                progress = ((i + 1) / len(products)) * 100
                logger.info(f"📊 Progress: {i + 1}/{len(products)} ({progress:.1f}%) - ✅ {stats['success']} | ❌ {stats['failed']} | 🔍 {stats['no_image_found']}")
            
            # Rate limiting
            await asyncio.sleep(0.3)
    
    client.close()
    
    logger.info("=" * 50)
    logger.info("📈 RÉSUMÉ RE-SCRAPE TUS")
    logger.info(f"   Total traités: {stats['total']}")
    logger.info(f"   ✅ Succès: {stats['success']}")
    logger.info(f"   ❌ Échecs: {stats['failed']}")
    logger.info(f"   🔍 Image non trouvée: {stats['no_image_found']}")
    logger.info("=" * 50)
    
    return stats


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(rescrape_tus_images(limit=limit))
