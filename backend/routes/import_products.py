"""
Product Import API - Import products from external sources (Telesys, SOMEF, TUS, Somfy, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import asyncio
import logging

from utils.dependencies import get_db, get_current_user
from models.user import User
from services.telesys_scraper import (
    scrape_all_products as scrape_telesys, 
    convert_to_mydar_product as convert_telesys,
)
from services.somef_scraper import (
    scrape_all_products as scrape_somef,
    convert_to_mydar_product as convert_somef,
    CATEGORIES as SOMEF_CATEGORIES
)
from services.tus_scraper import (
    scrape_all_products as scrape_tus,
    convert_to_mydar_product as convert_tus,
    CATEGORIES as TUS_CATEGORIES
)
from services.somfy_scraper import (
    scrape_all_products as scrape_somfy,
    convert_to_mydar_product as convert_somfy,
    CATEGORIES as SOMFY_CATEGORIES
)
import aiohttp

router = APIRouter(prefix="/import", tags=["Product Import"])
logger = logging.getLogger(__name__)

# Store import status
import_status = {
    "running": False,
    "progress": 0,
    "total": 0,
    "imported": 0,
    "skipped": 0,
    "errors": 0,
    "message": "",
    "started_at": None,
    "completed_at": None
}


class ImportRequest(BaseModel):
    source: str = "telesys"
    fournisseur: str = "Telesys"  # Supplier name (hidden from users)
    max_pages: Optional[int] = None  # None = all pages
    with_details: bool = True  # Fetch product details
    update_existing: bool = False  # Update existing products


class ImportStatus(BaseModel):
    running: bool
    progress: int
    total: int
    imported: int
    skipped: int
    errors: int
    message: str
    started_at: Optional[str]
    completed_at: Optional[str]


async def run_import_task(
    db: AsyncIOMotorDatabase,
    source: str,
    fournisseur: str,
    max_pages: Optional[int],
    with_details: bool,
    update_existing: bool
):
    """Background task to import products"""
    global import_status
    
    import_status["running"] = True
    import_status["progress"] = 0
    import_status["total"] = 0
    import_status["imported"] = 0
    import_status["skipped"] = 0
    import_status["errors"] = 0
    import_status["message"] = "Démarrage du scraping..."
    import_status["started_at"] = datetime.now(timezone.utc).isoformat()
    import_status["completed_at"] = None
    
    try:
        # Step 1: Scrape products based on source
        import_status["message"] = f"Scraping des produits depuis {source}..."
        logger.info(f"Starting import from {source}, fournisseur={fournisseur}, max_pages={max_pages}")
        
        if source.lower() == "somef":
            products = await scrape_somef(with_details=with_details)
            convert_func = convert_somef
        elif source.lower() == "tus":
            products = await scrape_tus(with_details=with_details)
            convert_func = convert_tus
        elif source.lower() == "somfy":
            products = await scrape_somfy(with_details=with_details)
            convert_func = convert_somfy
        else:  # telesys or default
            products = await scrape_telesys(max_pages=max_pages, with_details=with_details)
            convert_func = convert_telesys
        
        import_status["total"] = len(products)
        import_status["message"] = f"{len(products)} produits trouvés. Import en cours..."
        
        logger.info(f"Found {len(products)} products to import")
        
        # Step 2: Import products to database
        for i, product in enumerate(products):
            try:
                # Convert to MyDar format with fournisseur
                mydar_product = convert_func(product, source, fournisseur)
                
                # Check if product already exists (by source_url or name)
                existing = await db.products.find_one({
                    "$or": [
                        {"source_url": mydar_product["source_url"]},
                        {"name": mydar_product["name"]}
                    ]
                })
                
                if existing:
                    if update_existing:
                        # Update existing product
                        mydar_product["id"] = existing["id"]
                        mydar_product["created_at"] = existing.get("created_at", mydar_product["created_at"])
                        await db.products.update_one(
                            {"id": existing["id"]},
                            {"$set": mydar_product}
                        )
                        import_status["imported"] += 1
                    else:
                        import_status["skipped"] += 1
                else:
                    # Insert new product
                    await db.products.insert_one(mydar_product)
                    import_status["imported"] += 1
                
                import_status["progress"] = i + 1
                
            except Exception as e:
                logger.error(f"Error importing product {product.get('name', 'unknown')}: {e}")
                import_status["errors"] += 1
            
            # Update status message periodically
            if (i + 1) % 10 == 0:
                import_status["message"] = f"Import en cours... {i + 1}/{len(products)}"
        
        import_status["message"] = f"Import terminé ! {import_status['imported']} produits importés, {import_status['skipped']} ignorés, {import_status['errors']} erreurs."
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        import_status["message"] = f"Erreur: {str(e)}"
        import_status["errors"] += 1
    
    finally:
        import_status["running"] = False
        import_status["completed_at"] = datetime.now(timezone.utc).isoformat()


@router.post("/telesys", response_model=dict)
async def start_telesys_import(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Start importing products from Telesys website
    
    Admin only. Runs in background.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    if import_status["running"]:
        raise HTTPException(status_code=400, detail="Un import est déjà en cours")
    
    # Start background task
    background_tasks.add_task(
        run_import_task,
        db,
        request.source,
        request.fournisseur,
        request.max_pages,
        request.with_details,
        request.update_existing
    )
    
    return {
        "status": "started",
        "message": "Import démarré en arrière-plan. Utilisez GET /import/status pour suivre la progression."
    }


@router.get("/status", response_model=ImportStatus)
async def get_import_status(
    current_user: User = Depends(get_current_user)
):
    """Get current import status"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    return import_status


