"""
Enhanced SOMEF Rescraper V2
Re-scrapes all SOMEF products with IMPROVED SKU MATCHING
Matches products by:
1. Exact SKU match
2. SKU contained in product name
3. Partial SKU match

Then updates the database with specifications, videos, and images
"""
import asyncio
import aiohttp
import os
import sys
import hashlib
import re
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from pymongo import MongoClient

# Import scraper functions
from scripts.unified_scraper import (
    fetch_page, 
    parse_somef_product, 
    get_somef_product_urls,
    SITES,
    extract_youtube_urls
)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

# Output directory for images
IMAGES_DIR = Path("/app/uploads/products")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


async def download_and_save_image(session: aiohttp.ClientSession, url: str, product_sku: str) -> str:
    """Download image and save to local uploads folder, return local path"""
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
            ext = Path(url.split('?')[0]).suffix.lower()
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
            safe_sku = re.sub(r'[^\w\-]', '_', product_sku or 'unknown')
            filename = f"somef_{safe_sku}_{url_hash}{ext}"
            filepath = IMAGES_DIR / filename
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            return f"/api/upload/products/{filename}"
    except Exception as e:
        logger.debug(f"Failed to download image {url}: {e}")
        return None


def find_matching_product(db, scraped_sku: str, scraped_name: str):
    """
    Find matching product in database using multiple strategies:
    1. Exact SKU match
    2. SKU contained in existing product's name
    3. Scraped SKU contained anywhere in existing product fields
    """
    if not scraped_sku:
        return None
    
    products_collection = db['products']
    
    # Strategy 1: Exact SKU match (case-insensitive)
    product = products_collection.find_one({
        'source': 'somef',
        'sku': {'$regex': f'^{re.escape(scraped_sku)}$', '$options': 'i'}
    })
    if product:
        return product
    
    # Strategy 2: SKU appears in product name
    product = products_collection.find_one({
        'source': 'somef',
        'name': {'$regex': re.escape(scraped_sku), '$options': 'i'}
    })
    if product:
        return product
    
    # Strategy 3: Try matching by partial SKU (remove special chars)
    clean_sku = re.sub(r'[^\w]', '', scraped_sku).upper()
    if len(clean_sku) >= 3:
        # Search in name field
        product = products_collection.find_one({
            'source': 'somef',
            '$or': [
                {'name': {'$regex': clean_sku, '$options': 'i'}},
                {'sku': {'$regex': clean_sku, '$options': 'i'}}
            ]
        })
        if product:
            return product
    
    # Strategy 4: Match by scraped name keywords
    if scraped_name:
        # Extract meaningful keywords (at least 4 chars)
        keywords = [w for w in scraped_name.split() if len(w) >= 4][:3]
        if keywords:
            regex_pattern = '.*'.join([re.escape(k) for k in keywords])
            product = products_collection.find_one({
                'source': 'somef',
                'name': {'$regex': regex_pattern, '$options': 'i'}
            })
            if product:
                return product
    
    return None


