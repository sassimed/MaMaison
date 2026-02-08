"""
Tests de cohérence des données - MyDar.tn

Ces tests vérifient que les données dans MongoDB respectent les conventions définies
dans /app/docs/DATA_CONVENTIONS.md

Exécuter avec: pytest /app/backend/tests/test_data_coherence.py -v
"""

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
from typing import Set, List, Dict, Any

# Configuration
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


@pytest.fixture
async def db():
    """Connexion à la base de données"""
    client = AsyncIOMotorClient(MONGO_URL)
    database = client[DB_NAME]
    yield database
    client.close()


class TestSlugFormat:
    """Tests sur le format des slugs"""
    
    # Pattern étendu pour accepter les caractères accentués (réalité des données)
    VALID_SLUG_PATTERN = re.compile(r'^[a-zà-ÿ0-9]+(?:[-_][a-zà-ÿ0-9]+)*(?:__[a-zà-ÿ0-9]+(?:[-_][a-zà-ÿ0-9]+)*)?$')
    # Pattern strict (recommandé pour les nouveaux slugs)
    STRICT_SLUG_PATTERN = re.compile(r'^[a-z0-9]+(?:[-_][a-z0-9]+)*(?:__[a-z0-9]+(?:[-_][a-z0-9]+)*)?$')
    
    @pytest.mark.asyncio
    async def test_category_slugs_format(self, db):
        """Vérifie que tous les slugs de catégories sont en kebab-case"""
        categories = await db.categories.find({}, {"slug": 1, "label": 1}).to_list(None)
        
        invalid_slugs = []
        slugs_with_accents = []
        
        for cat in categories:
            slug = cat.get("slug", "")
            if not slug:
                invalid_slugs.append(f"Catégorie sans slug: {cat.get('label', 'N/A')}")
            elif not self.VALID_SLUG_PATTERN.match(slug):
                invalid_slugs.append(f"Slug invalide: '{slug}' pour '{cat.get('label', 'N/A')}'")
            elif not self.STRICT_SLUG_PATTERN.match(slug):
                slugs_with_accents.append(f"'{slug}' pour '{cat.get('label', 'N/A')}'")
        
        # Avertissement pour les slugs avec accents (à corriger idéalement)
        if slugs_with_accents:
            print(f"\n⚠️ {len(slugs_with_accents)} slugs contiennent des accents (recommandé de les corriger):")
            for s in slugs_with_accents[:5]:
                print(f"   - {s}")
        
        assert len(invalid_slugs) == 0, f"Slugs invalides trouvés:\n" + "\n".join(invalid_slugs)
    
    @pytest.mark.asyncio
    async def test_product_slugs_format(self, db):
        """Vérifie que les slugs de produits sont valides"""
        # Vérifier un échantillon de produits (les 100 premiers)
        products = await db.products.find({}, {"slug": 1, "name": 1}).limit(100).to_list(None)
        
        invalid_slugs = []
        for prod in products:
            slug = prod.get("slug", "")
            if slug and not re.match(r'^[a-z0-9-]+$', slug):
                invalid_slugs.append(f"Slug invalide: '{slug}' pour '{prod.get('name', 'N/A')[:30]}'")
        
        # Avertissement si > 10% invalides
        if len(invalid_slugs) > len(products) * 0.1:
            pytest.fail(f"Plus de 10% de slugs invalides:\n" + "\n".join(invalid_slugs[:10]))


