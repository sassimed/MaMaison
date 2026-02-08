"""
API de Migration / Synchronisation de Données
Endpoint à appeler après déploiement pour mettre à jour la base de données

POST /api/migrations/run
POST /api/migrations/init  (Initialize database with all data)
Headers: X-Migration-Key: <secret_key>
"""

from fastapi import APIRouter, HTTPException, Header
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from pathlib import Path
import hashlib
import json
import os

router = APIRouter(prefix="/migrations", tags=["Migrations"])

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Clé secrète pour sécuriser l'API (à définir dans .env)
MIGRATION_SECRET = os.environ.get('MIGRATION_SECRET', 'mydar-migration-2026')

# Path to static files
STATIC_DIR = Path(__file__).parent.parent / "static"


class MigrationResult(BaseModel):
    success: bool
    message: str
    migrations_run: List[str]
    details: Dict


class MigrationRequest(BaseModel):
    migrations: Optional[List[str]] = None  # Si None, exécute toutes les migrations


# ============ MIGRATIONS DISPONIBLES ============

async def migration_generate_model_codes() -> Dict:
    """
    Migration: Génère les codes modèles pour tous les produits qui n'en ont pas
    Format: BRAND-XXXX (ex: DAH-EE41)
    """
    cursor = db.products.find({'model_code': {'$exists': False}})
    
    updated = 0
    async for product in cursor:
        product_id = product.get('id', str(product.get('_id')))
        brand = (product.get('brand') or 'MD')[:3].upper()
        
        # Générer un code unique basé sur l'ID du produit
        hash_part = hashlib.md5(product_id.encode()).hexdigest()[:4].upper()
        model_code = f"{brand}-{hash_part}"
        
        await db.products.update_one(
            {'id': product_id},
            {'$set': {'model_code': model_code}}
        )
        updated += 1
    
    return {
        "migration": "generate_model_codes",
        "products_updated": updated,
        "status": "completed"
    }


async def migration_ensure_indexes() -> Dict:
    """
    Migration: Crée les index nécessaires pour les performances
    """
    indexes_created = []
    
    # Index pour la recherche de produits
    try:
        await db.products.create_index([("model_code", 1)])
        indexes_created.append("products.model_code")
    except Exception as e:
        pass  # Index existe déjà
    
    try:
        await db.products.create_index([("active", 1), ("image_missing", 1)])
        indexes_created.append("products.active_image")
    except Exception:
        pass
    
    # Index pour les sessions de chat
    try:
        await db.chat_sessions_v3.create_index([("session_id", 1)], unique=True)
        indexes_created.append("chat_sessions_v3.session_id")
    except Exception:
        pass
    
    # Index pour l'historique de chat
    try:
        await db.chat_history.create_index([("session_id", 1), ("timestamp", -1)])
        indexes_created.append("chat_history.session_timestamp")
    except Exception:
        pass
    
    # Index pour les purchase_requests
    try:
        await db.purchase_requests.create_index([("id", 1)])
        indexes_created.append("purchase_requests.id")
    except Exception:
        pass
    
    try:
        await db.purchase_requests.create_index([("user_email", 1)])
        indexes_created.append("purchase_requests.user_email")
    except Exception:
        pass
    
    return {
        "migration": "ensure_indexes",
        "indexes_created": indexes_created,
        "status": "completed"
    }


async def migration_cleanup_chat_sessions() -> Dict:
    """
    Migration: Nettoie les anciennes sessions de chat (plus de 30 jours)
    """
    from datetime import timedelta
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Supprimer les anciennes sessions
    result_sessions = await db.chat_sessions_v3.delete_many({
        "updated_at": {"$lt": thirty_days_ago}
    })
    
    # Supprimer l'ancien historique
    result_history = await db.chat_history.delete_many({
        "timestamp": {"$lt": thirty_days_ago}
    })
    
    return {
        "migration": "cleanup_chat_sessions",
        "sessions_deleted": result_sessions.deleted_count,
        "history_deleted": result_history.deleted_count,
        "status": "completed"
    }


async def migration_set_default_chatbot_model() -> Dict:
    """
    Migration: Configure le modèle IA par défaut si non défini
    """
    existing = await db.chatbot_settings.find_one({"key": "ai_model"})
    
    if not existing:
        await db.chatbot_settings.insert_one({
            "key": "ai_model",
            "value": "gpt-5.2",
            "updated_at": datetime.now(timezone.utc)
        })
        return {
            "migration": "set_default_chatbot_model",
            "model_set": "gpt-5.2",
            "status": "created"
        }
    
    return {
        "migration": "set_default_chatbot_model",
        "model_set": existing.get("value"),
        "status": "already_exists"
    }


