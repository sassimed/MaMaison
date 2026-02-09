"""
Script de migration des produits vers le modèle universel v3
Ajoute le support pour l'affiliation multi-sources
"""

import asyncio
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'mydar_db')


async def migrate_products():
    """Migration des produits vers le nouveau format universel"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("="*60)
    print("🚀 MIGRATION VERS MODÈLE UNIVERSEL v3")
    print("="*60)
    
    # Compter les produits
    total = await db.products.count_documents({})
    print(f"\n📊 Total produits à migrer: {total}")
    
    if total == 0:
        print("❌ Aucun produit trouvé. Chargement depuis le fichier JSON...")
        await load_products_from_json(db)
        total = await db.products.count_documents({})
        print(f"✅ {total} produits chargés depuis le JSON")
    
    # Récupérer tous les produits
    cursor = db.products.find({})
    products = await cursor.to_list(length=None)
    
    migrated = 0
    errors = 0
    
    for product in products:
        try:
            product_id = product.get('id') or str(product.get('_id'))
            
            # Construire les nouvelles structures
            update_data = {}
            
            # 1. Structure prices (affiliation multi-sources)
            current_price = product.get('price')
            if current_price or not product.get('prices'):
                prices_data = {
                    "default": {
                        "source": "internal",
                        "price": current_price,
                        "currency": product.get('currency', 'TND'),
                        "in_stock": product.get('in_stock', True),
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "sources": [],
                    "best_price": {
                        "source": "internal",
                        "price": current_price,
                        "currency": product.get('currency', 'TND')
                    } if current_price else None,
                    "price_history": []
                }
                update_data['prices'] = prices_data
            
            # 2. Convertir specifications en specs (format flexible)
            existing_specs = product.get('specifications', [])
            specs_list = []
            
            for section in existing_specs:
                section_name = section.get('name', 'general')
                for spec in section.get('specs', []):
                    key = spec.get('key', '').strip().rstrip(':').lower().replace(' ', '_')
                    value = spec.get('value', '').strip()
                    
                    if key and value and value not in ['–', '-', 'N/A', '']:
                        # Détecter le type de valeur
                        parsed_value = value
                        unit = None
                        
                        # Essayer de parser les nombres avec unités
                        import re
                        num_match = re.match(r'^([\d.,]+)\s*([a-zA-Z°%]+)?$', value)
                        if num_match:
                            try:
                                parsed_value = float(num_match.group(1).replace(',', '.'))
                                unit = num_match.group(2) if num_match.group(2) else None
                            except:
                                pass
                        
                        specs_list.append({
                            "key": key,
                            "value": parsed_value,
                            "unit": unit,
                            "display": value,
                            "group": section_name.lower().replace(' ', '_'),
                            "comparable": True,
                            "filterable": False
                        })
            
            if specs_list:
                update_data['specs'] = specs_list
            
            # 3. Structure tags
            search_data = product.get('search', {})
            keywords = search_data.get('keywords', [])
            
            tags_data = {
                "features": keywords[:20] if keywords else [],
                "rooms": [],
                "styles": [],
                "usage": [],
                "audience": [],
                "tier": None
            }
            
            # Détecter le tier basé sur le prix
            if current_price:
                if current_price < 50:
                    tags_data['tier'] = 'budget'
                elif current_price < 200:
                    tags_data['tier'] = 'mid_range'
                elif current_price < 500:
                    tags_data['tier'] = 'premium'
                else:
                    tags_data['tier'] = 'luxury'
            
            update_data['tags'] = tags_data
            
            # 4. Structure scores
            ranking = product.get('ranking', {})
            quality_score = ranking.get('quality_score', 50)
            
            scores_data = {
                "overall": quality_score,
                "value_for_money": None,
                "quality": quality_score,
                "design": None,
                "durability": None,
                "ease_of_use": None,
                "popularity": ranking.get('popularity_score'),
                "eco_score": None,
                "reviews_score": None,
                "reviews_count": 0
            }
            update_data['scores'] = scores_data
            
            # 5. Structure ai_data
            ai = product.get('ai', {})
            ai_data = {
                "summary": ai.get('summary'),
                "bullets": ai.get('bullets', []),
                "pros": [],
                "cons": [],
                "best_for": [],
                "not_for": [],
                "alternatives_ids": [],
                "accessories_ids": [],
                "bundle_suggestion": None
            }
            update_data['ai_data'] = ai_data
            
            # 6. Structure media
            media_data = {
                "primary_image": product.get('primary_image_url') or product.get('image_url') or product.get('image'),
                "images": product.get('images', []),
                "video_url": product.get('youtube_url'),
                "manual_pdf": product.get('manual_url'),
                "datasheet_pdf": product.get('datasheet_url'),
                "model_3d": None
            }
            update_data['media'] = media_data
            
            # 7. Structure meta
            meta_data = {
                "created_at": product.get('created_at') or datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "source": product.get('source') or product.get('scraped_source'),
                "source_url": product.get('source_url'),
                "data_quality": calculate_data_quality(product),
                "last_price_check": datetime.now(timezone.utc) if current_price else None,
                "active": product.get('active', True),
                "verified": False,
                "schema_version": "v3_universal"
            }
            update_data['meta'] = meta_data
            
            # 8. Mise à jour du schema_version
            update_data['schema_version'] = 'v3_universal'
            
            # Appliquer la migration
            await db.products.update_one(
                {"_id": product['_id']},
                {"$set": update_data}
            )
            
            migrated += 1
            
            if migrated % 100 == 0:
                print(f"  ✓ {migrated}/{total} produits migrés...")
                
        except Exception as e:
            errors += 1
            print(f"  ❌ Erreur produit {product.get('id', 'unknown')}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Migration terminée!")
    print(f"   - Produits migrés: {migrated}")
    print(f"   - Erreurs: {errors}")
    print(f"{'='*60}")
    
    # Créer les index
    await create_indexes(db)
    
    client.close()


def calculate_data_quality(product: dict) -> float:
    """Calcule le score de qualité des données (0-1)"""
    score = 0
    max_score = 10
    
    # Vérifier les champs importants
    if product.get('name'):
        score += 1
    if product.get('description') and len(product.get('description', '')) > 50:
        score += 1
    if product.get('brand'):
        score += 1
    if product.get('price') and product.get('price') > 0:
        score += 1
    if product.get('primary_image_url') or product.get('image_url'):
        score += 1
    if not product.get('image_missing', True):
        score += 1
    if product.get('specifications') and len(product.get('specifications', [])) > 0:
        score += 1.5
    if product.get('category_id'):
        score += 1
    if product.get('sku') or product.get('model_code'):
        score += 0.5
    if product.get('ai', {}).get('summary'):
        score += 1
    
    return min(score / max_score, 1.0)


async def load_products_from_json(db):
    """Charge les produits depuis le fichier JSON"""
    json_path = '/app/catalogue_complet.json'
    
    if not os.path.exists(json_path):
        json_path = '/app/uploads/catalogue_complet.json'
    
    if not os.path.exists(json_path):
        print(f"❌ Fichier JSON non trouvé")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    if products:
        # Supprimer les anciens produits
        await db.products.delete_many({})
        
        # Insérer les nouveaux
        await db.products.insert_many(products)
        print(f"✅ {len(products)} produits insérés")


async def create_indexes(db):
    """Crée les index pour optimiser les recherches"""
    print("\n📑 Création des index...")
    
    indexes = [
        ("id", 1),
        ("sku", 1),
        ("ean", 1),
        ("asin", 1),
        ("name", "text"),
        ("brand", 1),
        ("category_id", 1),
        ("category_path_ids", 1),
        ("active", 1),
        ("price", 1),
        ("prices.best_price.price", 1),
        ("specs.key", 1),
        ("specs.value", 1),
        ("tags.features", 1),
        ("tags.tier", 1),
        ("scores.overall", -1),
        ("image_missing", 1),
        ("schema_version", 1),
    ]
    
    for index_spec in indexes:
        try:
            if isinstance(index_spec[1], str) and index_spec[1] == "text":
                await db.products.create_index([(index_spec[0], "text")])
            else:
                await db.products.create_index([index_spec])
        except Exception as e:
            print(f"  ⚠️ Index {index_spec[0]}: {e}")
    
    # Index composé pour recherche
    try:
        await db.products.create_index([
            ("active", 1),
            ("image_missing", 1),
            ("scores.overall", -1)
        ])
    except:
        pass
    
    print("✅ Index créés")


async def verify_migration(db):
    """Vérifie la migration"""
    print("\n🔍 Vérification de la migration...")
    
    total = await db.products.count_documents({})
    with_prices = await db.products.count_documents({"prices": {"$exists": True}})
    with_specs = await db.products.count_documents({"specs": {"$exists": True, "$ne": []}})
    with_tags = await db.products.count_documents({"tags": {"$exists": True}})
    with_scores = await db.products.count_documents({"scores": {"$exists": True}})
    v3_schema = await db.products.count_documents({"schema_version": "v3_universal"})
    
    print(f"  Total produits: {total}")
    print(f"  Avec prices (affiliation): {with_prices} ({100*with_prices/total:.1f}%)")
    print(f"  Avec specs (structurées): {with_specs} ({100*with_specs/total:.1f}%)")
    print(f"  Avec tags: {with_tags} ({100*with_tags/total:.1f}%)")
    print(f"  Avec scores: {with_scores} ({100*with_scores/total:.1f}%)")
    print(f"  Schema v3: {v3_schema} ({100*v3_schema/total:.1f}%)")
    
    # Exemple de produit migré
    sample = await db.products.find_one({"schema_version": "v3_universal"}, {"_id": 0})
    if sample:
        print(f"\n📦 Exemple produit migré:")
        print(f"  Nom: {sample.get('name', 'N/A')[:50]}")
        print(f"  Prix interne: {sample.get('prices', {}).get('default', {}).get('price', 'N/A')}")
        print(f"  Specs: {len(sample.get('specs', []))} spécifications")
        print(f"  Score: {sample.get('scores', {}).get('overall', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(migrate_products())
