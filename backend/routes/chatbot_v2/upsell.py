"""
Logique Cross-sell et Upsell intelligente
"""

from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


class UpsellEngine:
    """Moteur de recommandations cross-sell et upsell"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
        # Règles d'upsell (produit supérieur)
        self.upsell_rules = {
            # Caméra 2MP → 4MP ou 5MP
            "camera_resolution": {
                "trigger": ["2mp", "2 mp", "1080p"],
                "suggest": ["4mp", "5mp", "4k"],
                "reason_fr": "Pour une meilleure qualité d'image et un zoom numérique plus efficace",
                "reason_ar": "لجودة صورة أفضل وزوم رقمي أكثر فعالية"
            },
            # NVR 4 voies → 8 voies
            "nvr_channels": {
                "trigger": ["4 voies", "4 canaux", "4ch"],
                "suggest": ["8 voies", "8 canaux", "8ch"],
                "reason_fr": "Pour pouvoir ajouter des caméras plus tard sans changer d'enregistreur",
                "reason_ar": "باش تنجم تزيد كاميرات مستقبلاً بلا ما تبدل المسجل"
            },
            # RTS → IO (Somfy)
            "somfy_protocol": {
                "trigger": ["rts"],
                "suggest": ["io", "io-homecontrol"],
                "reason_fr": "Pour avoir le retour d'état et une meilleure intégration domotique",
                "reason_ar": "باش تعرف حالة الستور وتدمجو مع الدوموتيك"
            }
        }
        
        # Règles de cross-sell (produits complémentaires)
        self.crosssell_rules = {
            "camera": [
                {
                    "product_type": "nvr",
                    "query": {"name": {"$regex": "nvr|enregistreur", "$options": "i"}},
                    "reason_fr": "Pour enregistrer et revoir les vidéos",
                    "reason_ar": "باش تسجل وتراجع الفيديوهات"
                },
                {
                    "product_type": "hdd",
                    "query": {"name": {"$regex": "disque|hdd|stockage", "$options": "i"}},
                    "reason_fr": "Pour le stockage des enregistrements",
                    "reason_ar": "لتخزين التسجيلات"
                }
            ],
            "nvr": [
                {
                    "product_type": "camera",
                    "query": {"name": {"$regex": "cam[ée]ra|dome|bullet", "$options": "i"}},
                    "reason_fr": "Caméras compatibles pour votre enregistreur",
                    "reason_ar": "كاميرات متوافقة مع المسجل متاعك"
                }
            ],
            "visiophone": [
                {
                    "product_type": "ecran",
                    "query": {"name": {"$regex": "moniteur|[ée]cran|class", "$options": "i"}, "category_path_ids": "videophonie"},
                    "reason_fr": "Écran supplémentaire pour une autre pièce",
                    "reason_ar": "شاشة إضافية لبيت آخر"
                }
            ],
            "centrale_alarme": [
                {
                    "product_type": "detecteur",
                    "query": {"name": {"$regex": "d[ée]tecteur|capteur|pir", "$options": "i"}},
                    "reason_fr": "Détecteurs pour protéger vos zones",
                    "reason_ar": "كاشفات لحماية المناطق"
                },
                {
                    "product_type": "sirene",
                    "query": {"name": {"$regex": "sir[èe]ne", "$options": "i"}},
                    "reason_fr": "Sirène pour alerter en cas d'intrusion",
                    "reason_ar": "صفارة للتنبيه في حالة اقتحام"
                }
            ],
            "motorisation": [
                {
                    "product_type": "telecommande",
                    "query": {"name": {"$regex": "t[ée]l[ée]commande|keygo|situo", "$options": "i"}},
                    "reason_fr": "Télécommande supplémentaire",
                    "reason_ar": "تيليكوموند إضافية"
                }
            ]
        }
    
    async def get_upsell_suggestions(
        self,
        product: Dict,
        language: str = "fr"
    ) -> List[Dict]:
        """
        Suggère des produits supérieurs (upsell)
        """
        suggestions = []
        name = product.get("name", "").lower()
        brand = product.get("brand", "")
        category = product.get("category_path_ids", "")
        
        for rule_name, rule in self.upsell_rules.items():
            # Vérifier si le produit correspond au trigger
            if any(trigger in name for trigger in rule["trigger"]):
                # Chercher un produit supérieur
                suggest_patterns = "|".join(rule["suggest"])
                query = {
                    "active": True,
                    "image_missing": False,
                    "name": {"$regex": suggest_patterns, "$options": "i"},
                }
                
                # Même catégorie
                if category:
                    if isinstance(category, list):
                        query["category_path_ids"] = {"$in": category}
                    else:
                        query["category_path_ids"] = category
                
                # Même marque si possible
                if brand:
                    query["brand"] = brand
                
                # Chercher le produit
                better_product = await self.db.products.find_one(
                    query,
                    {"_id": 0}
                )
                
                if better_product and better_product.get("id") != product.get("id"):
                    reason = rule.get(f"reason_{language}", rule.get("reason_fr"))
                    suggestions.append({
                        "type": "upsell",
                        "product": better_product,
                        "reason": reason
                    })
        
        return suggestions
    
    async def get_crosssell_suggestions(
        self,
        product: Dict,
        language: str = "fr",
        limit: int = 3
    ) -> List[Dict]:
        """
        Suggère des produits complémentaires (cross-sell)
        """
        suggestions = []
        name = product.get("name", "").lower()
        brand = product.get("brand", "")
        
        # Identifier le type de produit
        product_type = self._identify_product_type(name)
        
        if not product_type or product_type not in self.crosssell_rules:
            return suggestions
        
        rules = self.crosssell_rules[product_type]
        
        for rule in rules:
            query = rule["query"].copy()
            query["active"] = True
            query["image_missing"] = False
            
            # Préférer la même marque
            if brand:
                query_with_brand = {**query, "brand": brand}
                complementary = await self.db.products.find_one(
                    query_with_brand,
                    {"_id": 0}
                )
                if not complementary:
                    complementary = await self.db.products.find_one(
                        query,
                        {"_id": 0}
                    )
            else:
                complementary = await self.db.products.find_one(
                    query,
                    {"_id": 0}
                )
            
            if complementary and complementary.get("id") != product.get("id"):
                reason = rule.get(f"reason_{language}", rule.get("reason_fr"))
                suggestions.append({
                    "type": "crosssell",
                    "product_type": rule["product_type"],
                    "product": complementary,
                    "reason": reason
                })
            
            if len(suggestions) >= limit:
                break
        
        return suggestions
    
    async def get_bundle_suggestion(
        self,
        products: List[Dict],
        language: str = "fr"
    ) -> Optional[Dict]:
        """
        Suggère un kit/bundle si pertinent
        """
        # Identifier les types de produits dans le panier
        types = set()
        for p in products:
            name = p.get("name", "").lower()
            ptype = self._identify_product_type(name)
            if ptype:
                types.add(ptype)
        
        # Si on a caméra + nvr, suggérer un kit complet
        if "camera" in types and "nvr" not in types:
            # Chercher un kit
            kit = await self.db.products.find_one(
                {
                    "active": True,
                    "image_missing": False,
                    "name": {"$regex": "kit|pack|ensemble", "$options": "i"},
                    "category_path_ids": "videosurveillance"
                },
                {"_id": 0}
            )
            
            if kit:
                reason = "Un kit complet peut être plus avantageux" if language == "fr" else "كيت كامل ممكن يكون أفضل"
                return {
                    "type": "bundle",
                    "product": kit,
                    "reason": reason
                }
        
        return None
    
    def _identify_product_type(self, name: str) -> Optional[str]:
        """Identifie le type de produit à partir du nom"""
        name = name.lower()
        
        if any(kw in name for kw in ["caméra", "camera", "dome", "bullet", "ipc-", "hac-"]):
            return "camera"
        if any(kw in name for kw in ["nvr", "enregistreur"]):
            return "nvr"
        if any(kw in name for kw in ["dvr", "xvr"]):
            return "dvr"
        if any(kw in name for kw in ["visiophone", "vidéophone", "interphone"]):
            return "visiophone"
        if any(kw in name for kw in ["centrale", "alarme"]):
            return "centrale_alarme"
        if any(kw in name for kw in ["moteur", "motorisation", "volet", "portail"]):
            return "motorisation"
        if any(kw in name for kw in ["switch", "routeur"]):
            return "reseau"
        
        return None
    
    async def get_smart_recommendations(
        self,
        product: Dict,
        cart_items: List[Dict],
        language: str = "fr"
    ) -> Dict:
        """
        Retourne des recommandations intelligentes combinées
        """
        recommendations = {
            "upsell": [],
            "crosssell": [],
            "bundle": None,
            "warnings": []
        }
        
        # Upsell
        upsell = await self.get_upsell_suggestions(product, language)
        recommendations["upsell"] = upsell[:2]
        
        # Cross-sell (en évitant les doublons avec le panier)
        cart_ids = {p.get("id") for p in cart_items}
        crosssell = await self.get_crosssell_suggestions(product, language)
        recommendations["crosssell"] = [
            cs for cs in crosssell 
            if cs["product"].get("id") not in cart_ids
        ][:3]
        
        # Bundle
        all_products = cart_items + [product]
        bundle = await self.get_bundle_suggestion(all_products, language)
        recommendations["bundle"] = bundle
        
        return recommendations
