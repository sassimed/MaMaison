from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils.dependencies import get_db
from typing import Optional
from enum import Enum
from datetime import datetime

router = APIRouter(prefix="/products", tags=["Products"])


class SortOption(str, Enum):
    RECENT = "recent"
    OLDEST = "oldest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    POPULAR = "popular"


def get_sort_config(sort: SortOption):
    """Get sort field, direction, and cursor field for each sort option"""
    configs = {
        SortOption.RECENT: ("id", -1, "id"),  # Use id as proxy for recency (UUIDs are time-ordered)
        SortOption.OLDEST: ("id", 1, "id"),
        SortOption.PRICE_ASC: ("price", 1, "price"),
        SortOption.PRICE_DESC: ("price", -1, "price"),
        SortOption.NAME_ASC: ("name", 1, "name"),
        SortOption.NAME_DESC: ("name", -1, "name"),
        SortOption.POPULAR: ("is_featured", -1, "is_featured"),
    }
    return configs.get(sort, ("id", -1, "id"))


@router.get("")
async def get_products(
    # Search & filters
    q: Optional[str] = Query(None, description="Search query (name, description)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    technology: Optional[str] = Query(None, description="Filter by technology (WiFi, Zigbee)"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    # Image filter (admin only)
    has_image: Optional[bool] = Query(None, description="Filter by image presence (admin only)"),
    include_no_image: bool = Query(False, description="Include products without images (admin only)"),
    # Sorting
    sort: Optional[SortOption] = Query(SortOption.RECENT, description="Sort order"),
    # Cursor-based pagination
    cursor: Optional[str] = Query(None, description="Cursor for pagination (value|id)"),
    limit: int = Query(12, ge=1, le=50, description="Items per page"),
    # Database
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get products with advanced filtering, sorting and cursor-based pagination.
    
    Cursor format: "SORT_VALUE|ID" (e.g., "99.99|abc123" for price sort)
    This ensures stable pagination even when new products are added.
    
    SEO-friendly URL example: /api/products?q=camera&price_max=500&sort=price_asc
    
    By default, products without images are hidden. Use include_no_image=true for admin.
    Use has_image=false to get ONLY products without images (admin filter).
    """
    
    # Build base query for filters
    query = {}
    
    # By default, exclude products without images (unless admin requests otherwise)
    if has_image is not None:
        # Explicit filter: has_image=true or has_image=false
        if has_image:
            query["image"] = {"$exists": True, "$ne": None, "$ne": ""}
        else:
            # Get only products WITHOUT images
            query["$or"] = [
                {"image": {"$exists": False}},
                {"image": None},
                {"image": ""}
            ]
    elif not include_no_image:
        # Default: exclude products without images for public view
        query["image"] = {"$exists": True, "$ne": None, "$ne": ""}
    
    # Text search
    if q:
        text_search = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}}
        ]
        # If we already have an $or (for no-image filter), use $and to combine
        if "$or" in query:
            existing_or = query.pop("$or")
            query["$and"] = [
                {"$or": existing_or},
                {"$or": text_search}
            ]
        else:
            query["$or"] = text_search
    
    # Category filter
    if category:
        query["category"] = category
    
    # Technology filter
    if technology:
        query["technology"] = technology
    
    # Brand filter
    if brand:
        query["brand"] = brand
    
    # Price range filter
    if price_min is not None or price_max is not None:
        price_query = {}
        if price_min is not None:
            price_query["$gte"] = price_min
        if price_max is not None:
            price_query["$lte"] = price_max
        if price_query:
            query["price"] = price_query
    
    # Get sort configuration
    sort_field, sort_direction, cursor_field = get_sort_config(sort)
    
    # Apply cursor for stable pagination
    cursor_query = query.copy()
    if cursor:
        try:
            cursor_parts = cursor.split("|")
            cursor_value_str = cursor_parts[0]
            cursor_id = cursor_parts[1] if len(cursor_parts) > 1 else ""
            
            # Parse cursor value based on field type
            if cursor_field in ["price"]:
                cursor_value = float(cursor_value_str) if cursor_value_str else 0
            elif cursor_field in ["created_at"]:
                cursor_value = datetime.fromisoformat(cursor_value_str.replace('Z', '+00:00'))
            elif cursor_field in ["is_featured"]:
                cursor_value = cursor_value_str.lower() == "true"
            else:
                cursor_value = cursor_value_str
            
            # Build cursor condition based on sort direction
            if sort_direction == -1:  # Descending
                cursor_query["$or"] = [
                    {cursor_field: {"$lt": cursor_value}},
                    {cursor_field: cursor_value, "id": {"$lt": cursor_id}}
                ]
            else:  # Ascending
                cursor_query["$or"] = [
                    {cursor_field: {"$gt": cursor_value}},
                    {cursor_field: cursor_value, "id": {"$gt": cursor_id}}
                ]
        except Exception as e:
            # Invalid cursor, ignore and start from beginning
            pass
    
    # Get total count (without cursor for accurate total)
    total = await db.products.count_documents(query)
    
    # Fetch items with stable sort: sort_field + id for tie-breaking
    products = await db.products.find(
        cursor_query,
        {"_id": 0}
    ).sort([
        (sort_field, sort_direction),
        ("id", sort_direction)
    ]).limit(limit + 1).to_list(limit + 1)
    
    # Determine if there are more items
    has_more = len(products) > limit
    if has_more:
        products = products[:limit]
    
    # Build next cursor from the last item
    next_cursor = None
    if products and has_more:
        last_item = products[-1]
        last_value = last_item.get(cursor_field)
        
        # Format cursor value
        if last_value is not None:
            if hasattr(last_value, 'isoformat'):
                cursor_value_str = last_value.isoformat()
            elif isinstance(last_value, bool):
                cursor_value_str = str(last_value).lower()
            else:
                cursor_value_str = str(last_value)
            next_cursor = f"{cursor_value_str}|{last_item['id']}"
    
    return {
        "items": products,
        "pagination": {
            "cursor": cursor,
            "next_cursor": next_cursor,
            "limit": limit,
            "total": total,
            "has_more": has_more
        },
        "filters_applied": {
            "q": q,
            "category": category,
            "technology": technology,
            "brand": brand,
            "price_min": price_min,
            "price_max": price_max,
            "sort": sort
        }
    }


@router.get("/brands/list")
async def get_brands(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get list of unique brands"""
    brands = await db.products.distinct("brand")
    brands = [b for b in brands if b]
    brands.sort()
    return brands


@router.get("/price-range")
async def get_price_range(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get min and max product prices for filter sliders"""
    pipeline = [
        {"$match": {"price": {"$ne": None}}},
        {
            "$group": {
                "_id": None,
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"}
            }
        }
    ]
    result = await db.products.aggregate(pipeline).to_list(1)
    
    if result:
        return {
            "min": result[0].get("min_price", 0),
            "max": result[0].get("max_price", 1000)
        }
    return {"min": 0, "max": 1000}


@router.get("/technologies/list")
async def get_technologies(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get list of unique technologies"""
    technologies = await db.products.distinct("technology")
    technologies = [t for t in technologies if t]
    technologies.sort()
    return technologies


@router.get("/categories/list")
async def get_categories_with_count(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get list of categories with product counts (only products with images)"""
    pipeline = [
        {"$match": {"image": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = await db.products.aggregate(pipeline).to_list(100)
    return [{"name": r["_id"], "count": r["count"]} for r in result if r["_id"]]


@router.get("/stats/images")
async def get_image_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get statistics about products with/without images (admin)"""
    # Count products with images
    with_image = await db.products.count_documents({
        "image": {"$exists": True, "$ne": None, "$ne": ""}
    })
    
    # Count products without images
    without_image = await db.products.count_documents({
        "$or": [
            {"image": {"$exists": False}},
            {"image": None},
            {"image": ""}
        ]
    })
    
    # Get breakdown by source for products without images
    pipeline = [
        {"$match": {"$or": [
            {"image": {"$exists": False}},
            {"image": None},
            {"image": ""}
        ]}},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_source = await db.products.aggregate(pipeline).to_list(20)
    
    return {
        "total": with_image + without_image,
        "with_image": with_image,
        "without_image": without_image,
        "without_image_by_source": {r["_id"]: r["count"] for r in by_source}
    }


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a single product by ID"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product