async def rescrape_and_update_somef_v2():
    """Rescrape all SOMEF products and update database with improved matching"""
    
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    products_collection = db['products']
    
    # Stats
    stats = {
        'total_scraped': 0,
        'matched': 0,
        'updated': 0,
        'specs_added': 0,
        'videos_added': 0,
        'images_added': 0,
        'not_matched': 0,
        'errors': 0
    }
    
    # Track unmatched products
    unmatched_products = []
    
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Get all SOMEF product URLs
        logger.info("Fetching SOMEF product URLs from website...")
        product_urls = await get_somef_product_urls(session)
        stats['total_scraped'] = len(product_urls)
        logger.info(f"Found {len(product_urls)} SOMEF products to scrape")
        
        for i, url in enumerate(product_urls):
            try:
                # Fetch and parse product page
                html = await fetch_page(session, url)
                if not html:
                    continue
                
                product_data = parse_somef_product(html, url)
                scraped_sku = product_data.get('sku', '')
                scraped_name = product_data.get('name', '')
                
                # Extract additional YouTube videos from full HTML
                additional_videos = extract_youtube_urls(html)
                if additional_videos:
                    existing_ids = {v.get('video_id') for v in product_data.get('videos', [])}
                    for vid in additional_videos:
                        if vid.get('video_id') not in existing_ids:
                            product_data.setdefault('videos', []).append(vid)
                
                # Find matching product in database
                existing_product = find_matching_product(db, scraped_sku, scraped_name)
                
                if existing_product:
                    stats['matched'] += 1
                    update_data = {}
                    
                    # Update specifications if we have new ones
                    scraped_specs = product_data.get('specifications', [])
                    if scraped_specs and len(scraped_specs) > 0:
                        scraped_spec_count = len(scraped_specs[0].get('specs', []))
                        existing_specs = existing_product.get('specifications', [])
                        existing_spec_count = len(existing_specs[0].get('specs', [])) if existing_specs else 0
                        
                        if scraped_spec_count > 0 and scraped_spec_count > existing_spec_count:
                            update_data['specifications'] = scraped_specs
                            stats['specs_added'] += 1
                    
                    # Update videos if we have new ones
                    if product_data.get('videos'):
                        existing_videos = existing_product.get('videos', [])
                        existing_ids = {v.get('video_id') for v in existing_videos}
                        new_videos = [v for v in product_data['videos'] if v.get('video_id') not in existing_ids]
                        if new_videos:
                            update_data['videos'] = existing_videos + new_videos
                            stats['videos_added'] += len(new_videos)
                    
                    # Download and update images if needed
                    if product_data.get('images'):
                        existing_images = existing_product.get('images', [])
                        new_image_urls = [
                            img for img in product_data['images'] 
                            if img not in existing_images and not img.startswith('/api/upload')
                        ]
                        
                        if new_image_urls:
                            downloaded_images = []
                            for img_url in new_image_urls[:5]:
                                local_path = await download_and_save_image(session, img_url, scraped_sku)
                                if local_path:
                                    downloaded_images.append(local_path)
                            
                            if downloaded_images:
                                update_data['images'] = existing_images + downloaded_images
                                stats['images_added'] += len(downloaded_images)
                    
                    # Update full description if empty
                    if product_data.get('full_description') and not existing_product.get('full_description'):
                        update_data['full_description'] = product_data['full_description']
                    
                    # Update source URL
                    update_data['source_url'] = url
                    
                    # Apply updates if any
                    if update_data:
                        update_data['updated_at'] = datetime.now(timezone.utc)
                        products_collection.update_one(
                            {'_id': existing_product['_id']},
                            {'$set': update_data}
                        )
                        stats['updated'] += 1
                        logger.info(f"✓ Updated: {scraped_name} (SKU: {scraped_sku})")
                else:
                    stats['not_matched'] += 1
                    unmatched_products.append({
                        'sku': scraped_sku,
                        'name': scraped_name,
                        'url': url
                    })
                
                if (i + 1) % 20 == 0:
                    logger.info(f"Progress: {i + 1}/{len(product_urls)} | Matched: {stats['matched']} | Updated: {stats['updated']}")
                
                # Rate limiting
                await asyncio.sleep(0.3)
                
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing {url}: {e}")
    
    client.close()
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("SOMEF RESCRAPE V2 COMPLETE")
    logger.info("="*60)
    logger.info(f"Total products scraped: {stats['total_scraped']}")
    logger.info(f"Products matched in DB: {stats['matched']}")
    logger.info(f"Products updated: {stats['updated']}")
    logger.info(f"Specifications added: {stats['specs_added']}")
    logger.info(f"Videos added: {stats['videos_added']}")
    logger.info(f"Images added: {stats['images_added']}")
    logger.info(f"Not matched: {stats['not_matched']}")
    logger.info(f"Errors: {stats['errors']}")
    
    # Save unmatched products for review
    if unmatched_products:
        logger.info(f"\nUnmatched products saved to /tmp/somef_unmatched.txt")
        with open('/tmp/somef_unmatched.txt', 'w') as f:
            for p in unmatched_products:
                f.write(f"SKU: {p['sku']} | Name: {p['name']} | URL: {p['url']}\n")
    
    return stats


if __name__ == "__main__":
    asyncio.run(rescrape_and_update_somef_v2())
