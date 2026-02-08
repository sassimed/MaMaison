"""
Data Migration API for MyDar
Exports and imports shop data (products, categories) for production deployment
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils.dependencies import get_db
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import os

router = APIRouter(prefix="/data-migration", tags=["Data Migration"])

# Secret key for secure operations
MIGRATION_SECRET = os.environ.get("MIGRATION_SECRET", "mydar2024migrate")


class ImportDataRequest(BaseModel):
    secret_key: str
    products: List[dict]
    categories: List[dict]


@router.get("/export/shop-data/{secret_key}")
async def export_shop_data(secret_key: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Export all shop data (products, categories) for migration to production.
    Returns JSON with all products and categories.
    """
    if secret_key != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    try:
        # Export products (only those with images for production)
        products = await db.products.find(
            {"image": {"$exists": True, "$ne": None, "$ne": ""}},
            {"_id": 0}
        ).to_list(5000)
        
        # Export categories
        categories = await db.categories.find({}, {"_id": 0}).to_list(100)
        
        # Get unique brands from products
        brands_pipeline = [
            {"$match": {"image": {"$exists": True, "$ne": None, "$ne": ""}}},
            {"$group": {"_id": "$brand", "count": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None, "$ne": ""}}},
            {"$sort": {"count": -1}}
        ]
        brands_result = await db.products.aggregate(brands_pipeline).to_list(100)
        brands = [{"name": b["_id"], "product_count": b["count"]} for b in brands_result]
        
        # Get unique technologies
        tech_pipeline = [
            {"$match": {"image": {"$exists": True, "$ne": None, "$ne": ""}}},
            {"$group": {"_id": "$technology", "count": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None, "$ne": ""}}},
            {"$sort": {"count": -1}}
        ]
        tech_result = await db.products.aggregate(tech_pipeline).to_list(50)
        technologies = [{"name": t["_id"], "product_count": t["count"]} for t in tech_result]
        
        return {
            "success": True,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "stats": {
                "products_count": len(products),
                "categories_count": len(categories),
                "brands_count": len(brands),
                "technologies_count": len(technologies)
            },
            "data": {
                "products": products,
                "categories": categories,
                "brands": brands,
                "technologies": technologies
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@router.post("/import/shop-data/{secret_key}")
async def import_shop_data(
    secret_key: str,
    data: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Import shop data (products, categories) from another environment.
    Use this endpoint on production to import data.
    """
    if secret_key != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    try:
        products = data.get("products", [])
        categories = data.get("categories", [])
        
        results = {
            "products_imported": 0,
            "products_updated": 0,
            "categories_imported": 0,
            "categories_updated": 0,
            "errors": []
        }
        
        # Import categories first
        for category in categories:
            try:
                existing = await db.categories.find_one({"slug": category.get("slug")})
                if existing:
                    await db.categories.update_one(
                        {"slug": category.get("slug")},
                        {"$set": category}
                    )
                    results["categories_updated"] += 1
                else:
                    await db.categories.insert_one(category)
                    results["categories_imported"] += 1
            except Exception as e:
                results["errors"].append(f"Category {category.get('name')}: {str(e)}")
        
        # Import products in batches
        batch_size = 100
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            for product in batch:
                try:
                    # Check if product exists by ID or SKU
                    existing = await db.products.find_one({
                        "$or": [
                            {"id": product.get("id")},
                            {"sku": product.get("sku")} if product.get("sku") else {"id": "none"}
                        ]
                    })
                    
                    if existing:
                        await db.products.update_one(
                            {"id": product.get("id")},
                            {"$set": product}
                        )
                        results["products_updated"] += 1
                    else:
                        await db.products.insert_one(product)
                        results["products_imported"] += 1
                        
                except Exception as e:
                    results["errors"].append(f"Product {product.get('name', 'unknown')[:30]}: {str(e)}")
        
        return {
            "success": True,
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")


@router.get("/seed/shop-data/{secret_key}")
async def seed_shop_data_from_source(
    secret_key: str,
    source_url: str,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Seed shop data by fetching from a source URL.
    This endpoint fetches data from another MyDar instance and imports it.
    
    Usage: GET /api/data-migration/seed/shop-data/{secret}?source_url=https://source-domain.com
    """
    if secret_key != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    import aiohttp
    
    try:
        # Fetch data from source
        export_url = f"{source_url}/api/data-migration/export/shop-data/{secret_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(export_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to fetch from source: {await response.text()}"
                    )
                
                export_data = await response.json()
        
        if not export_data.get("success"):
            raise HTTPException(status_code=500, detail="Source export failed")
        
        # Get the data
        data = export_data.get("data", {})
        products = data.get("products", [])
        categories = data.get("categories", [])
        
        results = {
            "products_imported": 0,
            "products_updated": 0,
            "products_skipped": 0,
            "categories_imported": 0,
            "categories_updated": 0,
            "errors": []
        }
        
        # Clear existing categories and insert new ones
        if categories:
            await db.categories.delete_many({})
            for category in categories:
                try:
                    await db.categories.insert_one(category)
                    results["categories_imported"] += 1
                except Exception as e:
                    results["errors"].append(f"Category error: {str(e)}")
        
        # Import products - update if exists, insert if new
        for product in products:
            try:
                product_id = product.get("id")
                if not product_id:
                    results["products_skipped"] += 1
                    continue
                
                existing = await db.products.find_one({"id": product_id})
                
                if existing:
                    await db.products.update_one(
                        {"id": product_id},
                        {"$set": product}
                    )
                    results["products_updated"] += 1
                else:
                    await db.products.insert_one(product)
                    results["products_imported"] += 1
                    
            except Exception as e:
                results["errors"].append(f"Product error: {str(e)[:50]}")
        
        return {
            "success": True,
            "seeded_at": datetime.now(timezone.utc).isoformat(),
            "source": source_url,
            "source_stats": export_data.get("stats", {}),
            "results": results
        }
        
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seed error: {str(e)}")


@router.delete("/clear/shop-data/{secret_key}")
async def clear_shop_data(secret_key: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Clear all shop data (products, categories) - USE WITH CAUTION!
    """
    if secret_key != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    try:
        products_deleted = await db.products.delete_many({})
        categories_deleted = await db.categories.delete_many({})
        
        return {
            "success": True,
            "cleared_at": datetime.now(timezone.utc).isoformat(),
            "deleted": {
                "products": products_deleted.deleted_count,
                "categories": categories_deleted.deleted_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear error: {str(e)}")


@router.get("/stats")
async def get_shop_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get current shop data statistics (public endpoint)
    """
    try:
        products_count = await db.products.count_documents({
            "image": {"$exists": True, "$ne": None, "$ne": ""}
        })
        products_no_image = await db.products.count_documents({
            "$or": [
                {"image": {"$exists": False}},
                {"image": None},
                {"image": ""}
            ]
        })
        categories_count = await db.categories.count_documents({})
        
        # Get brands count
        brands = await db.products.distinct("brand")
        brands = [b for b in brands if b]
        
        # Get technologies count
        technologies = await db.products.distinct("technology")
        technologies = [t for t in technologies if t]
        
        return {
            "products_with_image": products_count,
            "products_without_image": products_no_image,
            "total_products": products_count + products_no_image,
            "categories": categories_count,
            "brands": len(brands),
            "technologies": len(technologies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