@router.post("/telesys/preview")
async def preview_telesys_import(
    max_products: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Preview products that would be imported (first page only)
    
    Admin only. Useful for testing before full import.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    try:
        # Scrape only first page without details for quick preview
        products = await scrape_all_products(max_pages=1, with_details=False)
        
        # Convert to MyDar format
        preview_products = []
        for p in products[:max_products]:
            mydar_product = convert_to_mydar_product(p, "telesys")
            preview_products.append({
                "name": mydar_product["name"],
                "category": mydar_product["category"],
                "brand": mydar_product["brand"],
                "image": mydar_product["image"],
                "source_url": mydar_product["source_url"]
            })
        
        return {
            "total_found": len(products),
            "preview_count": len(preview_products),
            "estimated_total": 737,  # Based on Telesys website
            "products": preview_products
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du scraping: {str(e)}")


@router.delete("/products/source/{source}")
async def delete_imported_products(
    source: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete all products imported from a specific source
    
    Admin only.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    result = await db.products.delete_many({"source": source})
    
    return {
        "status": "success",
        "deleted_count": result.deleted_count,
        "source": source
    }


@router.get("/products/count")
async def get_products_count_by_source(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get product count grouped by source"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    results = await db.products.aggregate(pipeline).to_list(100)
    
    total = sum(r["count"] for r in results)
    
    return {
        "total": total,
        "by_source": {r["_id"] or "manual": r["count"] for r in results}
    }


@router.post("/somef", response_model=dict)
async def start_somef_import(
    background_tasks: BackgroundTasks,
    with_details: bool = True,
    update_existing: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Start importing products from SOMEF website (somef.tn)
    
    Admin only. Runs in background.
    Imports: interrupteurs, prises, plaques, domotique, vidéophonie, etc.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    if import_status["running"]:
        raise HTTPException(status_code=400, detail="Un import est déjà en cours")
    
    # Start background task
    background_tasks.add_task(
        run_import_task,
        db,
        "somef",
        "SOMEF",
        None,  # max_pages not applicable for SOMEF
        with_details,
        update_existing
    )
    
    return {
        "status": "started",
        "message": "Import SOMEF démarré en arrière-plan. Utilisez GET /import/status pour suivre la progression.",
        "categories_count": len(SOMEF_CATEGORIES)
    }


@router.get("/somef/categories")
async def get_somef_categories(
    current_user: User = Depends(get_current_user)
):
    """Get list of SOMEF categories that will be scraped"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    return {
        "categories": [
            {
                "name": cat["name"],
                "system": cat.get("system", ""),
                "url": f"https://www.somef.tn{cat['url']}"
            }
            for cat in SOMEF_CATEGORIES
        ],
        "total_categories": len(SOMEF_CATEGORIES)
    }



@router.post("/tus", response_model=dict)
async def start_tus_import(
    background_tasks: BackgroundTasks,
    with_details: bool = True,
    update_existing: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Start importing products from TUS website (tus.com.tn)
    
    Admin only. Runs in background.
    Imports: Vidéosurveillance (Dahua), Contrôle d'accès (ZKTeco), Réseaux (Ruijie), Alarme, Smart Home
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    if import_status["running"]:
        raise HTTPException(status_code=400, detail="Un import est déjà en cours")
    
    # Start background task
    background_tasks.add_task(
        run_import_task,
        db,
        "tus",
        "TUS",
        None,  # max_pages not applicable for TUS
        with_details,
        update_existing
    )
    
    return {
        "status": "started",
        "message": "Import TUS démarré en arrière-plan. Utilisez GET /import/status pour suivre la progression.",
        "categories_count": len(TUS_CATEGORIES)
    }


@router.get("/tus/categories")
async def get_tus_categories(
    current_user: User = Depends(get_current_user)
):
    """Get list of TUS categories that will be scraped"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    return {
        "categories": [
            {
                "name": cat["name"],
                "brand": cat.get("brand", ""),
                "url": f"https://tus.com.tn{cat['url']}"
            }
            for cat in TUS_CATEGORIES
        ],
        "total_categories": len(TUS_CATEGORIES)
    }



@router.post("/somfy", response_model=dict)
async def start_somfy_import(
    background_tasks: BackgroundTasks,
    with_details: bool = True,
    update_existing: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Start importing products from Somfy website (somfy.tn)
    
    Admin only. Runs in background.
    Imports: Motorisation volets, stores, portails, garage, domotique Somfy
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    if import_status["running"]:
        raise HTTPException(status_code=400, detail="Un import est déjà en cours")
    
    # Start background task
    background_tasks.add_task(
        run_import_task,
        db,
        "somfy",
        "Somfy",
        None,
        with_details,
        update_existing
    )
    
    return {
        "status": "started",
        "message": "Import Somfy démarré en arrière-plan. Utilisez GET /import/status pour suivre la progression.",
        "categories_count": len(SOMFY_CATEGORIES)
    }


@router.get("/somfy/categories")
async def get_somfy_categories(
    current_user: User = Depends(get_current_user)
):
    """Get list of Somfy categories that will be scraped"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    return {
        "categories": [
            {
                "name": cat["name"],
                "type": cat.get("type", ""),
                "url": f"https://www.somfy.tn{cat['url']}"
            }
            for cat in SOMFY_CATEGORIES
        ],
        "total_categories": len(SOMFY_CATEGORIES)
    }


# Import enrichment service
from services.product_enrichment import enrich_all_products, get_category_stats, MASTER_CATEGORIES

# Enrichment status
enrichment_status = {
    "running": False,
    "progress": 0,
    "total": 0,
    "message": ""
}


@router.post("/enrich", response_model=dict)
async def start_product_enrichment(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Start product data enrichment process
    
    Analyzes all products and updates:
    - Categories (normalized to master taxonomy)
    - Brands (detected from product names/descriptions)
    - Technologies (WiFi, Zigbee, RTS, etc.)
    
    Admin only. Runs in background.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    if enrichment_status["running"]:
        raise HTTPException(status_code=400, detail="Un enrichissement est déjà en cours")
    
    async def run_enrichment():
        global enrichment_status
        enrichment_status["running"] = True
        enrichment_status["message"] = "Enrichissement en cours..."
        
        try:
            stats = await enrich_all_products(db)
            enrichment_status["message"] = f"Terminé ! {stats['updated']} produits mis à jour"
            enrichment_status["progress"] = stats["total"]
            enrichment_status["total"] = stats["total"]
        except Exception as e:
            enrichment_status["message"] = f"Erreur: {str(e)}"
            logger.error(f"Enrichment error: {e}")
        finally:
            enrichment_status["running"] = False
    
    background_tasks.add_task(run_enrichment)
    
    return {
        "status": "started",
        "message": "Enrichissement démarré en arrière-plan. Utilisez GET /import/enrich/status pour suivre la progression."
    }


@router.get("/enrich/status")
async def get_enrichment_status(
    current_user: User = Depends(get_current_user)
):
    """Get the current enrichment status"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    return enrichment_status


@router.get("/categories/master")
async def get_master_categories(
    current_user: User = Depends(get_current_user)
):
    """Get the master category taxonomy"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    return {
        "categories": [
            {
                "name": cat_name,
                "subcategories": cat_data.get("subcategories", []),
                "keywords_count": len(cat_data.get("keywords", []))
            }
            for cat_name, cat_data in MASTER_CATEGORIES.items()
        ],
        "total": len(MASTER_CATEGORIES)
    }


@router.get("/stats/detailed")
async def get_detailed_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get detailed product statistics (categories, brands, technologies)"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    stats = await get_category_stats(db)
    return stats



# Image migration status
image_migration_status = {
    "running": False,
    "total": 0,
    "success": 0,
    "failed": 0,
    "skipped": 0,
    "already_local": 0,
    "message": "",
    "started_at": None,
    "completed_at": None
}


async def run_image_migration_task(db: AsyncIOMotorDatabase, limit: int = None):
    """Background task to migrate images"""
    global image_migration_status
    import aiohttp
    import hashlib
    from pathlib import Path
    
    PRODUCTS_DIR = Path("/app/uploads/products")
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    
    image_migration_status = {
        "running": True,
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "already_local": 0,
        "message": "Démarrage...",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    
    try:
        # Count products to process
        query = {
            "primary_image_url": {"$regex": "^http", "$ne": None}
        }
        
        total = await db.products.count_documents(query)
        if limit:
            total = min(total, limit)
        
        image_migration_status["total"] = total
        image_migration_status["message"] = f"Migration de {total} images..."
        
        # Process products
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        async with aiohttp.ClientSession(connector=connector) as session:
            cursor = db.products.find(query)
            if limit:
                cursor = cursor.limit(limit)
            
            processed = 0
            async for product in cursor:
                product_id = product.get('id', str(product.get('_id', '')))
                primary_url = product.get('primary_image_url')
                
                if not primary_url:
                    image_migration_status["skipped"] += 1
                    continue
                
                if primary_url.startswith('/api/upload'):
                    image_migration_status["already_local"] += 1
                    continue
                
                try:
                    # Download image
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'image/*'
                    }
                    
                    async with session.get(primary_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status != 200:
                            image_migration_status["failed"] += 1
                            continue
                        
                        content = await response.read()
                        
                        if len(content) < 100:
                            image_migration_status["failed"] += 1
                            continue
                        
                        # Determine extension
                        url_path = primary_url.split('?')[0]
                        ext = Path(url_path).suffix.lower()
                        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                            ext = '.jpg'
                        
                        # Generate filename
                        url_hash = hashlib.md5(primary_url.encode()).hexdigest()[:8]
                        filename = f"{product_id}_{url_hash}{ext}"
                        file_path = PRODUCTS_DIR / filename
                        
                        # Save file
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                        # Update product
                        local_url = f"/api/upload/products/{filename}"
                        await db.products.update_one(
                            {"id": product_id},
                            {"$set": {
                                "primary_image_url": local_url,
                                "image_url": local_url,
                                "image": local_url,
                                "original_image_url": primary_url,
                                "image_migrated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        
                        image_migration_status["success"] += 1
                        
                except asyncio.TimeoutError:
                    image_migration_status["failed"] += 1
                except Exception as e:
                    logger.error(f"Error migrating image for {product_id}: {e}")
                    image_migration_status["failed"] += 1
                
                processed += 1
                if processed % 50 == 0:
                    image_migration_status["message"] = f"Progression: {processed}/{total} ({(processed/total*100):.1f}%)"
                
                # Rate limiting
                if processed % 20 == 0:
                    await asyncio.sleep(0.5)
        
        image_migration_status["message"] = "Migration terminée!"
        image_migration_status["completed_at"] = datetime.now(timezone.utc).isoformat()
        
    except Exception as e:
        logger.error(f"Image migration error: {e}")
        image_migration_status["message"] = f"Erreur: {str(e)}"
    finally:
        image_migration_status["running"] = False


@router.post("/images/migrate")
async def start_image_migration(
    background_tasks: BackgroundTasks,
    limit: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Start migrating product images from external URLs to local storage
    
    Admin only. Downloads all product images and stores them locally.
    - limit: Optional limit on number of products to process
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    if image_migration_status["running"]:
        raise HTTPException(status_code=400, detail="Une migration est déjà en cours")
    
    # Count products with external images
    query = {"primary_image_url": {"$regex": "^http", "$ne": None}}
    total = await db.products.count_documents(query)
    
    # Start background task
    background_tasks.add_task(run_image_migration_task, db, limit)
    
    return {
        "status": "started",
        "message": "Migration des images démarrée en arrière-plan",
        "total_to_process": min(total, limit) if limit else total,
        "endpoint_status": "/api/import/images/status"
    }


@router.get("/images/status")
async def get_image_migration_status(
    current_user: User = Depends(get_current_user)
):
    """Get current image migration status"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    return image_migration_status


@router.get("/images/stats")
async def get_image_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get statistics about product images"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    
    # Count by image type
    external_count = await db.products.count_documents({
        "primary_image_url": {"$regex": "^http"}
    })
    
    local_count = await db.products.count_documents({
        "primary_image_url": {"$regex": "^/api/upload"}
    })
    
    no_image_count = await db.products.count_documents({
        "$or": [
            {"primary_image_url": None},
            {"primary_image_url": ""}
        ]
    })
    
    migrated_count = await db.products.count_documents({
        "image_migrated_at": {"$exists": True}
    })
    
    return {
        "external_images": external_count,
        "local_images": local_count,
        "no_images": no_image_count,
        "migrated": migrated_count,
        "total": external_count + local_count + no_image_count
    }