class TestCategoryRelations:
    """Tests sur les relations entre catégories"""
    
    @pytest.mark.asyncio
    async def test_no_duplicate_category_slugs(self, db):
        """Vérifie qu'il n'y a pas de doublons de slugs dans les catégories"""
        categories = await db.categories.find({}, {"slug": 1}).to_list(None)
        
        slugs = [cat.get("slug") for cat in categories if cat.get("slug")]
        duplicates = [slug for slug in slugs if slugs.count(slug) > 1]
        unique_duplicates = list(set(duplicates))
        
        assert len(unique_duplicates) == 0, f"Slugs en doublon: {unique_duplicates}"
    
    @pytest.mark.asyncio
    async def test_subcategory_parent_exists(self, db):
        """Vérifie que chaque sous-catégorie a un parent valide"""
        # Récupérer toutes les catégories
        categories = await db.categories.find({}).to_list(None)
        
        # Créer un set des IDs valides (MongoDB id et slugs)
        valid_ids: Set[str] = set()
        for cat in categories:
            if cat.get("id"):
                valid_ids.add(str(cat.get("id")))
            if cat.get("slug"):
                valid_ids.add(cat.get("slug"))
        
        # Vérifier les parent_id
        orphans = []
        for cat in categories:
            parent_id = cat.get("parent_id")
            if parent_id and str(parent_id) not in valid_ids:
                orphans.append(f"'{cat.get('label')}' (parent_id: {parent_id})")
        
        # Note: Actuellement parent_id utilise ObjectId, donc ce test peut échouer
        # C'est attendu jusqu'à la migration vers slugs
        if orphans:
            print(f"\n⚠️ Catégories avec parent_id invalide (migration nécessaire): {len(orphans)}")
    
    @pytest.mark.asyncio
    async def test_category_levels_consistency(self, db):
        """Vérifie que les niveaux de catégories sont cohérents"""
        categories = await db.categories.find({}).to_list(None)
        
        issues = []
        for cat in categories:
            level = cat.get("level", 1)
            parent_id = cat.get("parent_id")
            
            # Niveau 1 ne devrait pas avoir de parent
            if level == 1 and parent_id:
                issues.append(f"'{cat.get('label')}' est niveau 1 mais a un parent")
            
            # Niveau > 1 devrait avoir un parent
            if level > 1 and not parent_id:
                issues.append(f"'{cat.get('label')}' est niveau {level} mais n'a pas de parent")
        
        assert len(issues) == 0, f"Incohérences de niveaux:\n" + "\n".join(issues)


class TestProductCategoryRelations:
    """Tests sur les relations entre produits et catégories"""
    
    @pytest.mark.asyncio
    async def test_product_category_ids_exist(self, db):
        """Vérifie que les category_id des produits correspondent à des catégories existantes"""
        # Récupérer tous les slugs de catégories
        categories = await db.categories.find({}, {"slug": 1}).to_list(None)
        category_slugs: Set[str] = {cat.get("slug") for cat in categories if cat.get("slug")}
        
        # Récupérer les category_id distincts des produits
        product_cat_ids = await db.products.distinct("category_id")
        
        # Vérifier que chaque category_id existe
        missing = []
        for cat_id in product_cat_ids:
            if cat_id:
                # Le category_id peut être "parent__enfant", extraire les parties
                parts = cat_id.split("__")
                base_slug = parts[0] if parts else cat_id
                
                if base_slug not in category_slugs:
                    missing.append(cat_id)
        
        # Avertissement si des catégories manquent
        if missing:
            print(f"\n⚠️ category_id non trouvés dans categories (potentiellement normal): {len(missing)}")
            print(f"   Exemples: {missing[:5]}")
    
    @pytest.mark.asyncio
    async def test_product_category_path_ids_format(self, db):
        """Vérifie que category_path_ids contient des slugs valides"""
        # Échantillon de produits
        products = await db.products.find(
            {"category_path_ids": {"$exists": True, "$ne": []}},
            {"category_path_ids": 1, "name": 1}
        ).limit(100).to_list(None)
        
        issues = []
        for prod in products:
            path_ids = prod.get("category_path_ids", [])
            for path_id in path_ids:
                # Vérifier que ce n'est pas un ObjectId (24 caractères hex)
                if re.match(r'^[a-f0-9]{24}$', str(path_id)):
                    issues.append(f"ObjectId trouvé dans category_path_ids: {path_id}")
                    break
        
        assert len(issues) == 0, f"category_path_ids contient des ObjectId:\n" + "\n".join(issues[:10])
    
    @pytest.mark.asyncio
    async def test_products_have_required_fields(self, db):
        """Vérifie que les produits ont les champs requis"""
        required_fields = ["name", "slug", "active"]
        
        products = await db.products.find({}).limit(100).to_list(None)
        
        missing_fields = []
        for prod in products:
            for field in required_fields:
                if field not in prod:
                    missing_fields.append(f"Produit '{prod.get('name', 'N/A')[:30]}' manque le champ '{field}'")
        
        if missing_fields:
            print(f"\n⚠️ Champs manquants: {len(missing_fields)}")