async def migration_normalize_product_data() -> Dict:
    """
    Migration: Normalise les données produits (active, in_stock, etc.)
    """
    # S'assurer que tous les produits ont les champs requis
    result = await db.products.update_many(
        {"active": {"$exists": False}},
        {"$set": {"active": True}}
    )
    active_set = result.modified_count
    
    result = await db.products.update_many(
        {"in_stock": {"$exists": False}},
        {"$set": {"in_stock": True}}
    )
    stock_set = result.modified_count
    
    result = await db.products.update_many(
        {"image_missing": {"$exists": False}},
        {"$set": {"image_missing": False}}
    )
    image_set = result.modified_count
    
    return {
        "migration": "normalize_product_data",
        "active_set": active_set,
        "stock_set": stock_set,
        "image_set": image_set,
        "status": "completed"
    }


# ============ LISTE DES MIGRATIONS ============

AVAILABLE_MIGRATIONS = {
    "generate_model_codes": migration_generate_model_codes,
    "ensure_indexes": migration_ensure_indexes,
    "cleanup_chat_sessions": migration_cleanup_chat_sessions,
    "set_default_chatbot_model": migration_set_default_chatbot_model,
    "normalize_product_data": migration_normalize_product_data,
}


# ============ ENDPOINTS ============

@router.get("/available")
async def get_available_migrations():
    """Liste les migrations disponibles"""
    return {
        "migrations": list(AVAILABLE_MIGRATIONS.keys()),
        "description": {
            "generate_model_codes": "Génère les codes modèles (BRAND-XXXX) pour les produits",
            "ensure_indexes": "Crée les index MongoDB pour les performances",
            "cleanup_chat_sessions": "Supprime les anciennes sessions de chat (>30 jours)",
            "set_default_chatbot_model": "Configure le modèle IA par défaut",
            "normalize_product_data": "Normalise les champs produits (active, in_stock, etc.)",
        }
    }


@router.post("/run", response_model=MigrationResult)
async def run_migrations(
    request: Optional[MigrationRequest] = None,
    x_migration_key: str = Header(None, alias="X-Migration-Key")
):
    """
    Exécute les migrations de données
    
    Headers:
        X-Migration-Key: Clé secrète pour autoriser l'exécution
    
    Body (optionnel):
        migrations: Liste des migrations à exécuter. Si vide, exécute toutes.
    
    Exemple:
        curl -X POST https://mydar.tn/api/migrations/run \\
             -H "X-Migration-Key: mydar-migration-2026" \\
             -H "Content-Type: application/json" \\
             -d '{"migrations": ["generate_model_codes", "ensure_indexes"]}'
    """
    
    # Vérifier la clé d'autorisation
    if x_migration_key != MIGRATION_SECRET:
        raise HTTPException(status_code=401, detail="Clé de migration invalide")
    
    # Déterminer quelles migrations exécuter
    if request and request.migrations:
        migrations_to_run = request.migrations
    else:
        migrations_to_run = list(AVAILABLE_MIGRATIONS.keys())
    
    # Vérifier que toutes les migrations demandées existent
    for m in migrations_to_run:
        if m not in AVAILABLE_MIGRATIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Migration inconnue: {m}. Disponibles: {list(AVAILABLE_MIGRATIONS.keys())}"
            )
    
    # Exécuter les migrations
    results = {}
    migrations_run = []
    
    for migration_name in migrations_to_run:
        try:
            migration_func = AVAILABLE_MIGRATIONS[migration_name]
            result = await migration_func()
            results[migration_name] = result
            migrations_run.append(migration_name)
        except Exception as e:
            results[migration_name] = {
                "migration": migration_name,
                "status": "error",
                "error": str(e)
            }
    
    # Log de la migration
    await db.migration_logs.insert_one({
        "timestamp": datetime.now(timezone.utc),
        "migrations_run": migrations_run,
        "results": results,
        "success": all(r.get("status") != "error" for r in results.values())
    })
    
    return MigrationResult(
        success=all(r.get("status") != "error" for r in results.values()),
        message=f"{len(migrations_run)} migration(s) exécutée(s)",
        migrations_run=migrations_run,
        details=results
    )


