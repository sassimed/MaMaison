from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timezone
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Import cache
from utils.cache import cache, cache_cleanup_task
db = client[os.environ['DB_NAME']]

# Set database for dependencies
from utils.dependencies import set_database
set_database(db)

# Import routes (after setting db)
from routes.auth import router as auth_router
from routes.services import router as services_router
from routes.products_v2 import router as products_router  # v2 with hierarchical categories
from routes.categories_v2 import router as categories_router  # v2 with tree structure
from routes.gallery import router as gallery_router
from routes.appointments import router as appointments_router
from routes.contacts import router as contacts_router
from routes.user import router as user_router
from routes.requests import router as requests_router
from routes.messages import router as messages_router
from routes.admin import router as admin_router
from routes.admin_products import router as admin_products_router
from routes.upload import router as upload_router
from routes.cart import router as cart_router, set_db as set_cart_db
from routes.annonces import router as annonces_router
from routes.reviews import router as reviews_router
from routes.seo import router as seo_router
# Use Chatbot V3 (IA with admin model selection)
from routes.chatbot_v3 import router as chatbot_router
from routes.notifications import router as notifications_router
from routes.direct_messages import router as direct_messages_router
from routes.import_products import router as import_router
from routes.data_migration import router as data_migration_router
from routes.migrations import router as migrations_router
from routes.analytics import router as analytics_router, create_analytics_indexes
from routes.logs import router as logs_router, create_logs_indexes

# Set database for cart routes
set_cart_db(db)

# Create the main app
app = FastAPI(
    title="Smart Life API",
    description="API for Smart Life - Professional Home Automation & Security",
    version="1.0.0"
)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Health check route
@api_router.get("/")
async def root():
    return {"message": "Smart Life API is running", "version": "1.0.0"}

# Cache management endpoints
@api_router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    return cache.stats()

@api_router.post("/cache/clear")
async def clear_cache(pattern: str = None):
    """Clear cache - optionally by pattern"""
    if pattern:
        deleted = await cache.delete_pattern(pattern)
        return {"message": f"Cleared {deleted} cache entries matching '{pattern}'"}
    else:
        await cache.clear()
        return {"message": "All cache cleared"}

@api_router.post("/cache/clear/categories")
async def clear_categories_cache():
    """Clear categories cache"""
    deleted = await cache.delete_pattern("categories:")
    return {"message": f"Cleared {deleted} category cache entries"}

@api_router.post("/cache/clear/products")
async def clear_products_cache():
    """Clear products cache"""
    deleted = await cache.delete_pattern("products:")
    return {"message": f"Cleared {deleted} product cache entries"}