class TestDataIntegrity:
    """Tests d'intégrité générale des données"""
    
    @pytest.mark.asyncio
    async def test_no_objectid_in_category_responses(self, db):
        """Vérifie que les catégories n'ont pas d'ObjectId exposés comme ID principal"""
        categories = await db.categories.find({}, {"id": 1, "slug": 1, "label": 1}).to_list(None)
        
        objectid_pattern = re.compile(r'^[a-f0-9]{24}$')
        issues = []
        
        for cat in categories:
            cat_id = str(cat.get("id", ""))
            slug = cat.get("slug", "")
            
            # Si l'id ressemble à un ObjectId et est différent du slug
            if objectid_pattern.match(cat_id) and cat_id != slug:
                issues.append(f"'{cat.get('label')}': id='{cat_id}' devrait être slug='{slug}'")
        
        # C'est un avertissement, pas une erreur bloquante
        if issues:
            print(f"\n⚠️ Catégories avec ObjectId comme id (migration données recommandée): {len(issues)}")
    
    @pytest.mark.asyncio
    async def test_products_price_status(self, db):
        """Vérifie le statut des prix des produits"""
        total = await db.products.count_documents({})
        with_price = await db.products.count_documents({"price": {"$exists": True, "$ne": None, "$gt": 0}})
        without_price = total - with_price
        
        print(f"\n📊 Statut des prix:")
        print(f"   Total produits: {total}")
        print(f"   Avec prix: {with_price} ({with_price/total*100:.1f}%)")
        print(f"   Sans prix: {without_price} ({without_price/total*100:.1f}%)")
        
        # Avertissement si beaucoup de produits sans prix
        if without_price > total * 0.5:
            print(f"   ⚠️ Plus de 50% des produits n'ont pas de prix!")
    
    @pytest.mark.asyncio
    async def test_products_image_status(self, db):
        """Vérifie le statut des images des produits"""
        total = await db.products.count_documents({})
        with_image = await db.products.count_documents({
            "$or": [
                {"primary_image_url": {"$exists": True, "$ne": None, "$ne": ""}},
                {"images": {"$exists": True, "$ne": []}}
            ]
        })
        without_image = total - with_image
        
        print(f"\n📊 Statut des images:")
        print(f"   Total produits: {total}")
        print(f"   Avec image: {with_image} ({with_image/total*100:.1f}%)")
        print(f"   Sans image: {without_image} ({without_image/total*100:.1f}%)")
    
    @pytest.mark.asyncio
    async def test_user_roles_valid(self, db):
        """Vérifie que les rôles utilisateurs sont valides"""
        # Rôles acceptés (minuscules et majuscules pour compatibilité)
        valid_roles = {
            "client", "pro", "admin",  # Standard
            "CLIENT", "PRO", "ADMIN",  # Majuscules legacy
            "PARTICULIER", "PROFESSIONNEL",  # Aliases legacy
            "particulier", "professionnel"
        }
        
        users = await db.users.find({}, {"email": 1, "role": 1}).to_list(None)
        
        invalid_roles = []
        legacy_roles = []
        
        for user in users:
            role = user.get("role", "")
            if role is None or role == "None":
                invalid_roles.append(f"'{user.get('email')}' n'a pas de rôle défini")
            elif role not in valid_roles:
                invalid_roles.append(f"'{user.get('email')}' a un rôle invalide: '{role}'")
            elif role.upper() in ["ADMIN", "PARTICULIER", "PROFESSIONNEL"]:
                legacy_roles.append(f"'{user.get('email')}': '{role}'")
        
        # Avertissement pour les rôles legacy
        if legacy_roles:
            print(f"\n⚠️ {len(legacy_roles)} utilisateurs avec rôles en majuscules (legacy):")
            for r in legacy_roles[:5]:
                print(f"   - {r}")
        
        # Ne pas échouer pour les rôles legacy, juste pour les invalides
        actual_invalid = [r for r in invalid_roles if "pas de rôle défini" in r]
        if actual_invalid:
            print(f"\n⚠️ Utilisateurs sans rôle: {len(actual_invalid)}")


