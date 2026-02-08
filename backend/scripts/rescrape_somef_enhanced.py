"""
Enhanced SOMEF Rescraper
Re-scrapes all SOMEF products to get:
- Technical specifications from description lists
- All gallery images
- YouTube videos from iframes and links
- PDF attachments

Then updates the database with the new information
"""
import asyncio
import aiohttp
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Import scraper functions
from scripts.unified_scraper import (
    fetch_page, 
    parse_somef_product, 
    get_somef_product_urls,
    SITES,
    download_image,
    extract_youtube_urls
)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
            filename = f"somef_{product_sku}_{url_hash}{ext}"
            filepath = IMAGES_DIR / filename
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            # Return API-accessible path
            return f"/api/upload/products/{filename}"
    except Exception as e:
        logger.debug(f"Failed to download image {url}: {e}")
        return None


async def rescrape_and_update_somef():
    """Rescrape all SOMEF products and update database"""
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        logger.error("Missing MONGO_URL or DB_NAME environment variables")
        return
    
    client = MongoClient(mongo_url)
    db = client[db_name]
    products_collection = db['products']
    
    # Stats
    stats = {
        'total_found': 0,
        'updated': 0,
        'new_specs': 0,
        'new_videos': 0,
        'new_images': 0,
        'errors': 0
    }
    
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Get all SOMEF product URLs
        logger.info("Fetching SOMEF product URLs...")
        product_urls = await get_somef_product_urls(session)
        stats['total_found'] = len(product_urls)
        logger.info(f"Found {len(product_urls)} SOMEF products to scrape")
        
        for i, url in enumerate(product_urls):
            try:
                # Fetch and parse product page
                html = await fetch_page(session, url)
                if not html:
                    continue
                
                product_data = parse_somef_product(html, url)
                
                # Extract additional YouTube videos from full HTML
                additional_videos = extract_youtube_urls(html)
                if additional_videos:
                    existing_ids = {v.get('video_id') for v in product_data.get('videos', [])}
                    for vid in additional_videos:
                        if vid.get('video_id') not in existing_ids:
                            product_data.setdefault('videos', []).append(vid)
                
                # Find existing product by SKU or name
                query = {}
                if product_data.get('sku'):
                    query = {'$or': [
                        {'sku': product_data['sku']},
                        {'name': {'$regex': product_data['name'], '$options': 'i'}}
                    ]}
                else:
                    query = {'name': {'$regex': product_data['name'][:30], '$options': 'i'}}
                
                existing_product = products_collection.find_one(query)
                
                if existing_product:
                    update_data = {}
                    
                    # Update specifications if we have new ones
                    if product_data.get('specifications') and len(product_data['specifications']) > 0:
                        specs = product_data['specifications']
                        if len(specs[0].get('specs', [])) > len(existing_product.get('specifications', [{}])[0].get('specs', []) if existing_product.get('specifications') else []):
                            update_data['specifications'] = specs
                            stats['new_specs'] += 1
                    
                    # Update videos if we have new ones
                    if product_data.get('videos'):
                        existing_videos = existing_product.get('videos', [])
                        existing_ids = {v.get('video_id') for v in existing_videos}
                        new_videos = [v for v in product_data['videos'] if v.get('video_id') not in existing_ids]
                        if new_videos:
                            update_data['videos'] = existing_videos + new_videos
                            stats['new_videos'] += len(new_videos)
                    
                    # Download and update images if needed
                    if product_data.get('images'):
                        existing_images = existing_product.get('images', [])
                        # Only download new images not already in database
                        new_image_urls = [img for img in product_data['images'] if img not in existing_images and not img.startswith('/api/upload')]
                        
                        if new_image_urls:
                            downloaded_images = []
                            for img_url in new_image_urls[:5]:  # Limit to 5 new images
                                local_path = await download_and_save_image(session, img_url, product_data.get('sku', 'unknown'))
                                if local_path:
                                    downloaded_images.append(local_path)
                            
                            if downloaded_images:
                                # Add new images to existing ones
                                update_data['images'] = existing_images + downloaded_images
                                stats['new_images'] += len(downloaded_images)
                    
                    # Update full description if empty
                    if product_data.get('full_description') and not existing_product.get('full_description'):
                        update_data['full_description'] = product_data['full_description']
                    
                    # Update attachments if we have new ones
                    if product_data.get('attachments'):
                        update_data['attachments'] = product_data['attachments']
                    
                    # Apply updates
                    if update_data:
                        update_data['updated_at'] = datetime.now(timezone.utc)
                        update_data['source_url'] = url
                        products_collection.update_one(
                            {'_id': existing_product['_id']},
                            {'$set': update_data}
                        )
                        stats['updated'] += 1
                        logger.info(f"Updated: {product_data['name']} ({product_data.get('sku', 'N/A')})")
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{len(product_urls)} products processed")
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing {url}: {e}")
    
    client.close()
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("SOMEF RESCRAPE COMPLETE")
    logger.info("="*50)
    logger.info(f"Total products found: {stats['total_found']}")
    logger.info(f"Products updated: {stats['updated']}")
    logger.info(f"New specifications added: {stats['new_specs']}")
    logger.info(f"New videos added: {stats['new_videos']}")
    logger.info(f"New images downloaded: {stats['new_images']}")
    logger.info(f"Errors: {stats['errors']}")
    
    return stats


if __name__ == "__main__":
    asyncio.run(rescrape_and_update_somef())
