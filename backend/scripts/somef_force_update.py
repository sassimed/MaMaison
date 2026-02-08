"""
SOMEF Force Update Script
Forces update of specifications for ALL matched products regardless of existing specs
"""
import asyncio
import aiohttp
import re
from pymongo import MongoClient
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from scripts.unified_scraper import (
    fetch_page, 
    parse_somef_product, 
    get_somef_product_urls,
    extract_youtube_urls
)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"


def find_matching_product(db, scraped_sku: str, scraped_name: str):
    """Find matching product in database"""
    if not scraped_sku:
        return None
    
    products_collection = db['products']
    
    # Strategy 1: Exact SKU match
    product = products_collection.find_one({
        'source': 'somef',
        'sku': {'$regex': f'^{re.escape(scraped_sku)}$', '$options': 'i'}
    })
    if product:
        return product
    
    # Strategy 2: SKU in product name
    product = products_collection.find_one({
        'source': 'somef',
        'name': {'$regex': re.escape(scraped_sku), '$options': 'i'}
    })
    if product:
        return product
    
    # Strategy 3: Clean SKU match
    clean_sku = re.sub(r'[^\w]', '', scraped_sku).upper()
    if len(clean_sku) >= 3:
        product = products_collection.find_one({
            'source': 'somef',
            '$or': [
                {'name': {'$regex': clean_sku, '$options': 'i'}},
                {'sku': {'$regex': clean_sku, '$options': 'i'}}
            ]
        })
        if product:
            return product
    
    return None


async def force_update_somef():
    """Force update all SOMEF products with specs from website"""
    
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    products_collection = db['products']
    
    stats = {
        'total_scraped': 0,
        'matched': 0,
        'updated_with_specs': 0,
        'updated_with_videos': 0,
        'not_matched': 0,
        'errors': 0
    }
    
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        logger.info("Fetching SOMEF product URLs...")
        product_urls = await get_somef_product_urls(session)
        stats['total_scraped'] = len(product_urls)
        logger.info(f"Found {len(product_urls)} products to process")
        
        for i, url in enumerate(product_urls):
            try:
                html = await fetch_page(session, url)
                if not html:
                    continue
                
                product_data = parse_somef_product(html, url)
                scraped_sku = product_data.get('sku', '')
                scraped_name = product_data.get('name', '')
                
                # Extract videos
                additional_videos = extract_youtube_urls(html)
                if additional_videos:
                    existing_ids = {v.get('video_id') for v in product_data.get('videos', [])}
                    for vid in additional_videos:
                        if vid.get('video_id') not in existing_ids:
                            product_data.setdefault('videos', []).append(vid)
                
                # Find matching product
                existing_product = find_matching_product(db, scraped_sku, scraped_name)
                
                if existing_product:
                    stats['matched'] += 1
                    update_data = {'source_url': url, 'updated_at': datetime.now(timezone.utc)}
                    
                    # FORCE UPDATE: Always update specs if scraped has any
                    scraped_specs = product_data.get('specifications', [])
                    if scraped_specs and len(scraped_specs) > 0 and len(scraped_specs[0].get('specs', [])) > 0:
                        update_data['specifications'] = scraped_specs
                        stats['updated_with_specs'] += 1
                    
                    # Update videos if any
                    if product_data.get('videos'):
                        existing_videos = existing_product.get('videos', [])
                        existing_ids = {v.get('video_id') for v in existing_videos}
                        all_videos = existing_videos + [v for v in product_data['videos'] if v.get('video_id') not in existing_ids]
                        if len(all_videos) > len(existing_videos):
                            update_data['videos'] = all_videos
                            stats['updated_with_videos'] += 1
                    
                    # Apply updates
                    products_collection.update_one(
                        {'_id': existing_product['_id']},
                        {'$set': update_data}
                    )
                    
                    if scraped_specs and len(scraped_specs[0].get('specs', [])) > 0:
                        logger.info(f"✓ {scraped_name} ({scraped_sku}) - {len(scraped_specs[0]['specs'])} specs")
                else:
                    stats['not_matched'] += 1
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i + 1}/{len(product_urls)} | Specs updated: {stats['updated_with_specs']}")
                
                await asyncio.sleep(0.3)
                
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error: {url} - {e}")
    
    client.close()
    
    logger.info("\n" + "="*60)
    logger.info("SOMEF FORCE UPDATE COMPLETE")
    logger.info("="*60)
    logger.info(f"Total scraped: {stats['total_scraped']}")
    logger.info(f"Matched: {stats['matched']}")
    logger.info(f"Updated with specs: {stats['updated_with_specs']}")
    logger.info(f"Updated with videos: {stats['updated_with_videos']}")
    logger.info(f"Not matched: {stats['not_matched']}")
    logger.info(f"Errors: {stats['errors']}")
    
    return stats


if __name__ == "__main__":
    asyncio.run(force_update_somef())