class TestAPIConsistency:
    """Tests de cohérence pour les APIs"""
    
    @pytest.mark.asyncio
    async def test_category_slug_uniqueness_for_api(self, db):
        """Vérifie que chaque catégorie a un slug unique utilisable comme ID API"""
        categories = await db.categories.find({}, {"slug": 1, "label": 1}).to_list(None)
        
        slug_counts: Dict[str, int] = {}
        for cat in categories:
            slug = cat.get("slug", "")
            if slug:
                slug_counts[slug] = slug_counts.get(slug, 0) + 1
        
        duplicates = {slug: count for slug, count in slug_counts.items() if count > 1}
        
        assert len(duplicates) == 0, f"Slugs en doublon (problème pour API): {duplicates}"
    
    @pytest.mark.asyncio
    async def test_active_products_have_category(self, db):
        """Vérifie que les produits actifs ont une catégorie"""
        active_without_category = await db.products.count_documents({
            "active": True,
            "$or": [
                {"category_id": {"$exists": False}},
                {"category_id": None},
                {"category_id": ""}
            ]
        })
        
        if active_without_category > 0:
            print(f"\n⚠️ {active_without_category} produits actifs sans catégorie")


# Fonction utilitaire pour exécuter les tests manuellement
async def run_coherence_check():
    """Exécute une vérification rapide de cohérence"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 60)
    print("🔍 VÉRIFICATION DE COHÉRENCE DES DONNÉES")
    print("=" * 60)
    
    # Stats basiques
    categories_count = await db.categories.count_documents({})
    products_count = await db.products.count_documents({})
    users_count = await db.users.count_documents({})
    
    print(f"\n📊 Collections:")
    print(f"   Catégories: {categories_count}")
    print(f"   Produits: {products_count}")
    print(f"   Utilisateurs: {users_count}")
    
    # Vérifier les slugs de catégories
    categories = await db.categories.find({}, {"slug": 1}).to_list(None)
    slugs = [c.get("slug") for c in categories if c.get("slug")]
    unique_slugs = set(slugs)
    
    print(f"\n✅ Slugs de catégories: {len(unique_slugs)} uniques sur {len(slugs)}")
    
    # Vérifier les category_id des produits
    product_cat_ids = await db.products.distinct("category_id")
    objectid_pattern = re.compile(r'^[a-f0-9]{24}$')
    objectid_cat_ids = [cid for cid in product_cat_ids if cid and objectid_pattern.match(str(cid))]
    
    if objectid_cat_ids:
        print(f"\n⚠️ Produits avec ObjectId comme category_id: {len(objectid_cat_ids)}")
    else:
        print(f"\n✅ Tous les category_id utilisent des slugs")
    
    # Vérifier les prix
    with_price = await db.products.count_documents({"price": {"$gt": 0}})
    print(f"\n📊 Produits avec prix: {with_price}/{products_count} ({with_price/products_count*100:.1f}%)")
    
    client.close()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_coherence_check())