@router.get("/status")
async def get_migration_status():
    """Retourne le statut des données et des dernières migrations"""
    
    # Stats produits
    total_products = await db.products.count_documents({})
    products_with_code = await db.products.count_documents({"model_code": {"$exists": True}})
    active_products = await db.products.count_documents({"active": True})
    
    # Stats sessions
    total_sessions = await db.chat_sessions_v3.count_documents({})
    
    # Dernière migration
    last_migration = await db.migration_logs.find_one(
        {}, 
        sort=[("timestamp", -1)]
    )
    
    return {
        "database": {
            "products": {
                "total": total_products,
                "with_model_code": products_with_code,
                "missing_model_code": total_products - products_with_code,
                "active": active_products
            },
            "chat_sessions": total_sessions
        },
        "last_migration": {
            "timestamp": last_migration.get("timestamp") if last_migration else None,
            "migrations_run": last_migration.get("migrations_run") if last_migration else [],
            "success": last_migration.get("success") if last_migration else None
        } if last_migration else None
    }


@router.post("/init")
async def init_database(
    x_migration_key: str = Header(None, alias="X-Migration-Key")
):
    """
    Initialise la base de données avec toutes les données (produits, catégories, settings)
    À appeler après un déploiement sur une nouvelle base de données vide.
    
    Headers:
        X-Migration-Key: Clé secrète pour autoriser l'exécution
    
    Exemple:
        curl -X POST https://mydar.tn/api/migrations/init \\
             -H "X-Migration-Key: mydar-migration-2026"
    """
    
    # Vérifier la clé d'autorisation
    if x_migration_key != MIGRATION_SECRET:
        raise HTTPException(status_code=401, detail="Clé de migration invalide")
    
    results = {
        "products": {"status": "pending", "count": 0},
        "categories": {"status": "pending", "count": 0},
        "settings": {"status": "pending", "count": 0},
        "users": {"status": "pending", "count": 0},
        "migrations": {"status": "pending"}
    }
    
    try:
        # 1. Importer les produits
        products_file = STATIC_DIR / "init_products.json"
        if products_file.exists():
            with open(products_file, "r") as f:
                products = json.load(f)
            
            if products:
                # Supprimer les anciens produits et insérer les nouveaux
                await db.products.delete_many({})
                await db.products.insert_many(products)
                results["products"] = {"status": "completed", "count": len(products)}
        else:
            results["products"] = {"status": "error", "error": "File not found"}
        
        # 2. Importer les catégories
        categories_file = STATIC_DIR / "init_categories.json"
        if categories_file.exists():
            with open(categories_file, "r") as f:
                categories = json.load(f)
            
            if categories:
                # Supprimer les anciennes catégories
                await db.categories.delete_many({})
                
                # S'assurer que chaque catégorie a un id unique
                for i, cat in enumerate(categories):
                    if not cat.get("id"):
                        # Générer un id basé sur le slug ou l'index
                        cat["id"] = cat.get("slug") or cat.get("_id") or f"cat_{i}"
                
                await db.categories.insert_many(categories)
                results["categories"] = {"status": "completed", "count": len(categories)}
        else:
            results["categories"] = {"status": "error", "error": "File not found"}
        
        # 3. Importer les settings du chatbot
        settings_file = STATIC_DIR / "init_settings.json"
        if settings_file.exists():
            with open(settings_file, "r") as f:
                settings = json.load(f)
            
            if settings:
                await db.chatbot_settings.delete_many({})
                await db.chatbot_settings.insert_many(settings)
                results["settings"] = {"status": "completed", "count": len(settings)}
        else:
            results["settings"] = {"status": "skipped", "reason": "No settings file"}
        
        # 4. Importer les utilisateurs
        users_file = STATIC_DIR / "init_users.json"
        if users_file.exists():
            with open(users_file, "r") as f:
                users = json.load(f)
            
            if users:
                # Ne pas supprimer les users existants, juste upsert
                for user in users:
                    await db.users.update_one(
                        {"email": user.get("email")},
                        {"$set": user},
                        upsert=True
                    )
                results["users"] = {"status": "completed", "count": len(users)}
        else:
            results["users"] = {"status": "skipped", "reason": "No users file"}
        
        # 5. Exécuter toutes les migrations
        migrations_results = {}
        for migration_name, migration_func in AVAILABLE_MIGRATIONS.items():
            try:
                result = await migration_func()
                migrations_results[migration_name] = result
            except Exception as e:
                migrations_results[migration_name] = {"status": "error", "error": str(e)}
        
        results["migrations"] = {
            "status": "completed",
            "details": migrations_results
        }
        
        # Log
        await db.migration_logs.insert_one({
            "timestamp": datetime.now(timezone.utc),
            "type": "init",
            "results": results,
            "success": True
        })
        
        return {
            "success": True,
            "message": "Base de données initialisée avec succès",
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur lors de l'initialisation: {str(e)}",
            "results": results
        }
