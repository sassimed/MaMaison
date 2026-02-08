"""
Script de migration des images produits
Télécharge les images depuis les URLs externes et les stocke localement
"""

import asyncio
import aiohttp
import os
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

# Configuration
load_dotenv('/app/backend/.env')
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
UPLOAD_DIR = Path("/app/uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Stats
stats = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "skipped": 0,
    "already_local": 0
}


def get_file_extension(url: str, content_type: str = None) -> str:
    """Détermine l'extension du fichier"""
    # Try from URL first
    url_path = url.split('?')[0]
    ext = Path(url_path).suffix.lower()
    
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return ext
    
    # Fallback to content-type
    if content_type:
        type_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp'
        }
        return type_map.get(content_type, '.jpg')
    
    return '.jpg'


def generate_filename(product_id: str, url: str, ext: str) -> str:
    """Génère un nom de fichier unique basé sur le produit et l'URL"""
    # Use hash of URL for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{product_id}_{url_hash}{ext}"


async def download_image(session: aiohttp.ClientSession, url: str, product_id: str) -> dict:
    """Télécharge une image et retourne le chemin local"""
    try:
        # Skip if already local
        if url.startswith('/api/upload') or url.startswith('/uploads'):
            return {"status": "already_local", "url": url}
        
        # Add headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/*',
            'Referer': url.split('/')[2] if '/' in url else ''
        }
        
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                return {"status": "error", "error": f"HTTP {response.status}"}
            
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return {"status": "error", "error": f"Not an image: {content_type}"}
            
            content = await response.read()
            
            # Check size (max 10MB)
            if len(content) > 10 * 1024 * 1024:
                return {"status": "error", "error": "File too large"}
            
            if len(content) < 100:
                return {"status": "error", "error": "File too small"}
            
            # Save file
            ext = get_file_extension(url, content_type)
            filename = generate_filename(product_id, url, ext)
            file_path = UPLOAD_DIR / filename
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            local_url = f"/api/upload/products/{filename}"
            return {"status": "success", "local_url": local_url, "size": len(content)}
            
    except asyncio.TimeoutError:
        return {"status": "error", "error": "Timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


async def process_product(session: aiohttp.ClientSession, db, product: dict) -> bool:
    """Traite un produit: télécharge ses images et met à jour la base"""
    product_id = product.get('id', str(product.get('_id', '')))
    
    # Get image URLs
    primary_url = product.get('primary_image_url') or product.get('image_url')
    additional_images = product.get('images', [])
    
    if not primary_url:
        stats["skipped"] += 1
        return False
    
    # Check if already migrated
    if primary_url.startswith('/api/upload'):
        stats["already_local"] += 1
        return True
    
    updates = {}
    
    # Download primary image
    result = await download_image(session, primary_url, product_id)
    
    if result["status"] == "success":
        updates["primary_image_url"] = result["local_url"]
        updates["image_url"] = result["local_url"]  # Legacy field
        updates["image"] = result["local_url"]  # Another legacy field
    elif result["status"] == "already_local":
        stats["already_local"] += 1
        return True
    else:
        logger.warning(f"Failed to download primary image for {product_id}: {result.get('error')}")
        stats["failed"] += 1
        return False
    
    # Download additional images
    if additional_images:
        new_images = []
        for img_url in additional_images[:5]:  # Limit to 5 additional images
            if isinstance(img_url, str) and img_url.startswith('http'):
                img_result = await download_image(session, img_url, product_id)
                if img_result["status"] == "success":
                    new_images.append(img_result["local_url"])
                elif img_result["status"] == "already_local":
                    new_images.append(img_url)
            elif isinstance(img_url, str):
                new_images.append(img_url)
        
        if new_images:
            updates["images"] = new_images
    
    # Update database
    if updates:
        updates["image_migrated_at"] = datetime.utcnow().isoformat()
        updates["original_image_url"] = primary_url  # Keep original for reference
        
        await db.products.update_one(
            {"id": product_id},
            {"$set": updates}
        )
        stats["success"] += 1
        return True
    
    return False


async def migrate_images(batch_size: int = 20, limit: int = None):
    """Migration principale des images"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Count products to process
    query = {
        "$or": [
            {"primary_image_url": {"$regex": "^http"}},
            {"image_url": {"$regex": "^http"}}
        ],
        "primary_image_url": {"$ne": None}
    }
    
    total = await db.products.count_documents(query)
    stats["total"] = total if not limit else min(total, limit)
    
    logger.info(f"🚀 Démarrage migration: {stats['total']} produits à traiter")
    
    # Process in batches
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        cursor = db.products.find(query)
        if limit:
            cursor = cursor.limit(limit)
        
        batch = []
        processed = 0
        
        async for product in cursor:
            batch.append(product)
            
            if len(batch) >= batch_size:
                # Process batch
                tasks = [process_product(session, db, p) for p in batch]
                await asyncio.gather(*tasks)
                
                processed += len(batch)
                progress = (processed / stats["total"]) * 100
                logger.info(f"📊 Progression: {processed}/{stats['total']} ({progress:.1f}%) - ✅ {stats['success']} | ❌ {stats['failed']} | ⏭️ {stats['skipped']}")
                
                batch = []
                await asyncio.sleep(0.5)  # Rate limiting
        
        # Process remaining
        if batch:
            tasks = [process_product(session, db, p) for p in batch]
            await asyncio.gather(*tasks)
    
    client.close()
    
    logger.info("=" * 50)
    logger.info("📈 RÉSUMÉ MIGRATION")
    logger.info(f"   Total traités: {stats['total']}")
    logger.info(f"   ✅ Succès: {stats['success']}")
    logger.info(f"   ❌ Échecs: {stats['failed']}")
    logger.info(f"   ⏭️ Sans image: {stats['skipped']}")
    logger.info(f"   🔄 Déjà local: {stats['already_local']}")
    logger.info("=" * 50)
    
    return stats


# Route endpoint pour déclencher la migration
async def run_migration_endpoint(limit: int = None):
    """Endpoint pour lancer la migration"""
    return await migrate_images(batch_size=20, limit=limit)


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(migrate_images(limit=limit))