# Route pour initialiser la BD en production (GET pour accès navigateur)
@api_router.get("/init-database/{secret_key}")
@api_router.post("/init-database/{secret_key}")
async def init_database(secret_key: str):
    """Initialize database with seed data. Use secret key: mydar2024init"""
    if secret_key != "mydar2024init":
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    from datetime import timedelta
    from passlib.context import CryptContext
    import random
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    results = {"users": 0, "categories": 0, "products": 0, "services": 0, "annonces": 0}
    
    # Check if already seeded
    existing_products = await db.products.count_documents({})
    if existing_products > 50:
        return {"message": "Database already initialized", "products_count": existing_products}
    
    # Users
    users = [
        {"id": str(uuid.uuid4()), "email": "admin@mydar.tn", "full_name": "Administrateur MyDar", "phone": "+216 70 123 456", "role": "ADMIN", "is_active": True, "is_email_verified": True, "hashed_password": pwd_context.hash("admin123"), "loyalty_points": 0, "total_spent": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "email": "pro@mydar.tn", "full_name": "TechPro Installation", "phone": "+216 98 765 432", "role": "PROFESSIONNEL", "is_active": True, "is_email_verified": True, "hashed_password": pwd_context.hash("pro123"), "loyalty_points": 150, "total_spent": 2500, "company_info": {"company_name": "TechPro SARL"}, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "email": "client@mydar.tn", "full_name": "Mohamed Ben Salah", "phone": "+216 55 111 222", "role": "PARTICULIER", "is_active": True, "is_email_verified": True, "hashed_password": pwd_context.hash("client123"), "loyalty_points": 75, "total_spent": 850, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
    ]
    for user in users:
        if not await db.users.find_one({"email": user["email"]}):
            await db.users.insert_one(user)
            results["users"] += 1
    
    # Categories
    categories = [
        {"id": str(uuid.uuid4()), "name": "Vidéosurveillance", "description": "Caméras et NVR", "icon": "Camera", "product_count": 0},
        {"id": str(uuid.uuid4()), "name": "Alarme", "description": "Systèmes d'alarme", "icon": "Bell", "product_count": 0},
        {"id": str(uuid.uuid4()), "name": "Éclairage", "description": "Ampoules connectées", "icon": "Lightbulb", "product_count": 0},
        {"id": str(uuid.uuid4()), "name": "Module", "description": "Hubs et modules", "icon": "Cpu", "product_count": 0},
        {"id": str(uuid.uuid4()), "name": "Interrupteur", "description": "Interrupteurs smart", "icon": "ToggleRight", "product_count": 0},
        {"id": str(uuid.uuid4()), "name": "Prise", "description": "Prises connectées", "icon": "Plug", "product_count": 0},
        {"id": str(uuid.uuid4()), "name": "Volet", "description": "Motorisation volets", "icon": "Blinds", "product_count": 0},
        {"id": str(uuid.uuid4()), "name": "Écran", "description": "Écrans de contrôle", "icon": "Monitor", "product_count": 0},
    ]
    if await db.categories.count_documents({}) < 5:
        await db.categories.delete_many({})
        await db.categories.insert_many(categories)
        results["categories"] = len(categories)
    
    # Services
    services = [
        {"id": "videophone", "name": "Vidéophone", "slug": "videophone", "description": "Contrôle d'accès vidéo", "icon": "Video", "category": "security", "featured": True},
        {"id": "lighting", "name": "Éclairage Intelligent", "slug": "eclairage", "description": "Automatisation éclairage", "icon": "Lightbulb", "category": "automation", "featured": True},
        {"id": "alarm", "name": "Système d'Alarme", "slug": "alarme", "description": "Protection domicile", "icon": "Bell", "category": "security", "featured": True},
        {"id": "video-surveillance", "name": "Vidéosurveillance", "slug": "videosurveillance", "description": "Caméras HD/4K", "icon": "Camera", "category": "security", "featured": True},
        {"id": "shutters", "name": "Volets Connectés", "slug": "volets", "description": "Centralisation volets", "icon": "Blinds", "category": "automation", "featured": False},
        {"id": "network", "name": "Réseau & Câblage", "slug": "reseau", "description": "WiFi et câblage", "icon": "Wifi", "category": "network", "featured": False},
    ]
    if await db.services.count_documents({}) < 5:
        await db.services.delete_many({})
        await db.services.insert_many(services)
        results["services"] = len(services)
    
    # Products (1000)
    marques = ["Tuya", "Sonoff", "Aqara", "Shelly", "Dahua", "Hikvision", "Xiaomi", "TP-Link"]
    technologies = ["WiFi", "Zigbee", "WiFi/Zigbee"]
    cats_list = ["Vidéosurveillance", "Alarme", "Éclairage", "Module", "Interrupteur", "Prise", "Volet", "Écran"]
    templates = {
        "Vidéosurveillance": [("Caméra Dôme", 150, 350), ("Caméra Bullet", 180, 400), ("NVR", 300, 600)],
        "Alarme": [("Kit Alarme", 250, 500), ("Détecteur", 25, 60), ("Sirène", 35, 80)],
        "Éclairage": [("Ampoule LED", 15, 35), ("Ruban LED", 35, 90), ("Spot", 25, 55)],
        "Module": [("Hub Zigbee", 60, 120), ("Module Relais", 35, 80)],
        "Interrupteur": [("Interrupteur Tactile", 40, 90), ("Variateur", 55, 110)],
        "Prise": [("Prise Connectée", 20, 45), ("Multiprise", 50, 110)],
        "Volet": [("Module Volet", 40, 85), ("Moteur", 90, 200)],
        "Écran": [("Écran Tactile", 120, 280), ("Thermostat", 130, 280)],
    }
    
    if await db.products.count_documents({}) < 50:
        products = []
        for i in range(1000):
            cat = random.choice(cats_list)
            tpls = templates.get(cat, [("Produit", 50, 200)])
            name, pmin, pmax = random.choice(tpls)
            marque = random.choice(marques)
            products.append({
                "id": str(uuid.uuid4()),
                "name": f"{name} {marque} {random.choice(['Pro', 'Plus', 'Max', ''])}".strip(),
                "description": f"Produit {cat.lower()} de qualité. Technologie {random.choice(technologies)}.",
                "brand": marque,
                "technology": random.choice(technologies),
                "category": cat,
                "image_url": f"https://picsum.photos/seed/{i}/500/500",
                "compatibility": ["Alexa", "Google Home"],
                "price": round(random.uniform(pmin, pmax), 3),
                "featured": random.random() > 0.9,
                "stock_quantity": random.randint(5, 100),
            })
        await db.products.delete_many({})
        for i in range(0, 1000, 100):
            await db.products.insert_many(products[i:i+100])
        results["products"] = 1000
    
    # Annonces (1000)
    from datetime import timedelta as td
    villes = ["Tunis", "Sfax", "Sousse", "Ariana", "Ben Arous", "La Marsa", "Hammamet", "Nabeul", "Monastir", "Bizerte", "Gabès", "Kairouan"]
    cat_ann = ["Installation Caméra", "Système d'Alarme", "Domotique", "Éclairage Connecté", "Serrure Connectée", "Réseau WiFi/Câblage"]
    statuts = ["EN_ATTENTE", "PUBLIEE", "PUBLIEE", "PUBLIEE", "ATTRIBUEE"]
    titles = ["Installation vidéosurveillance", "Système alarme", "Domotique maison", "Éclairage connecté", "Motorisation volets", "Réseau WiFi"]
    
    client = await db.users.find_one({"role": "PARTICULIER"})
    pro = await db.users.find_one({"role": "PROFESSIONNEL"})
    
    if client and pro and await db.annonces.count_documents({}) < 50:
        annonces = []
        for i in range(1000):
            status = random.choice(statuts)
            created = datetime.now(timezone.utc) - td(days=random.randint(0, 60))
            ann = {
                "id": str(uuid.uuid4()),
                "client_id": client["id"],
                "client_name": client["full_name"],
                "client_email": client["email"],
                "client_phone": f"+216 {random.randint(20,99)} {random.randint(100,999)} {random.randint(100,999)}",
                "title": f"{random.choice(titles)} {random.choice(villes)}",
                "description": f"Recherche professionnel. Surface {random.randint(50,300)}m².",
                "category": random.choice(cat_ann),
                "city": random.choice(villes),
                "address": f"Quartier {random.choice(['Centre', 'Nord', 'Sud'])}",
                "status": status,
                "responses": [],
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
            }
            if status != "EN_ATTENTE":
                ann["published_at"] = created.isoformat()
            annonces.append(ann)
        await db.annonces.delete_many({})
        for i in range(0, 1000, 100):
            await db.annonces.insert_many(annonces[i:i+100])
        results["annonces"] = 1000
    
    # Update category counts
    for cat in cats_list:
        count = await db.products.count_documents({"category": cat})
        await db.categories.update_one({"name": cat}, {"$set": {"product_count": count}})
    
    return {
        "message": "Database initialized successfully!",
        "results": results,
        "test_accounts": {
            "admin": "admin@mydar.tn / admin123",
            "pro": "pro@mydar.tn / pro123", 
            "client": "client@mydar.tn / client123"
        }
    }

# Include all routes
api_router.include_router(auth_router)
api_router.include_router(services_router)
api_router.include_router(products_router)
api_router.include_router(categories_router)
api_router.include_router(gallery_router)
api_router.include_router(appointments_router)
api_router.include_router(contacts_router)
api_router.include_router(user_router)
api_router.include_router(requests_router)
api_router.include_router(messages_router)
api_router.include_router(admin_router)
api_router.include_router(admin_products_router)
api_router.include_router(upload_router)
api_router.include_router(cart_router)
api_router.include_router(annonces_router)
api_router.include_router(reviews_router)
api_router.include_router(seo_router)
api_router.include_router(chatbot_router)
api_router.include_router(notifications_router)
api_router.include_router(direct_messages_router)
api_router.include_router(import_router)
api_router.include_router(data_migration_router)
api_router.include_router(migrations_router)
api_router.include_router(analytics_router)
api_router.include_router(logs_router)

# Endpoint pour télécharger les exports de produits
@api_router.get("/export/products")
async def download_products_export():
    """Télécharger la liste complète des produits en JSON"""
    file_path = ROOT_DIR / "static" / "products_export.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
    return FileResponse(
        path=str(file_path),
        filename="mydar_products_export.json",
        media_type="application/json"
    )

@api_router.get("/export/products-light")
async def download_products_light_export():
    """Télécharger la liste allégée des produits en JSON"""
    file_path = ROOT_DIR / "static" / "products_export_light.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
    return FileResponse(
        path=str(file_path),
        filename="mydar_products_light.json",
        media_type="application/json"
    )

@api_router.get("/export/catalogue-complet")
async def download_catalogue_complet():
    """Télécharger le catalogue complet avec toutes les données (15MB)"""
    file_path = ROOT_DIR / "static" / "catalogue_complet.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Catalogue file not found")
    return FileResponse(
        path=str(file_path),
        filename="mydar_catalogue_complet.json",
        media_type="application/json"
    )

