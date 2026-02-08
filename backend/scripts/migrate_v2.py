"""
Migration script for MyDar v2 Gemini2 schema
Migrates products and categories to new optimized schema
"""

import json
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')


def build_category_path_ids(categories: list, category_id: str) -> list:
    """Build the full path of category IDs from root to this category"""
    cat_map = {c['id']: c for c in categories}
    path = []
    current_id = category_id
    
    while current_id:
        path.insert(0, current_id)
        cat = cat_map.get(current_id)
        if cat:
            current_id = cat.get('parent_id')
        else:
            break
    
    return path


def get_category_level(categories: list, category_id: str) -> int:
    """Get the depth level of a category (1 = root)"""
    path = build_category_path_ids(categories, category_id)
    return len(path)


async def migrate():
    print(f"Connecting to MongoDB: {MONGO_URL}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Load JSON data
    print("Loading JSON data...")
    with open('/app/products_v2.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    categories = data.get('categories', [])
    products = data.get('products', [])
    
    print(f"Categories: {len(categories)}")
    print(f"Products: {len(products)}")
    
    # === STEP 1: Backup existing collections ===
    print("\n=== Step 1: Backing up existing data ===")
    
    # Backup old products
    old_products = await db.products.find({}).to_list(None)
    if old_products:
        await db.products_backup_v1.drop()
        await db.products_backup_v1.insert_many(old_products)
        print(f"Backed up {len(old_products)} products to products_backup_v1")
    
    # Backup old categories
    old_categories = await db.categories.find({}).to_list(None)
    if old_categories:
        await db.categories_backup_v1.drop()
        await db.categories_backup_v1.insert_many(old_categories)
        print(f"Backed up {len(old_categories)} categories to categories_backup_v1")
    
    # === STEP 2: Drop and recreate collections ===
    print("\n=== Step 2: Dropping old collections ===")
    await db.products.drop()
    await db.categories.drop()
    print("Old collections dropped")
    
    # === STEP 3: Insert new categories ===
    print("\n=== Step 3: Inserting categories ===")
    
    categories_docs = []
    for cat in categories:
        cat_id = cat['id']
        path_ids = build_category_path_ids(categories, cat_id)
        level = len(path_ids)
        
        # Generate slug from id
        slug = cat_id.replace('__', '/').replace('_', '-')
        
        doc = {
            "_id": cat_id,
            "label": cat['label'],
            "slug": slug,
            "parent_id": cat.get('parent_id'),
            "path_ids": path_ids,
            "level": level,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        categories_docs.append(doc)
    
    if categories_docs:
        await db.categories.insert_many(categories_docs)
        print(f"Inserted {len(categories_docs)} categories")
    
    # === STEP 4: Insert products ===
    print("\n=== Step 4: Inserting products ===")
    
    products_docs = []
    for prod in products:
        # Ensure category_path_ids exists
        if not prod.get('category_path_ids'):
            prod['category_path_ids'] = build_category_path_ids(categories, prod.get('category_id', ''))
        
        # Build document with new schema
        doc = {
            "_id": prod.get('id') or prod.get('sku', str(len(products_docs))),
            "sku": prod.get('sku'),
            "name": prod.get('name'),
            "slug": prod.get('slug'),
            "description": prod.get('description'),
            "brand": prod.get('brand'),
            "price": prod.get('price'),
            "currency": prod.get('currency', 'TND'),
            
            # Category hierarchy
            "category_id": prod.get('category_id'),
            "category_path_ids": prod.get('category_path_ids', []),
            "category_label": prod.get('category_label'),
            "subcategory_label": prod.get('subcategory_label'),
            
            # Images
            "images": prod.get('images', []),
            "primary_image_url": prod.get('primary_image_url') or prod.get('image'),
            "image_missing": prod.get('image_missing', not bool(prod.get('image'))),
            
            # Attributes for filtering
            "attributes": prod.get('attributes', {}),
            "attributes_norm": prod.get('attributes_norm', {}),
            
            # Search optimization
            "search": prod.get('search', {
                "keywords": [],
                "synonyms": [],
                "facets": {}
            }),
            
            # AI/Gemini data
            "ai": prod.get('ai', {
                "summary": prod.get('description', '')[:200] if prod.get('description') else "",
                "bullets": [],
                "source_text": ""
            }),
            
            # Ranking
            "ranking": prod.get('ranking', {
                "quality_score": 50,
                "boost_featured": prod.get('featured', False),
                "boost_in_stock": prod.get('in_stock', True),
                "penalty_missing_image": prod.get('image_missing', False)
            }),
            
            # Legacy fields for compatibility
            "category": prod.get('category'),
            "image": prod.get('image'),
            "specifications": prod.get('specifications', {}),
            "source": prod.get('source'),
            "source_url": prod.get('source_url'),
            "fournisseur": prod.get('fournisseur'),
            "in_stock": prod.get('in_stock', True),
            "featured": prod.get('featured', False),
            "active": prod.get('active', True),
            "technologies": prod.get('technologies', []),
            
            # Timestamps
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "schema_version": "v2_gemini2"
        }
        products_docs.append(doc)
    
    if products_docs:
        # Insert in batches
        batch_size = 500
        for i in range(0, len(products_docs), batch_size):
            batch = products_docs[i:i+batch_size]
            await db.products.insert_many(batch)
            print(f"Inserted batch {i//batch_size + 1}: {len(batch)} products")
    
    print(f"Total products inserted: {len(products_docs)}")
    
    # === STEP 5: Create indexes ===
    print("\n=== Step 5: Creating indexes ===")
    
    # Categories indexes
    await db.categories.create_index("parent_id")
    await db.categories.create_index("path_ids")
    await db.categories.create_index("slug", unique=True)
    await db.categories.create_index("level")
    print("Categories indexes created")
    
    # Products indexes
    await db.products.create_index("category_id")
    await db.products.create_index("category_path_ids")
    await db.products.create_index("attributes_norm.connectivity")
    await db.products.create_index("attributes_norm.technologies")
    await db.products.create_index("search.facets.brand")
    await db.products.create_index("search.facets.category")
    await db.products.create_index("search.facets.subcategory")
    await db.products.create_index([("ranking.quality_score", -1)])
    await db.products.create_index("active")
    await db.products.create_index("brand")
    await db.products.create_index("image_missing")
    
    # Text search index
    await db.products.create_index([
        ("name", "text"),
        ("description", "text"),
        ("ai.source_text", "text"),
        ("search.keywords", "text")
    ], default_language="french", name="text_search_index")
    
    print("Products indexes created")
    
    # === STEP 6: Verify ===
    print("\n=== Step 6: Verification ===")
    
    cat_count = await db.categories.count_documents({})
    prod_count = await db.products.count_documents({})
    active_count = await db.products.count_documents({"active": True})
    with_image = await db.products.count_documents({"image_missing": False})
    
    print(f"Categories: {cat_count}")
    print(f"Products total: {prod_count}")
    print(f"Products active: {active_count}")
    print(f"Products with images: {with_image}")
    
    # Test hierarchical query
    root_cats = await db.categories.count_documents({"parent_id": None})
    sub_cats = await db.categories.count_documents({"parent_id": {"$ne": None}})
    print(f"Root categories: {root_cats}")
    print(f"Subcategories: {sub_cats}")
    
    # Test product by category path
    videosurv_products = await db.products.count_documents({"category_path_ids": "videosurveillance"})
    print(f"Products in Vidéosurveillance (hierarchical): {videosurv_products}")
    
    print("\n✅ Migration completed successfully!")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
