"""
Admin Products API
Endpoints for managing products (CRUD operations)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
import os
import re
import uuid
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/admin/products-manage", tags=["Admin Products"])

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# Pydantic models
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    category_label: Optional[str] = None
    subcategory_label: Optional[str] = None
    primary_image_url: Optional[str] = None
    images: Optional[List[str]] = None
    videos: Optional[List[dict]] = None
    specifications: Optional[dict] = None  # Changed to dict to match DB structure
    connectivity: Optional[str] = None
    technologies: Optional[List[str]] = None
    featured: Optional[bool] = None
    active: Optional[bool] = None
    stock_quantity: Optional[int] = None
    
    class Config:
        extra = "ignore"  # Ignore extra fields from frontend


class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    description: Optional[str] = ""
    brand: Optional[str] = None
    price: Optional[float] = None
    category_label: str
    subcategory_label: str
    primary_image_url: Optional[str] = None
    images: Optional[List[str]] = []
    connectivity: Optional[str] = None
    technologies: Optional[List[str]] = []
    featured: bool = False
    stock_quantity: int = 0


def slugify(text):
    """Convert text to slug format"""
    text = text.lower()
    text = text.replace(' ', '-').replace("'", '-').replace('é', 'e').replace('ô', 'o')
    text = text.replace('î', 'i').replace('&', '').replace('à', 'a')
    text = re.sub(r'-+', '-', text).strip('-')
    return text


async def find_product_by_id(product_id: str):
    """Helper to find a product by ObjectId or UUID id field"""
    from bson import ObjectId
    
    product = None
    query_id = None
    
    # Try ObjectId first
    try:
        if len(product_id) == 24:
            query_id = ObjectId(product_id)
            product = await db.products.find_one({"_id": query_id})
    except:
        pass
    
    # Try by 'id' field (UUID)
    if not product:
        product = await db.products.find_one({"id": product_id})
        if product:
            query_id = product.get("_id")
    
    # Try string _id
    if not product:
        product = await db.products.find_one({"_id": product_id})
        if product:
            query_id = product_id
    
    return product, query_id


@router.get("")
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    has_image: Optional[bool] = None,
    q: Optional[str] = None,
    search: Optional[str] = None,  # Alias for q
    include_no_image: bool = False
):
    """List products for admin with filters"""
    query = {}
    
    # Use search param if q is not provided (alias)
    search_term = q or search
    
    # Category filter
    if category:
        query["category_label"] = {"$regex": category, "$options": "i"}
    
    if subcategory:
        query["subcategory_label"] = {"$regex": subcategory, "$options": "i"}
    
    # Image filter
    if has_image is not None:
        if has_image:
            query["$and"] = [
                {"primary_image_url": {"$exists": True}},
                {"primary_image_url": {"$ne": None}},
                {"primary_image_url": {"$ne": ""}}
            ]
        else:
            query["$or"] = [
                {"primary_image_url": {"$exists": False}},
                {"primary_image_url": None},
                {"primary_image_url": ""},
                {"image_missing": True}
            ]
    
    # Search - include model_code
    if search_term:
        search_conditions = [
            {"name": {"$regex": search_term, "$options": "i"}},
            {"sku": {"$regex": search_term, "$options": "i"}},
            {"brand": {"$regex": search_term, "$options": "i"}},
            {"model_code": {"$regex": search_term, "$options": "i"}}
        ]
        
        # If there's already an $or from image filter, we need to use $and
        if "$or" in query:
            existing_or = query.pop("$or")
            query["$and"] = [
                {"$or": existing_or},
                {"$or": search_conditions}
            ]
        else:
            query["$or"] = search_conditions
    
    # Count total
    total = await db.products.count_documents(query)
    
    # Pagination
    skip = (page - 1) * limit
    
    # Fetch products
    products = await db.products.find(query).sort([
        ("updated_at", -1),
        ("name", 1)
    ]).skip(skip).limit(limit).to_list(limit)
    
    # Format response
    items = []
    for p in products:
        items.append({
            "id": str(p.get("_id")),
            "name": p.get("name"),
            "sku": p.get("sku"),
            "model_code": p.get("model_code"),  # Include model_code
            "description": p.get("description", "")[:200],
            "brand": p.get("brand"),
            "price": p.get("price"),
            "category_label": p.get("category_label"),
            "subcategory_label": p.get("subcategory_label"),
            "category": f"{p.get('category_label', '')} > {p.get('subcategory_label', '')}",
            "primary_image_url": p.get("primary_image_url"),
            "image_url": p.get("primary_image_url"),  # Alias for compatibility
            "images": p.get("images", []),
            "videos": p.get("videos", []),
            "specifications": p.get("specifications", []),
            "connectivity": p.get("attributes", {}).get("connectivity"),
            "technologies": p.get("attributes_norm", {}).get("technologies", []),
            "featured": p.get("featured", False),
            "active": p.get("active", True),
            "stock_quantity": p.get("stock_quantity", 0),
            "source": p.get("source"),
            "updated_at": p.get("updated_at").isoformat() if p.get("updated_at") and hasattr(p.get("updated_at"), 'isoformat') else p.get("updated_at")
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/stats/images")
async def get_image_stats():
    """Get statistics about product images"""
    total = await db.products.count_documents({})
    
    without_image = await db.products.count_documents({
        "$or": [
            {"primary_image_url": {"$exists": False}},
            {"primary_image_url": None},
            {"primary_image_url": ""},
            {"image_missing": True}
        ]
    })
    
    with_image = total - without_image
    
    return {
        "total": total,
        "with_image": with_image,
        "without_image": without_image,
        "percentage_with_image": round(with_image / total * 100, 1) if total > 0 else 0
    }


def safe_isoformat(value):
    """Safely convert date to ISO format string"""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


@router.get("/{product_id}")
async def get_product(product_id: str):
    """Get a single product by ID"""
    product, query_id = await find_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    return {
        "id": str(product.get("_id")),
        "name": product.get("name"),
        "sku": product.get("sku"),
        "model_code": product.get("model_code"),
        "description": product.get("description", ""),
        "brand": product.get("brand"),
        "price": product.get("price"),
        "category_label": product.get("category_label"),
        "subcategory_label": product.get("subcategory_label"),
        "category_id": product.get("category_id"),
        "primary_image_url": product.get("primary_image_url"),
        "images": product.get("images", []),
        "videos": product.get("videos", []),
        "specifications": product.get("specifications", []),
        "attributes": product.get("attributes", {}),
        "attributes_norm": product.get("attributes_norm", {}),
        "featured": product.get("featured", False),
        "active": product.get("active", True),
        "stock_quantity": product.get("stock_quantity", 0),
        "source": product.get("source"),
        "source_url": product.get("source_url"),
        "created_at": safe_isoformat(product.get("created_at")),
        "updated_at": safe_isoformat(product.get("updated_at"))
    }


@router.put("/{product_id}")
async def update_product(product_id: str, data: ProductUpdate):
    """Update a product"""
    product, query_id = await find_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    update_data = {"updated_at": datetime.now(timezone.utc)}
    
    # Update basic fields
    if data.name is not None:
        update_data["name"] = data.name
    if data.sku is not None:
        update_data["sku"] = data.sku
    if data.description is not None:
        update_data["description"] = data.description
    if data.brand is not None:
        update_data["brand"] = data.brand
    if data.price is not None:
        update_data["price"] = data.price
    if data.featured is not None:
        update_data["featured"] = data.featured
    if data.active is not None:
        update_data["active"] = data.active
    if data.stock_quantity is not None:
        update_data["stock_quantity"] = data.stock_quantity
    
    # Update category
    if data.category_label is not None or data.subcategory_label is not None:
        cat_label = data.category_label or product.get("category_label")
        subcat_label = data.subcategory_label or product.get("subcategory_label")
        
        if cat_label and subcat_label:
            cat_slug = slugify(cat_label)
            subcat_slug = slugify(subcat_label)
            
            update_data["category_label"] = cat_label
            update_data["subcategory_label"] = subcat_label
            update_data["category"] = f"{cat_label} > {subcat_label}"
            update_data["category_id"] = f"{cat_slug}__{subcat_slug}"
            update_data["category_path_ids"] = cat_slug
    
    # Update images
    if data.primary_image_url is not None:
        update_data["primary_image_url"] = data.primary_image_url
        update_data["image_missing"] = not bool(data.primary_image_url)
    if data.images is not None:
        update_data["images"] = data.images
    
    # Update videos
    if data.videos is not None:
        update_data["videos"] = data.videos
    
    # Update specifications
    if data.specifications is not None:
        update_data["specifications"] = data.specifications
    
    # Update connectivity and technologies
    if data.connectivity is not None:
        if "attributes" not in update_data:
            update_data["attributes"] = product.get("attributes", {})
        update_data["attributes"]["connectivity"] = data.connectivity
    
    if data.technologies is not None:
        if "attributes_norm" not in update_data:
            update_data["attributes_norm"] = product.get("attributes_norm", {})
        update_data["attributes_norm"]["technologies"] = data.technologies
    
    # Apply update
    result = await db.products.update_one(
        {"_id": query_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Produit mis à jour"}


@router.post("/{product_id}/gallery/add")
async def add_to_gallery(product_id: str, image_url: str):
    """Add an image to product gallery"""
    product, query_id = await find_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    images = product.get("images", [])
    if image_url not in images:
        images.append(image_url)
    
    await db.products.update_one(
        {"_id": query_id},
        {"$set": {"images": images, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"success": True, "images": images}


@router.post("/{product_id}/gallery/remove")
async def remove_from_gallery(product_id: str, image_url: str):
    """Remove an image from product gallery"""
    product, query_id = await find_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    images = product.get("images", [])
    if image_url in images:
        images.remove(image_url)
    
    await db.products.update_one(
        {"_id": query_id},
        {"$set": {"images": images, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"success": True, "images": images}


@router.post("/{product_id}/gallery/reorder")
async def reorder_gallery(product_id: str, images: List[str]):
    """Reorder product gallery images"""
    product, query_id = await find_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    await db.products.update_one(
        {"_id": query_id},
        {"$set": {"images": images, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"success": True, "images": images}


@router.post("/{product_id}/set-primary-image")
async def set_primary_image(product_id: str, image_url: str):
    """Set the primary image from gallery"""
    product, query_id = await find_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    await db.products.update_one(
        {"_id": query_id},
        {"$set": {
            "primary_image_url": image_url,
            "image_missing": False,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"success": True, "primary_image_url": image_url}


@router.post("")
async def create_product(data: ProductCreate):
    """Create a new product"""
    # Generate IDs
    product_id = str(uuid.uuid4())
    cat_slug = slugify(data.category_label)
    subcat_slug = slugify(data.subcategory_label)
    
    product = {
        "_id": product_id,
        "id": product_id,
        "name": data.name,
        "sku": data.sku or "",
        "description": data.description,
        "brand": data.brand,
        "price": data.price,
        "category_label": data.category_label,
        "subcategory_label": data.subcategory_label,
        "category": f"{data.category_label} > {data.subcategory_label}",
        "category_id": f"{cat_slug}__{subcat_slug}",
        "category_path_ids": cat_slug,
        "primary_image_url": data.primary_image_url,
        "images": data.images or [],
        "videos": [],
        "specifications": [],
        "attributes": {"connectivity": data.connectivity},
        "attributes_norm": {"technologies": data.technologies or []},
        "featured": data.featured,
        "active": True,
        "stock_quantity": data.stock_quantity,
        "image_missing": not bool(data.primary_image_url),
        "source": "admin",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.products.insert_one(product)
    
    return {"success": True, "id": product_id, "message": "Produit créé"}


@router.delete("/{product_id}")
async def delete_product(product_id: str):
    """Delete a product"""
    product, query_id = await find_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    result = await db.products.delete_one({"_id": query_id})
    
    return {"success": True, "message": "Produit supprimé"}


@router.post("/{product_id}/toggle-active")
async def toggle_product_active(product_id: str):
    """Toggle product active status"""
    product, query_id = await find_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    new_status = not product.get("active", True)
    
    await db.products.update_one(
        {"_id": query_id},
        {"$set": {"active": new_status, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"success": True, "active": new_status}