# ============ OBSERVABILITY ENDPOINTS ============
from utils.observability import metrics as perf_metrics, health_checker, error_tracker, logger as obs_logger

@api_router.get("/health")
async def health_check():
    """Comprehensive health check"""
    return await health_checker.check_all()

@api_router.get("/metrics")
async def get_perf_metrics():
    """Get performance metrics"""
    return {
        "latency": perf_metrics.get_all_stats(window_seconds=300),
        "cache": cache.stats(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/metrics/errors")
async def get_error_metrics():
    """Get error summary (admin only)"""
    return {
        "recent_errors": error_tracker.get_recent_errors(10),
        "error_summary": error_tracker.get_error_summary()
    }

# Include the API router in the main app
app.include_router(api_router)

# ============ PERFORMANCE MIDDLEWARE ============
from utils.middleware import PerformanceMiddleware, RateLimitMiddleware

# Add performance monitoring middleware (outermost = first to execute)
app.add_middleware(PerformanceMiddleware)

# Add rate limiting (100 requests/min per IP, burst of 30)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100, burst=30)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import utilities
from utils.indexes import create_indexes
from utils.event_queue import event_queue
from utils.database import ensure_indexes, RECOMMENDED_INDEXES

# Register MongoDB health check
async def check_mongodb():
    try:
        await db.command('ping')
        return True
    except:
        return False

health_checker.register("mongodb", check_mongodb)

@app.on_event("startup")
async def startup_event():
    logger.info("Smart Life API starting up...")
    
    # Create all indexes for optimal performance
    await create_indexes(db)
    logger.info("Database indexes created")
    
    # Create analytics indexes
    await create_analytics_indexes()
    logger.info("Analytics indexes created")
    
    # Create logs indexes
    await create_logs_indexes()
    logger.info("Logs indexes created")
    
    # Ensure performance indexes
    await ensure_indexes(db, ["products", "orders", "users", "analytics_events"])
    logger.info("Performance indexes ensured")
    
    # Start cache cleanup background task
    asyncio.create_task(cache_cleanup_task())
    logger.info("Cache cleanup task started")
    
    # Start event queue for async analytics
    await event_queue.start()
    logger.info("Event queue started")
    
    obs_logger.info("API startup complete", type="startup")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Shutting down...")
    
    # Stop event queue gracefully
    await event_queue.stop()
    logger.info("Event queue stopped")
    
    # Close database connection
    client.close()
    logger.info("Database connection closed")

