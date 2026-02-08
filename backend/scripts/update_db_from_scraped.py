"""
Script pour mettre à jour la base de données avec les données scrapées
- Ajoute les descriptions manquantes
- Ajoute les liens YouTube
- Ajoute les images supplémentaires
- Met à jour les spécifications
"""
import json
import os
import shutil
from pathlib import Path
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
SCRAPED_JSON = '/app/scraped_data/all_products_20260207_214032.json'
SCRAPED_IMAGES_DIR = Path('/app/scraped_data/images')
UPLOAD_DIR = Path('/app/uploads/products')

# Mapping des fournisseurs
SOURCE_TO_FOURNISSEUR = {
    'tus': 'TUS',
    'telesys': 'Telesys',
    'somfy': 'somfy',
    'somef': 'somef'
}

stats = {
    "total_matched": 0,
    "descriptions_updated": 0,
    "videos_added": 0,
    "images_added": 0,
    "specs_updated": 0,
    "not_matched": 0,
    "errors": 0
}


def normalize_url(url: str) -> str:
    """Normalize URL for matching"""
    if not url:
        return ""
    url = url.lower().strip()
    url = url.rstrip('/')
    # Remove protocol
    url = url.replace('https://', '').replace('http://', '')
    # Remove www
    url = url.replace('www.', '')
    return url


def find_matching_product(db, scraped_product: dict) -> dict:
    """Find matching product in database"""
    source_url = scraped_product.get('source_url', '')
    name = scraped_product.get('name', '')
    sku = scraped_product.get('sku', '')
    
    # Try matching by source_url first
    if source_url:
        normalized_url = normalize_url(source_url)
        
        # Direct match
        product = db.products.find_one({"source_url": source_url})
        if product:
            return product
        
        # Partial match on URL
        product = db.products.find_one({
            "source_url": {"$regex": normalized_url.split('/')[-1], "$options": "i"}
        })
        if product:
            return product
    
    # Try matching by SKU
    if sku and len(sku) > 2:
        product = db.products.find_one({"sku": sku})
        if product:
            return product
    
    # Try matching by name (exact)
    if name:
        product = db.products.find_one({"name": name})
        if product:
            return product
        
        # Partial name match (first 30 chars)
        if len(name) > 30:
            product = db.products.find_one({
                "name": {"$regex": f"^{name[:30]}", "$options": "i"}
            })
            if product:
                return product
    
    return None


def copy_image_to_uploads(scraped_image: dict, product_id: str) -> str:
    """Copy scraped image to uploads directory and return new path"""
    try:
        source_path = Path(scraped_image.get('local_path', ''))
        if not source_path.exists():
            return None
        
        # Generate new filename
        filename = scraped_image.get('filename', '')
        if not filename:
            return None
        
        # Copy to uploads
        dest_path = UPLOAD_DIR / filename
        if not dest_path.exists():
            shutil.copy2(source_path, dest_path)
        
        return f"/api/upload/products/{filename}"
    except Exception as e:
        logger.debug(f"Error copying image: {e}")
        return None


