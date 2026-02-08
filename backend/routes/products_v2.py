"""
Products API - v2 Gemini2 Schema
Endpoints for product listing with hierarchical category filtering
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from enum import Enum
from datetime import datetime, timezone
import os
import re
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/products", tags=["Products"])

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ============ SUBCATEGORY PRIORITY SYSTEM ============
# Lower number = higher priority (appears first)
# Accessories always have highest number (appear last)
SUBCATEGORY_PRIORITY = {
    # Vidéosurveillance: Caméras -> Enregistreurs -> Stockage -> Accessoires
    "Caméras": 1,
    "Enregistreurs": 2,
    "Stockage": 3,
    "Accessoires vidéosurveillance": 99,
    
    # Alarme: Centrales -> Détecteurs -> Claviers -> Sirènes -> Modules -> Télécommandes -> Accessoires
    "Centrales d'alarme": 1,
    "Détecteurs & Contacts": 2,
    "Claviers": 3,
    "Sirènes": 4,
    "Modules de communication": 5,
    "Télécommandes": 6,
    "Accessoires alarme": 99,
    
    # Contrôle d'Accès: Lecteurs -> Badges -> Accessoires
    "Lecteurs": 1,
    "Badges & Tags": 2,
    "Serrures & Gâches": 3,
    "Accessoires contrôle d'accès": 99,
    
    # Vidéophonie: Platines -> Moniteurs -> Kits -> Accessoires
    "Platines de rue": 1,
    "Moniteurs": 2,
    "Kits": 3,
    "Accessoires vidéophonie": 99,
    
    # Domotique: Box -> Modules -> Capteurs -> Accessoires
    "Box & Passerelles": 1,
    "Modules": 2,
    "Capteurs": 3,
    "Accessoires domotique": 99,
    
    # Réseau: Routeurs -> Switches -> Points d'accès -> PoE -> Modules -> Accessoires
    "Routeurs": 1,
    "Switches": 2,
    "Points d'accès": 3,
    "PoE & Alimentation": 4,
    "Modules & Cartes": 5,
    "Accessoires réseau": 99,
    
    # Incendie: Détecteurs -> Sirènes -> Accessoires
    "Détecteurs": 1,
    "Accessoires incendie": 99,
    
    # Éclairage: Sources -> Accessoires
    "Sources lumineuses": 1,
    "Accessoires éclairage": 99,
    
    # Default for unlisted subcategories
    "Interrupteurs": 1,
    "Prises": 1,
    "Moteurs": 1,
    "Appareillage": 1,
    "Coffrets & Tableaux": 1,
}

def get_subcategory_priority(subcategory: str) -> int:
    """Get priority for subcategory. Lower = appears first. Accessories always last (99)."""
    if not subcategory:
        return 50
    # Check if it's an accessory (always last)
    if "accessoire" in subcategory.lower():
        return 99
    return SUBCATEGORY_PRIORITY.get(subcategory, 50)


class SortOption(str, Enum):
    RECENT = "recent"
    OLDEST = "oldest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    POPULAR = "popular"
    QUALITY = "quality"


def get_sort_config(sort: SortOption):
    """Get sort field and direction"""
    configs = {
        SortOption.RECENT: [("created_at", -1), ("_id", -1)],
        SortOption.OLDEST: [("created_at", 1), ("_id", 1)],
        SortOption.PRICE_ASC: [("price", 1), ("_id", 1)],
        SortOption.PRICE_DESC: [("price", -1), ("_id", -1)],
        SortOption.NAME_ASC: [("name", 1), ("_id", 1)],
        SortOption.NAME_DESC: [("name", -1), ("_id", -1)],
        SortOption.POPULAR: [("featured", -1), ("ranking.quality_score", -1), ("_id", -1)],
        SortOption.QUALITY: [("ranking.quality_score", -1), ("_id", -1)],
    }
    return configs.get(sort, [("ranking.quality_score", -1), ("_id", -1)])


@router.get("")
async def get_products(
    # Search
    q: Optional[str] = Query(None, description="Search query (name, keywords)"),
    
    # Category filters (NEW v2)
    category_id: Optional[str] = Query(None, description="Filter by exact category ID (leaf category)"),
    category: Optional[str] = Query(None, description="Filter by category path (includes subcategories)"),
    subcategory_id: Optional[str] = Query(None, description="Alias for category_id (subcategory filter)"),
    
    # Facet filters (NEW v2)
    connectivity: Optional[str] = Query(None, description="Filter by connectivity (Filaire, WiFi, Hybride)"),
    technologies: Optional[List[str]] = Query(None, description="Filter by technologies"),
    technology: Optional[str] = Query(None, description="Single technology filter (legacy)"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    
    # Price filters
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    
    # Image filter
    has_image: Optional[bool] = Query(None, description="Filter by image presence"),
    include_no_image: bool = Query(False, description="Include products without images"),
    
    # Sorting
    sort: Optional[SortOption] = Query(SortOption.QUALITY, description="Sort order"),
    
    # Pagination (both modes supported)
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(24, ge=1, le=100, description="Items per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (alternative to page)")
):
    """
    Get products with v2 hierarchical category filtering.
    
    Category filtering:
    - category: Filters by category_path_ids (includes all subcategories)
    - category_id / subcategory_id: Filters by exact category_id (leaf category only)
    
    Example: 
    - /products?category=videosurveillance → All video surveillance products
    - /products?category_id=videosurveillance__cameras-ip → Only IP cameras
    """
    
    # Handle cursor-based pagination
    if cursor and cursor.startswith("page_"):
        try:
            page = int(cursor.replace("page_", ""))
        except ValueError:
            page = 1
    
    # Build query
    query = {"active": True}
    
    # Image filter
    if has_image is not None:
        if has_image:
            query["image_missing"] = False
        else:
            query["image_missing"] = True
    elif not include_no_image:
        query["image_missing"] = False
    
    # Category filter (hierarchical) - support both old and new format
    if category:
        # v2: category is now a path ID like "videosurveillance"
        query["$or"] = [
            {"category_path_ids": category},
            {"category": {"$regex": category, "$options": "i"}}  # Legacy support
        ]
    elif category_id or subcategory_id:
        cat_id = category_id or subcategory_id
        query["$or"] = [
            {"category_id": cat_id},
            {"category": {"$regex": cat_id.replace("__", " ").replace("-", " "), "$options": "i"}}
        ]
    
    # Facet filters
    if connectivity:
        # Map common terms to DB values
        conn_map = {
            "wifi": "Sans fil",
            "WiFi": "Sans fil", 
            "sans fil": "Sans fil",
            "filaire": "Filaire",
            "Filaire": "Filaire",
            "hybride": "Hybride",
            "Hybride": "Hybride"
        }
        conn_value = conn_map.get(connectivity, connectivity)
        query["attributes_norm.connectivity"] = conn_value
    
    # Handle both technologies (list) and technology (single) params
    tech_list = technologies or ([technology] if technology else None)
    if tech_list:
        query["$or"] = query.get("$or", []) + [
            {"attributes_norm.technologies": {"$in": tech_list}},
            {"technologies": {"$in": tech_list}}  # Legacy field
        ]
    
    if brand:
        query["brand"] = {"$regex": f"^{re.escape(brand)}$", "$options": "i"}
    
    # Price filter
    if price_min is not None or price_max is not None:
        price_query = {}
        if price_min is not None:
            price_query["$gte"] = price_min
        if price_max is not None:
            price_query["$lte"] = price_max
        if price_query:
            query["price"] = price_query
    
    # Text search with smart ranking
    if q:
        search_term = q.strip()
        
        # Build search query - include model_code
        query["$or"] = query.get("$or", []) + [
            {"model_code": {"$regex": search_term, "$options": "i"}},
            {"sku": {"$regex": search_term, "$options": "i"}},
            {"name": {"$regex": search_term, "$options": "i"}},
            {"search.keywords": {"$regex": search_term, "$options": "i"}},
            {"brand": {"$regex": search_term, "$options": "i"}},
            {"description": {"$regex": search_term, "$options": "i"}}
        ]
        
        # Use aggregation for smart relevance scoring
        # Count total first
        total = await db.products.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total + limit - 1) // limit
        
        # Aggregation pipeline with relevance scoring
        pipeline = [
            {"$match": query},
            {"$addFields": {
                "relevance_score": {
                    "$add": [
                        # Exact SKU match = highest priority (100 points)
                        {"$cond": [
                            {"$regexMatch": {"input": {"$ifNull": ["$sku", ""]}, "regex": f"^{re.escape(search_term)}$", "options": "i"}},
                            100, 0
                        ]},
                        # SKU contains search term (50 points)
                        {"$cond": [
                            {"$regexMatch": {"input": {"$ifNull": ["$sku", ""]}, "regex": re.escape(search_term), "options": "i"}},
                            50, 0
                        ]},
                        # Name starts with search term (40 points)
                        {"$cond": [
                            {"$regexMatch": {"input": {"$ifNull": ["$name", ""]}, "regex": f"^{re.escape(search_term)}", "options": "i"}},
                            40, 0
                        ]},
                        # Name contains search term (30 points)
                        {"$cond": [
                            {"$regexMatch": {"input": {"$ifNull": ["$name", ""]}, "regex": re.escape(search_term), "options": "i"}},
                            30, 0
                        ]},
                        # Brand exact match (20 points)
                        {"$cond": [
                            {"$regexMatch": {"input": {"$ifNull": ["$brand", ""]}, "regex": f"^{re.escape(search_term)}$", "options": "i"}},
                            20, 0
                        ]},
                        # Keywords match (10 points)
                        {"$cond": [
                            {"$in": [search_term.lower(), {"$ifNull": ["$search.keywords", []]}]},
                            10, 0
                        ]},
                        # Quality score bonus (0-10 points)
                        {"$multiply": [{"$ifNull": ["$ranking.quality_score", 0]}, 0.1]}
                    ]
                }
            }},
            {"$sort": {"relevance_score": -1, "ranking.quality_score": -1, "_id": 1}},
            {"$skip": skip},
            {"$limit": limit},
            {"$project": {"relevance_score": 0}}  # Remove internal field
        ]
        
        products = await db.products.aggregate(pipeline).to_list(limit)
        
        # Remove MongoDB _id from results
        for p in products:
            if "_id" in p:
                del p["_id"]
    else:
        # No search term - use standard query with subcategory priority
        # Count total
        total = await db.products.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total + limit - 1) // limit
        
        # Check if filtering by category - use subcategory priority sorting
        if category or category_id or subcategory_id:
            # Use aggregation for subcategory priority sorting
            pipeline = [
                {"$match": query},
                {"$addFields": {
                    "subcategory_priority": {
                        "$switch": {
                            "branches": [
                                # Vidéosurveillance order
                                {"case": {"$eq": ["$subcategory_label", "Caméras"]}, "then": 1},
                                {"case": {"$eq": ["$subcategory_label", "Enregistreurs"]}, "then": 2},
                                {"case": {"$eq": ["$subcategory_label", "Stockage"]}, "then": 3},
                                {"case": {"$eq": ["$subcategory_label", "Accessoires vidéosurveillance"]}, "then": 99},
                                
                                # Alarme order
                                {"case": {"$eq": ["$subcategory_label", "Centrales d'alarme"]}, "then": 1},
                                {"case": {"$eq": ["$subcategory_label", "Détecteurs & Contacts"]}, "then": 2},
                                {"case": {"$eq": ["$subcategory_label", "Claviers"]}, "then": 3},
                                {"case": {"$eq": ["$subcategory_label", "Sirènes"]}, "then": 4},
                                {"case": {"$eq": ["$subcategory_label", "Modules de communication"]}, "then": 5},
                                {"case": {"$eq": ["$subcategory_label", "Télécommandes"]}, "then": 6},
                                {"case": {"$eq": ["$subcategory_label", "Accessoires alarme"]}, "then": 99},
                                
                                # Contrôle d'Accès order
                                {"case": {"$eq": ["$subcategory_label", "Lecteurs"]}, "then": 1},
                                {"case": {"$eq": ["$subcategory_label", "Badges & Tags"]}, "then": 2},
                                {"case": {"$eq": ["$subcategory_label", "Serrures & Gâches"]}, "then": 3},
                                {"case": {"$eq": ["$subcategory_label", "Accessoires contrôle d'accès"]}, "then": 99},
                                
                                # Vidéophonie order
                                {"case": {"$eq": ["$subcategory_label", "Platines de rue"]}, "then": 1},
                                {"case": {"$eq": ["$subcategory_label", "Moniteurs"]}, "then": 2},
                                {"case": {"$eq": ["$subcategory_label", "Kits"]}, "then": 3},
                                {"case": {"$eq": ["$subcategory_label", "Accessoires vidéophonie"]}, "then": 99},
                                
                                # Domotique order
                                {"case": {"$eq": ["$subcategory_label", "Box & Passerelles"]}, "then": 1},
                                {"case": {"$eq": ["$subcategory_label", "Modules"]}, "then": 2},
                                {"case": {"$eq": ["$subcategory_label", "Capteurs"]}, "then": 3},
                                {"case": {"$eq": ["$subcategory_label", "Accessoires domotique"]}, "then": 99},
                                
                                # Réseau order
                                {"case": {"$eq": ["$subcategory_label", "Routeurs"]}, "then": 1},
                                {"case": {"$eq": ["$subcategory_label", "Switches"]}, "then": 2},
                                {"case": {"$eq": ["$subcategory_label", "Points d'accès"]}, "then": 3},
                                {"case": {"$eq": ["$subcategory_label", "PoE & Alimentation"]}, "then": 4},
                                {"case": {"$eq": ["$subcategory_label", "Modules & Cartes"]}, "then": 5},
                                {"case": {"$eq": ["$subcategory_label", "Accessoires réseau"]}, "then": 99},
                                
                                # Incendie order
                                {"case": {"$eq": ["$subcategory_label", "Détecteurs"]}, "then": 1},
                                {"case": {"$eq": ["$subcategory_label", "Accessoires incendie"]}, "then": 99},
                                
                                # Éclairage order
                                {"case": {"$eq": ["$subcategory_label", "Sources lumineuses"]}, "then": 1},
                                {"case": {"$eq": ["$subcategory_label", "Accessoires éclairage"]}, "then": 99},
                                
                                # Generic accessory detection (always last)
                                {"case": {"$regexMatch": {"input": {"$ifNull": ["$subcategory_label", ""]}, "regex": "accessoire", "options": "i"}}, "then": 99},
                            ],
                            "default": 50  # Default priority for unlisted subcategories
                        }
                    }
                }},
                {"$sort": {"subcategory_priority": 1, "ranking.quality_score": -1, "_id": 1}},
                {"$skip": skip},
                {"$limit": limit},
                {"$project": {"subcategory_priority": 0}}  # Remove internal field
            ]
            
            products = await db.products.aggregate(pipeline).to_list(limit)
            
            # Remove MongoDB _id from results
            for p in products:
                if "_id" in p:
                    del p["_id"]
        else:
            # No category filter - use standard sorting
            sort_config = get_sort_config(sort)
            
            products = await db.products.find(
                query,
                {"_id": 0}
            ).sort(sort_config).skip(skip).limit(limit).to_list(limit)
    
    # Format response with both v2 structure and legacy compatibility
    # Legacy format for existing frontend
    response = {
        # V2 format
        "products": products,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_more": page < total_pages,
        
        # Legacy format for existing frontend compatibility
        "items": products,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": page < total_pages,
            "next_cursor": f"page_{page + 1}" if page < total_pages else None
        }
    }
    
    return response


@router.get("/facets")
async def get_product_facets(
    category: Optional[str] = Query(None, description="Category to get facets for"),
    category_id: Optional[str] = Query(None, description="Exact category ID")
):
    """
    Get available facets (filters) for a category.
    Returns unique values for connectivity, technologies, brands.
    """
    query = {"active": True, "image_missing": False}
    
    if category:
        query["category_path_ids"] = category
    elif category_id:
        query["category_id"] = category_id
    
    # Get distinct values using aggregation
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "connectivities": {"$addToSet": "$attributes_norm.connectivity"},
            "brands": {"$addToSet": "$brand"},
            "technologies": {"$push": "$attributes_norm.technologies"}
        }}
    ]
    
    result = await db.products.aggregate(pipeline).to_list(1)
    
    if not result:
        return {
            "connectivities": [],
            "technologies": [],
            "brands": []
        }
    
    data = result[0]
    
    # Flatten technologies array
    all_technologies = set()
    for tech_list in data.get("technologies", []):
        if tech_list:
            all_technologies.update(tech_list)
    
    # Clean up None values
    connectivities = [c for c in data.get("connectivities", []) if c]
    brands = [b for b in data.get("brands", []) if b]
    
    return {
        "connectivities": sorted(connectivities),
        "technologies": sorted(list(all_technologies)),
        "brands": sorted(brands)
    }


@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Max results")
):
    """
    Full-text search with smart relevance ranking.
    Prioritizes: Exact SKU > SKU contains > Name starts with > Name contains > Brand > Keywords
    """
    search_term = q.strip()
    
    # Base query
    base_query = {
        "active": True,
        "image_missing": False,
        "$or": [
            {"sku": {"$regex": search_term, "$options": "i"}},
            {"name": {"$regex": search_term, "$options": "i"}},
            {"search.keywords": {"$regex": search_term, "$options": "i"}},
            {"brand": {"$regex": search_term, "$options": "i"}}
        ]
    }
    
    # Aggregation pipeline with smart relevance scoring
    pipeline = [
        {"$match": base_query},
        {"$addFields": {
            "relevance_score": {
                "$add": [
                    # Exact SKU match = highest priority (100 points)
                    {"$cond": [
                        {"$regexMatch": {"input": {"$ifNull": ["$sku", ""]}, "regex": f"^{re.escape(search_term)}$", "options": "i"}},
                        100, 0
                    ]},
                    # SKU contains search term (50 points)
                    {"$cond": [
                        {"$regexMatch": {"input": {"$ifNull": ["$sku", ""]}, "regex": re.escape(search_term), "options": "i"}},
                        50, 0
                    ]},
                    # Name starts with search term (40 points)
                    {"$cond": [
                        {"$regexMatch": {"input": {"$ifNull": ["$name", ""]}, "regex": f"^{re.escape(search_term)}", "options": "i"}},
                        40, 0
                    ]},
                    # Name contains search term (30 points)
                    {"$cond": [
                        {"$regexMatch": {"input": {"$ifNull": ["$name", ""]}, "regex": re.escape(search_term), "options": "i"}},
                        30, 0
                    ]},
                    # Brand exact match (20 points)
                    {"$cond": [
                        {"$regexMatch": {"input": {"$ifNull": ["$brand", ""]}, "regex": f"^{re.escape(search_term)}$", "options": "i"}},
                        20, 0
                    ]},
                    # Quality score bonus (0-10 points)
                    {"$multiply": [{"$ifNull": ["$ranking.quality_score", 0]}, 0.1]}
                ]
            }
        }},
        {"$sort": {"relevance_score": -1, "ranking.quality_score": -1}},
        {"$limit": limit},
        {"$project": {"relevance_score": 0}}
    ]
    
    products = await db.products.aggregate(pipeline).to_list(limit)
    
    # Remove MongoDB _id from results
    for p in products:
        if "_id" in p:
            del p["_id"]
    
    return {
        "query": q,
        "products": products,
        "total": len(products)
    }




@router.get("/by-category/{category_id}")
async def get_products_by_category(
    category_id: str,
    include_subcategories: bool = Query(True, description="Include products from subcategories"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100)
):
    """
    Get products for a specific category.
    If include_subcategories=True, returns all products in category tree.
    """
    query = {"active": True, "image_missing": False}
    
    if include_subcategories:
        query["category_path_ids"] = category_id
    else:
        query["category_id"] = category_id
    
    total = await db.products.count_documents(query)
    skip = (page - 1) * limit
    
    products = await db.products.find(
        query,
        {"_id": 0}
    ).sort([("ranking.quality_score", -1)]).skip(skip).limit(limit).to_list(limit)
    
    # Get category info
    category = await db.categories.find_one({"_id": category_id})
    
    return {
        "category": {
            "id": category_id,
            "label": category["label"] if category else category_id
        },
        "products": products,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }


# ============ LEGACY COMPATIBILITY ENDPOINTS ============

@router.get("/brands/list")
async def get_brands_list():
    """Get list of all unique brands (legacy endpoint)"""
    brands = await db.products.distinct("brand", {"active": True, "brand": {"$ne": None}})
    return sorted([b for b in brands if b])


@router.get("/technologies/list")
async def get_technologies_list():
    """Get list of all unique technologies (legacy endpoint)"""
    # Get from attributes_norm.technologies
    pipeline = [
        {"$match": {"active": True}},
        {"$unwind": {"path": "$attributes_norm.technologies", "preserveNullAndEmptyArrays": False}},
        {"$group": {"_id": "$attributes_norm.technologies"}},
        {"$sort": {"_id": 1}}
    ]
    result = await db.products.aggregate(pipeline).to_list(None)
    return [r["_id"] for r in result if r["_id"]]


@router.get("/price-range")
async def get_price_range():
    """Get min and max prices (legacy endpoint)"""
    pipeline = [
        {"$match": {"active": True, "price": {"$gt": 0}}},
        {"$group": {
            "_id": None,
            "min": {"$min": "$price"},
            "max": {"$max": "$price"}
        }}
    ]
    result = await db.products.aggregate(pipeline).to_list(1)
    if result:
        return {"min": result[0]["min"], "max": result[0]["max"]}
    return {"min": 0, "max": 10000}


@router.get("/{product_id}")
async def get_product(product_id: str):
    """
    Get a single product by ID
    """
    # Chercher par le champ 'id' (pas _id)
    product = await db.products.find_one(
        {"id": product_id},
        {"_id": 0}
    )
    
    if not product:
        # Try by slug
        product = await db.products.find_one(
            {"slug": product_id},
            {"_id": 0}
        )
    
    if not product:
        # Try by model_code
        product = await db.products.find_one(
            {"model_code": {"$regex": f"^{product_id}$", "$options": "i"}},
            {"_id": 0}
        )
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get category info
    if product.get("category_id"):
        category = await db.categories.find_one(
            {"_id": product["category_id"]},
            {"label": 1, "slug": 1, "path_ids": 1}
        )
        if category:
            product["category_info"] = {
                "id": product["category_id"],
                "label": category["label"],
                "slug": category["slug"],
                "path_ids": category.get("path_ids", [])
            }
    
    # Get related products (same category, different product)
    related = await db.products.find(
        {
            "category_id": product.get("category_id"),
            "id": {"$ne": product.get("id")},
            "active": True,
            "image_missing": False
        },
        {"_id": 0, "id": 1, "name": 1, "price": 1, "primary_image_url": 1, "brand": 1}
    ).sort([("ranking.quality_score", -1)]).limit(6).to_list(6)
    
    product["related_products"] = related
    
    return product

