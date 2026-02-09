"""
Categories API - v2 Gemini2 Schema
Endpoints for hierarchical category navigation
With caching for improved performance
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Import cache utilities
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cache import cache, cached, CacheTTL

load_dotenv()

router = APIRouter(prefix="/categories", tags=["categories"])

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def serialize_id(value):
    """Convert ObjectId or any value to string"""
    if isinstance(value, ObjectId):
        return str(value)
    return value


async def _get_categories_cached(parent_id: Optional[str], include_children: bool):
    """Internal function to fetch categories - results are cached"""
    query = {}
    
    if parent_id is None or parent_id == "null":
        query["parent_id"] = None
    else:
        query["parent_id"] = parent_id
    
    categories = await db.categories.find(query).sort("label", 1).to_list(None)
    
    # Icon mapping for frontend compatibility
    icon_map = {
        "videosurveillance": "Camera",
        "alarme": "Bell",
        "controle-d-acces": "Lock",
        "videophonie": "Video",
        "incendie": "Flame",
        "interrupteur": "ToggleRight",
        "prise": "Plug",
        "plaque": "Box",
        "coffret-tableau": "Zap",
        "boite-monture": "Box",
        "eclairage": "Lightbulb",
        "domotique": "Home",
        "motorisation": "Settings",
        "reseau": "Router",
        "accessoire": "Package",
    }
    
    result = []
    for cat in categories:
        # Use slug as ID for frontend compatibility with products (products use slugs in category_path_ids)
        cat_slug = cat.get("slug", "")
        cat_label = cat.get("label", "")
        mongo_id = serialize_id(cat.get("id") or cat.get("_id"))
        
        # Get parent slug if parent exists
        parent_id = cat.get("parent_id")
        parent_slug = None
        if parent_id:
            parent_doc = await db.categories.find_one({"$or": [{"id": parent_id}, {"_id": parent_id}]})
            if parent_doc:
                parent_slug = parent_doc.get("slug")
        
        cat_data = {
            "id": cat_slug,  # Use slug as ID for product filtering compatibility
            "mongo_id": mongo_id,  # Keep original MongoDB ID for reference
            "label": cat_label,
            "name": cat_label,
            "slug": cat_slug,
            "parent_id": parent_slug,  # Use parent slug for consistency
            "level": cat.get("level", 1),
            "path_ids": cat.get("path_ids", [cat_slug]),
            "is_active": cat.get("is_active", True),
            "icon": icon_map.get(cat_slug, "Package"),
            "subcategories": []
        }
        
        if include_children:
            # Get subcategories by parent's MongoDB ID
            subcategories = await db.categories.find({
                "$or": [
                    {"parent_id": mongo_id},  # MongoDB ObjectId reference
                    {"parent_id": cat_slug}   # Slug reference (legacy)
                ],
                "is_active": True
            }).sort("label", 1).to_list(None)
            
            for sub in subcategories:
                sub_slug = sub.get("slug", "")
                cat_data["subcategories"].append({
                    "id": sub_slug,  # Use slug as ID
                    "label": sub.get("label", ""),
                    "slug": sub_slug,
                    "product_count": sub.get("product_count", 0)
                })
            
            cat_data["children_count"] = len(subcategories)
            cat_data["has_children"] = len(subcategories) > 0
            
            # Count products using slugs (matching product data structure)
            products_count = await db.products.count_documents({
                "active": True,
                "$or": [
                    {"category_path_ids": cat_slug},
                    {"category_id": {"$regex": f"^{cat_slug}", "$options": "i"}},
                    {"category": cat_label}
                ]
            })
            cat_data["products_count"] = products_count
            cat_data["product_count"] = products_count
        
        result.append(cat_data)
    
    return result


@router.get("")
async def get_categories(
    parent_id: Optional[str] = Query(None, description="Filter by parent category ID (null for root categories)"),
    include_children: bool = Query(True, description="Include child categories and subcategories")
):
    """
    Get all categories or filter by parent.
    Results are cached for 10 minutes.
    """
    # Create cache key
    cache_key = f"categories:list:{parent_id}:{include_children}"
    
    # Try to get from cache
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Fetch from database
    result = await _get_categories_cached(parent_id, include_children)
    
    # Cache for 10 minutes
    await cache.set(cache_key, result, CacheTTL.LONG)
    
    return result


@router.get("/tree")
async def get_category_tree():
    """Get full category tree structure - cached for 30 minutes"""
    cache_key = "categories:tree"
    
    # Try cache first
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    all_categories = await db.categories.find({"is_active": True}).sort("label", 1).to_list(None)
    
    cat_map = {}
    mongo_id_to_slug = {}  # Map MongoDB ID to slug for parent linking
    roots = []
    
    for cat in all_categories:
        cat_slug = cat.get("slug", "")
        mongo_id = serialize_id(cat.get("id") or cat.get("_id"))
        mongo_id_to_slug[mongo_id] = cat_slug
        
        cat_data = {
            "id": cat_slug,  # Use slug as ID
            "label": cat.get("label", ""),
            "slug": cat_slug,
            "level": cat.get("level", 1),
            "children": []
        }
        cat_map[cat_slug] = cat_data
        
        if cat.get("parent_id") is None:
            roots.append(cat_data)
    
    # Link children to parents using MongoDB ID to slug mapping
    for cat in all_categories:
        parent_mongo_id = serialize_id(cat.get("parent_id"))
        cat_slug = cat.get("slug", "")
        if parent_mongo_id:
            # Find parent slug from MongoDB ID
            parent_slug = mongo_id_to_slug.get(parent_mongo_id)
            if parent_slug and parent_slug in cat_map:
                parent = cat_map[parent_slug]
                if cat_map.get(cat_slug):
                    parent["children"].append(cat_map[cat_slug])
    
    result = {"tree": roots}
    
    # Cache for 30 minutes
    await cache.set(cache_key, result, CacheTTL.VERY_LONG)
    
    return result


@router.get("/{category_id}")
async def get_category(category_id: str):
    """Get a specific category by ID (slug or MongoDB ID)"""
    category = await db.categories.find_one({
        "$or": [
            {"slug": category_id},  # Prioritize slug
            {"id": category_id},
            {"_id": category_id}
        ]
    })
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    cat_slug = category.get("slug", "")
    cat_label = category.get("label", "")
    mongo_id = serialize_id(category.get("id") or category.get("_id"))
    
    # Get parent info using slug
    parent = None
    parent_mongo_id = category.get("parent_id")
    if parent_mongo_id:
        parent_doc = await db.categories.find_one({
            "$or": [{"id": parent_mongo_id}, {"_id": parent_mongo_id}]
        })
        if parent_doc:
            parent = {
                "id": parent_doc.get("slug", ""),  # Use slug
                "label": parent_doc.get("label", "")
            }
    
    # Get children by MongoDB parent_id
    children = await db.categories.find({
        "$or": [
            {"parent_id": mongo_id},
            {"parent_id": cat_slug}
        ],
        "is_active": True
    }).sort("label", 1).to_list(None)
    
    # Count products using slug (matching product data structure)
    products_count = await db.products.count_documents({
        "active": True,
        "$or": [
            {"category_path_ids": cat_slug},
            {"category_id": {"$regex": f"^{cat_slug}", "$options": "i"}},
            {"category": cat_label}
        ]
    })
    
    return {
        "id": cat_slug,  # Use slug as ID
        "mongo_id": mongo_id,
        "label": cat_label,
        "slug": cat_slug,
        "parent_id": parent["id"] if parent else None,
        "parent": parent,
        "level": category.get("level", 1),
        "path_ids": category.get("path_ids", [cat_slug]),
        "children": [
            {
                "id": c.get("slug", ""),  # Use slug
                "label": c.get("label", ""),
                "slug": c.get("slug", "")
            } for c in children
        ],
        "products_count": products_count,
        "is_active": category.get("is_active", True)
    }


@router.get("/{category_id}/children")
async def get_category_children(category_id: str):
    """Get direct children of a category"""
    # Find parent by slug first, then by MongoDB ID
    parent = await db.categories.find_one({
        "$or": [
            {"slug": category_id},  # Prioritize slug
            {"id": category_id}, 
            {"_id": category_id}
        ]
    })
    if not parent:
        raise HTTPException(status_code=404, detail="Category not found")
    
    parent_slug = parent.get("slug", "")
    parent_mongo_id = serialize_id(parent.get("id") or parent.get("_id"))
    
    # Find children by MongoDB parent_id
    children = await db.categories.find({
        "$or": [
            {"parent_id": parent_mongo_id},
            {"parent_id": parent_slug}
        ],
        "is_active": True
    }).sort("label", 1).to_list(None)
    
    result = []
    for child in children:
        child_slug = child.get("slug", "")
        child_label = child.get("label", "")
        # Count products using slug (matching product data structure)
        products_count = await db.products.count_documents({
            "active": True,
            "$or": [
                {"category_id": child_slug},
                {"category_id": {"$regex": f"^{child_slug}$", "$options": "i"}},
                {"subcategory_label": child_label}
            ]
        })
        result.append({
            "id": child_slug,  # Use slug as ID
            "label": child_label,
            "slug": child_slug,
            "level": child.get("level", 2),
            "products_count": products_count
        })
    
    return {
        "parent": {"id": parent_slug, "label": parent.get("label", "")},
        "children": result,
        "total": len(result)
    }


@router.get("/{category_id}/breadcrumb")
async def get_category_breadcrumb(category_id: str):
    """Get breadcrumb path for a category"""
    category = await db.categories.find_one({
        "$or": [
            {"slug": category_id},  # Prioritize slug
            {"id": category_id}, 
            {"_id": category_id}
        ]
    })
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # path_ids are already slugs in the current data structure
    path_ids = category.get("path_ids", [category.get("slug", "")])
    
    breadcrumb = []
    for path_slug in path_ids:
        cat = await db.categories.find_one({
            "$or": [
                {"slug": path_slug},
                {"id": path_slug}, 
                {"_id": path_slug}
            ]
        })
        if cat:
            breadcrumb.append({
                "id": cat.get("slug", ""),  # Use slug as ID
                "label": cat.get("label", ""),
                "slug": cat.get("slug", "")
            })
    
    return {"breadcrumb": breadcrumb}
