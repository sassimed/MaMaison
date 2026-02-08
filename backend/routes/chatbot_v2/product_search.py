"""
Recherche intelligente de produits pour le Chatbot Conseiller
"""

from typing import List, Dict, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import re


class ProductSearchEngine:
    """Moteur de recherche produits intelligent"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
        # Mapping catégorie vers category_path_ids
        self.category_mapping = {
            "videosurveillance": "videosurveillance",
            "vidéosurveillance": "videosurveillance",
            "camera": "videosurveillance",
            "caméra": "videosurveillance",
            "nvr": "videosurveillance",
            "dvr": "videosurveillance",
            "videophonie": "videophonie",
            "vidéophonie": "videophonie",
            "visiophone": "videophonie",
            "interphone": "videophonie",
            "alarme": "alarme",
            "controle-d-accès": "controle-d-accès",
            "controle d'acces": "controle-d-accès",
            "pointeuse": "controle-d-accès",
            "badge": "controle-d-accès",
            "motorisation": "motorisation",
            "volet": "motorisation",
            "portail": "motorisation",
            "somfy": "motorisation",
            "reseau": "reseau",
            "réseau": "reseau",
            "switch": "reseau",
            "routeur": "reseau",
            "interrupteur": "interrupteur",
            "prise": "prise",
            "eclairage": "eclairage",
            "éclairage": "eclairage",
        }
        
        # Mapping connectivité
        self.connectivity_mapping = {
            "wifi": "Sans fil",
            "wi-fi": "Sans fil",
            "sans fil": "Sans fil",
            "wireless": "Sans fil",
            "filaire": "Filaire",
            "cable": "Filaire",
            "câble": "Filaire",
            "ethernet": "Filaire",
            "poe": "Filaire",
            "hybride": "Hybride",
        }
        
        # Sous-catégories par type de produit
        self.subcategory_keywords = {
            "camera": ["cameras", "camera"],
            "nvr": ["enregistreurs", "nvr"],
            "dvr": ["enregistreurs", "dvr", "xvr"],
            "dome": ["cameras"],
            "bullet": ["cameras"],
            "ptz": ["cameras"],
        }
        
        # Mots-clés à exclure (accessoires)
        self.exclude_keywords = {
            "support", "câble", "cable", "adaptateur", "alimentation",
            "vis", "connecteur", "rallonge", "pile", "batterie",
            "disque dur", "hdd", "ssd", "seagate", "western digital"
        }
    
    async def search_products(
        self,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        environment: Optional[str] = None,
        connectivity: Optional[str] = None,
        brand: Optional[str] = None,
        budget_max: Optional[float] = None,
        keywords: Optional[List[str]] = None,
        product_type: Optional[str] = None,
        limit: int = 10
    ) -> Tuple[List[Dict], Dict]:
        """
        Recherche intelligente de produits avec filtres
        Retourne (produits, metadata)
        """
        metadata = {
            "filters_applied": [],
            "total_found": 0,
            "search_method": "filtered"
        }
        
        # Construire la requête de base
        query = {"active": True, "image_missing": False}
        and_conditions = []
        
        # Filtre catégorie
        if category:
            cat_id = self.category_mapping.get(category.lower(), category.lower())
            query["category_path_ids"] = cat_id
            metadata["filters_applied"].append(f"category={cat_id}")
        
        # Filtre environnement (intérieur/extérieur)
        if environment:
            if environment.lower() in ["exterieur", "extérieur", "outdoor", "خارج", "برا"]:
                # Produits IP65+ pour extérieur - condition OR
                and_conditions.append({
                    "$or": [
                        {"name": {"$regex": "ext[ée]rieur|outdoor|ip6[567]", "$options": "i"}},
                        {"description": {"$regex": "ext[ée]rieur|outdoor|ip6[567]", "$options": "i"}},
                        {"attributes_norm.environment": {"$regex": "ext|outdoor", "$options": "i"}},
                    ]
                })
                metadata["filters_applied"].append("environment=exterieur")
            elif environment.lower() in ["interieur", "intérieur", "indoor", "داخل"]:
                metadata["filters_applied"].append("environment=interieur")
        
        # Filtre connectivité
        if connectivity:
            conn_value = self.connectivity_mapping.get(connectivity.lower(), connectivity)
            query["attributes_norm.connectivity"] = conn_value
            metadata["filters_applied"].append(f"connectivity={conn_value}")
        
        # Filtre marque
        if brand:
            query["brand"] = {"$regex": brand, "$options": "i"}
            metadata["filters_applied"].append(f"brand={brand}")
        
        # Filtre budget
        if budget_max and budget_max > 0:
            query["price"] = {"$gt": 0, "$lte": budget_max}
            metadata["filters_applied"].append(f"budget_max={budget_max}")
        
        # Filtre type de produit (camera, nvr, etc.)
        if product_type:
            type_lower = product_type.lower()
            if type_lower in ["camera", "caméra"]:
                query["name"] = {"$regex": "cam[ée]ra|dome|bullet|tourelle|eyeball|ipc-|hac-", "$options": "i"}
            elif type_lower in ["nvr", "enregistreur"]:
                query["name"] = {"$regex": "nvr|enregistreur", "$options": "i"}
            elif type_lower == "dvr":
                query["name"] = {"$regex": "dvr|xvr", "$options": "i"}
            metadata["filters_applied"].append(f"type={product_type}")
        
        # Recherche par mots-clés
        if keywords and len(keywords) > 0:
            keyword_conditions = []
            for kw in keywords:
                if kw.lower() not in self.exclude_keywords:
                    keyword_conditions.append({"name": {"$regex": kw, "$options": "i"}})
                    keyword_conditions.append({"description": {"$regex": kw, "$options": "i"}})
            if keyword_conditions:
                and_conditions.append({"$or": keyword_conditions})
        
        # Combiner toutes les conditions AND
        if and_conditions:
            query["$and"] = and_conditions
        
        # Exécuter la requête
        try:
            products = await self.db.products.find(
                query,
                {"_id": 0}
            ).sort([
                ("ranking.quality_score", -1),
                ("featured", -1),
                ("price", 1)
            ]).limit(limit * 2).to_list(limit * 2)
            
            # Post-filtrage pour exclure les accessoires
            filtered = []
            for p in products:
                name_lower = p.get("name", "").lower()
                if not any(excl in name_lower for excl in self.exclude_keywords):
                    filtered.append(p)
                    if len(filtered) >= limit:
                        break
            
            metadata["total_found"] = len(filtered)
            return filtered, metadata
            
        except Exception as e:
            print(f"[ProductSearch Error] {e}")
            return [], metadata
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Récupère un produit par son ID"""
        try:
            product = await self.db.products.find_one(
                {"id": product_id},
                {"_id": 0}
            )
            return product
        except Exception as e:
            print(f"[GetProduct Error] {e}")
            return None
    
    async def get_compatible_products(
        self,
        product: Dict,
        limit: int = 5
    ) -> List[Dict]:
        """
        Trouve les produits compatibles/complémentaires
        """
        compatible = []
        category = product.get("category", "")
        name = product.get("name", "").lower()
        brand = product.get("brand", "")
        
        # Règles de compatibilité
        if "caméra" in name or "camera" in name:
            # Caméra → NVR compatible
            nvr_query = {
                "active": True,
                "image_missing": False,
                "name": {"$regex": "nvr|enregistreur", "$options": "i"},
            }
            if brand:
                nvr_query["brand"] = brand
            
            nvrs = await self.db.products.find(
                nvr_query, {"_id": 0}
            ).sort("ranking.quality_score", -1).limit(3).to_list(3)
            
            for nvr in nvrs:
                nvr["compatibility_reason"] = "NVR compatible pour enregistrer cette caméra"
            compatible.extend(nvrs)
            
        elif "nvr" in name or "enregistreur" in name:
            # NVR → Caméras compatibles + HDD
            cam_query = {
                "active": True,
                "image_missing": False,
                "name": {"$regex": "cam[ée]ra|dome|bullet", "$options": "i"},
            }
            if brand:
                cam_query["brand"] = brand
            
            cameras = await self.db.products.find(
                cam_query, {"_id": 0}
            ).sort("ranking.quality_score", -1).limit(3).to_list(3)
            
            for cam in cameras:
                cam["compatibility_reason"] = "Caméra compatible avec cet enregistreur"
            compatible.extend(cameras)
            
        elif "visiophone" in name or "interphone" in name:
            # Visiophone → Écran supplémentaire
            screen_query = {
                "active": True,
                "image_missing": False,
                "category_path_ids": "videophonie",
                "name": {"$regex": "moniteur|[ée]cran|class", "$options": "i"},
            }
            
            screens = await self.db.products.find(
                screen_query, {"_id": 0}
            ).sort("ranking.quality_score", -1).limit(2).to_list(2)
            
            for screen in screens:
                screen["compatibility_reason"] = "Écran supplémentaire pour cette installation"
            compatible.extend(screens)
            
        elif "alarme" in category.lower() or "centrale" in name:
            # Centrale alarme → Détecteurs + Sirène
            detector_query = {
                "active": True,
                "image_missing": False,
                "category_path_ids": "alarme",
                "name": {"$regex": "d[ée]tecteur|capteur|sirène", "$options": "i"},
            }
            
            detectors = await self.db.products.find(
                detector_query, {"_id": 0}
            ).sort("ranking.quality_score", -1).limit(3).to_list(3)
            
            for det in detectors:
                det["compatibility_reason"] = "Composant compatible pour cette centrale"
            compatible.extend(detectors)
        
        return compatible[:limit]
    
    async def get_category_summary(self) -> Dict[str, int]:
        """Résumé des catégories avec comptages"""
        try:
            pipeline = [
                {"$match": {"active": True, "image_missing": False}},
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            result = await self.db.products.aggregate(pipeline).to_list(50)
            return {r["_id"]: r["count"] for r in result if r["_id"]}
        except Exception:
            return {}
    
    async def get_brands_for_category(self, category: str) -> List[str]:
        """Liste des marques disponibles pour une catégorie"""
        try:
            cat_id = self.category_mapping.get(category.lower(), category.lower())
            pipeline = [
                {"$match": {"category_path_ids": cat_id, "active": True}},
                {"$group": {"_id": "$brand"}},
                {"$sort": {"_id": 1}}
            ]
            result = await self.db.products.aggregate(pipeline).to_list(50)
            return [r["_id"] for r in result if r["_id"]]
        except Exception:
            return []