def update_product(db, db_product: dict, scraped_product: dict) -> dict:
    """Update database product with scraped data"""
    updates = {}
    product_id = db_product.get('id', str(db_product.get('_id', '')))
    
    # 1. Update description if current is shorter
    current_desc = db_product.get('description', '') or ''
    scraped_short_desc = scraped_product.get('short_description', '') or ''
    scraped_full_desc = scraped_product.get('full_description', '') or ''
    scraped_meta_desc = scraped_product.get('meta_description', '') or ''
    
    # Choose best description
    best_desc = max([scraped_short_desc, scraped_full_desc, scraped_meta_desc], key=len)
    
    if len(best_desc) > len(current_desc) + 50:  # Only update if significantly longer
        updates['description'] = best_desc
        stats["descriptions_updated"] += 1
    
    # 2. Add YouTube videos
    scraped_videos = scraped_product.get('videos', [])
    current_videos = db_product.get('videos', [])
    
    if scraped_videos and not current_videos:
        updates['videos'] = scraped_videos
        stats["videos_added"] += len(scraped_videos)
    elif scraped_videos:
        # Merge videos (avoid duplicates)
        existing_ids = {v.get('video_id') for v in current_videos if isinstance(v, dict)}
        new_videos = [v for v in scraped_videos if v.get('video_id') not in existing_ids]
        if new_videos:
            updates['videos'] = current_videos + new_videos
            stats["videos_added"] += len(new_videos)
    
    # 3. Add additional images
    scraped_images = scraped_product.get('downloaded_images', [])
    current_images = db_product.get('images', []) or []
    current_primary = db_product.get('primary_image_url', '')
    
    new_image_urls = []
    for img in scraped_images:
        local_url = copy_image_to_uploads(img, product_id)
        if local_url and local_url not in current_images and local_url != current_primary:
            new_image_urls.append(local_url)
    
    if new_image_urls:
        # Add to images array
        all_images = list(set(current_images + new_image_urls))
        updates['images'] = all_images
        stats["images_added"] += len(new_image_urls)
        
        # Set primary image if missing
        if not current_primary or not current_primary.startswith('/api/upload'):
            updates['primary_image_url'] = new_image_urls[0]
            updates['image_url'] = new_image_urls[0]
    
    # 4. Update specifications if missing or less complete
    scraped_specs = scraped_product.get('specifications', [])
    current_specs = db_product.get('specifications', [])
    
    if scraped_specs:
        # Count total specs
        scraped_spec_count = sum(len(s.get('specs', [])) for s in scraped_specs if isinstance(s, dict))
        current_spec_count = 0
        if current_specs and isinstance(current_specs, list):
            current_spec_count = sum(len(s.get('specs', [])) for s in current_specs if isinstance(s, dict))
        
        if scraped_spec_count > current_spec_count:
            updates['specifications'] = scraped_specs
            stats["specs_updated"] += 1
    
    # 5. Update brand if missing
    if not db_product.get('brand') and scraped_product.get('brand'):
        updates['brand'] = scraped_product['brand']
    
    # 6. Update SKU if missing
    if not db_product.get('sku') and scraped_product.get('sku'):
        updates['sku'] = scraped_product['sku']
    
    # 7. Add categories if missing
    if not db_product.get('categories') and scraped_product.get('categories'):
        updates['scraped_categories'] = scraped_product['categories']
    
    # 8. Add features if available
    if scraped_product.get('features'):
        updates['features'] = scraped_product['features']
    
    # 9. Add datasheet URL if available
    if scraped_product.get('datasheet_url') and not db_product.get('datasheet_url'):
        updates['datasheet_url'] = scraped_product['datasheet_url']
    
    # 10. Add attributes
    if scraped_product.get('attributes'):
        current_attrs = db_product.get('attributes', {}) or {}
        merged_attrs = {**scraped_product['attributes'], **current_attrs}
        if merged_attrs != current_attrs:
            updates['attributes'] = merged_attrs
    
    return updates


def run_update():
    """Main update function"""
    logger.info("Loading scraped data...")
    
    with open(SCRAPED_JSON, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    total_scraped = 0
    for site, products in scraped_data['products'].items():
        total_scraped += len(products)
    
    logger.info(f"Total scraped products: {total_scraped}")
    logger.info(f"Processing updates...")
    
    processed = 0
    for site, products in scraped_data['products'].items():
        fournisseur = SOURCE_TO_FOURNISSEUR.get(site, site)
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing {site.upper()}: {len(products)} products")
        logger.info(f"{'='*50}")
        
        for i, scraped_product in enumerate(products):
            try:
                # Find matching product
                db_product = find_matching_product(db, scraped_product)
                
                if not db_product:
                    # Try by fournisseur + partial name
                    name = scraped_product.get('name', '')
                    if name and len(name) > 10:
                        db_product = db.products.find_one({
                            "fournisseur": fournisseur,
                            "name": {"$regex": name[:20], "$options": "i"}
                        })
                
                if db_product:
                    stats["total_matched"] += 1
                    
                    # Get updates
                    updates = update_product(db, db_product, scraped_product)
                    
                    if updates:
                        updates['data_enriched_at'] = datetime.now(timezone.utc).isoformat()
                        updates['scraped_source'] = site
                        
                        # Apply updates
                        db.products.update_one(
                            {"_id": db_product['_id']},
                            {"$set": updates}
                        )
                else:
                    stats["not_matched"] += 1
                
                processed += 1
                if processed % 100 == 0:
                    logger.info(f"Progress: {processed}/{total_scraped} - Matched: {stats['total_matched']}")
                    
            except Exception as e:
                logger.error(f"Error processing product: {e}")
                stats["errors"] += 1
    
    client.close()
    
    logger.info("\n" + "=" * 50)
    logger.info("UPDATE COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Total processed: {processed}")
    logger.info(f"Matched products: {stats['total_matched']}")
    logger.info(f"Not matched: {stats['not_matched']}")
    logger.info(f"Descriptions updated: {stats['descriptions_updated']}")
    logger.info(f"Videos added: {stats['videos_added']}")
    logger.info(f"Images added: {stats['images_added']}")
    logger.info(f"Specifications updated: {stats['specs_updated']}")
    logger.info(f"Errors: {stats['errors']}")
    
    return stats


if __name__ == "__main__":
    run_update()
