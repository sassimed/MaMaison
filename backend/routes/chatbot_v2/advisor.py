"""
Conseiller Intelligent - Logique principale
Gère le flux de conversation et les décisions
"""

from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import re
import json

from .models import (
    ConversationState, ConversationPhase, UserNeed, 
    ProductRecommendation
)
from .prompts import (
    DISCOVERY_QUESTIONS, TECHNICAL_EXPLANATIONS,
    GREETING_MESSAGES
)
from .product_search import ProductSearchEngine
from .compatibility import CompatibilityChecker
from .upsell import UpsellEngine


class AdvisorEngine:
    """Moteur de conseil intelligent"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.search_engine = ProductSearchEngine(db)
        self.compatibility = CompatibilityChecker()
        self.upsell_engine = UpsellEngine(db)
        
        # Patterns pour détecter les intentions
        self.intent_patterns = {
            "greeting": [
                r"^(bonjour|bonsoir|salut|hello|hi|عسلامة|سلام|مرحبا)",
            ],
            "search": [
                r"(cherche|veux|besoin|trouve|نحب|نلوج|عندك)",
                r"(caméra|camera|كاميرا|nvr|alarme|visiophone)",
            ],
            "explain": [
                r"(c'est quoi|qu'est-ce que|explique|معناها|شنوة)",
                r"(poe|nvr|dvr|ip67|onvif|h\.?265|rts|io|zigbee)",
            ],
            "compare": [
                r"(compare|différence|vs|versus|قارن|الفرق)",
            ],
            "compatibility": [
                r"(compatible|marche avec|fonctionne avec|يخدم مع|متوافق)",
            ],
            "price": [
                r"(prix|coût|budget|سعر|قداش|كم)",
            ],
            "number_response": [
                r"^[0-9]$",
            ],
        }
        
        # Mapping catégorie depuis le message
        self.category_keywords = {
            "caméra": "videosurveillance",
            "camera": "videosurveillance",
            "كاميرا": "videosurveillance",
            "nvr": "videosurveillance",
            "dvr": "videosurveillance",
            "surveillance": "videosurveillance",
            "visiophone": "videophonie",
            "interphone": "videophonie",
            "sonnette": "videophonie",
            "alarme": "alarme",
            "détecteur": "alarme",
            "intrusion": "alarme",
            "pointeuse": "controle-d-accès",
            "badge": "controle-d-accès",
            "accès": "controle-d-accès",
            "empreinte": "controle-d-accès",
            "volet": "motorisation",
            "store": "motorisation",
            "portail": "motorisation",
            "somfy": "motorisation",
            "moteur": "motorisation",
            "switch": "reseau",
            "routeur": "reseau",
            "wifi": "reseau",
        }
    
    def detect_language(self, message: str) -> str:
        """Détecte la langue du message (fr ou ar)"""
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', message))
        if arabic_chars > 2:
            return "ar"
        return "fr"
    
    def detect_intent(self, message: str) -> str:
        """Détecte l'intention principale du message"""
        msg_lower = message.lower().strip()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, msg_lower, re.IGNORECASE):
                    return intent
        
        return "search"  # Par défaut, on considère que c'est une recherche
    
    def extract_criteria_from_message(self, message: str, state: ConversationState) -> UserNeed:
        """Extrait les critères de recherche du message"""
        need = state.user_need.model_copy()
        msg_lower = message.lower()
        
        # Détecter la catégorie
        for keyword, category in self.category_keywords.items():
            if keyword in msg_lower:
                need.category = category
                break
        
        # Détecter l'environnement
        if any(kw in msg_lower for kw in ["extérieur", "exterieur", "outdoor", "خارج", "برا"]):
            need.environment = "exterieur"
        elif any(kw in msg_lower for kw in ["intérieur", "interieur", "indoor", "داخل"]):
            need.environment = "interieur"
        
        # Détecter la connectivité
        if any(kw in msg_lower for kw in ["wifi", "wi-fi", "sans fil", "ويفي", "بلا خيط"]):
            need.connectivity = "wifi"
        elif any(kw in msg_lower for kw in ["filaire", "câble", "cable", "poe", "بالخيط"]):
            need.connectivity = "filaire"
        
        # Détecter la marque
        brands = ["dahua", "somfy", "hikvision", "zkteco", "inim", "ruijie"]
        for brand in brands:
            if brand in msg_lower:
                need.brand_preference = brand
                break
        
        # Détecter le budget
        price_match = re.search(r"(\d+)\s*(dt|dinars?|تند)", msg_lower)
        if price_match:
            need.budget_max = float(price_match.group(1))
        
        return need
    
    def process_numeric_response(
        self, 
        message: str, 
        state: ConversationState,
        last_question: Optional[str]
    ) -> UserNeed:
        """Traite une réponse numérique à une question"""
        need = state.user_need.model_copy()
        num = int(message.strip())
        
        if not last_question:
            return need
        
        # Identifier le type de question posée
        q_lower = last_question.lower()
        
        if any(kw in q_lower for kw in ["intérieur", "extérieur", "داخل", "خارج"]):
            if num == 1:
                need.environment = "interieur"
            elif num == 2:
                need.environment = "exterieur"
            elif num == 3:
                need.environment = "both"
        
        elif any(kw in q_lower for kw in ["wifi", "filaire", "بلا خيط", "بالكابل"]):
            if num == 1:
                need.connectivity = "wifi"
            elif num == 2:
                need.connectivity = "filaire"
        
        elif any(kw in q_lower for kw in ["maison", "commerce", "bureau", "دار", "محل"]):
            if num == 1:
                need.use_case = "maison"
            elif num == 2:
                need.use_case = "commerce"
            elif num == 3:
                need.use_case = "entrepot"
        
        elif any(kw in q_lower for kw in ["enregistreur", "nvr", "مسجل"]):
            if num == 1:
                need.specific_features.append("has_recorder")
            elif num == 2:
                need.specific_features.append("needs_full_system")
        
        return need
    
    def get_next_question(
        self, 
        state: ConversationState
    ) -> Optional[Tuple[str, str, List[str]]]:
        """
        Retourne la prochaine question à poser
        Returns: (question_id, question_text, options) ou None si toutes les infos sont là
        """
        need = state.user_need
        lang = state.language
        
        # Pas de catégorie = on ne peut pas poser de questions spécifiques
        if not need.category:
            return None
        
        # Récupérer les questions pour cette catégorie
        cat_questions = DISCOVERY_QUESTIONS.get(need.category, {}).get(lang, [])
        
        # Parcourir toutes les questions et retourner la première non posée
        for question_id, question_text, options in cat_questions:
            # Skip si déjà posée
            if question_id in state.questions_asked:
                continue
            
            # Skip si l'info est déjà connue
            if question_id == "environment" and need.environment:
                continue
            if question_id == "connectivity" and need.connectivity:
                continue
            if question_id == "housing_type" and "housing_type" in need.specific_features:
                continue
            
            # Cette question n'a pas été posée et l'info n'est pas connue
            return (question_id, question_text, options)
        
        return None
    
    def has_enough_info(self, state: ConversationState) -> bool:
        """Vérifie si on a assez d'informations pour recommander"""
        need = state.user_need
        
        # Minimum: catégorie
        if not need.category:
            return False
        
        # Pour vidéosurveillance: on veut environnement ET connectivité (ou au moins 2 questions posées)
        if need.category == "videosurveillance":
            # Si les deux critères sont remplis, OK
            if need.environment and need.connectivity:
                return True
            # Sinon, on continue à poser des questions jusqu'à 2 minimum
            return len(state.questions_asked) >= 2
        
        # Pour alarme: type de propriété
        if need.category == "alarme":
            return len(state.questions_asked) >= 1
        
        # Pour vidéophonie: au moins 1 question
        if need.category == "videophonie":
            return len(state.questions_asked) >= 1
        
        # Pour contrôle d'accès: type d'accès
        if need.category == "controle-d-accès":
            return len(state.questions_asked) >= 1
        
        # Pour motorisation: type de motorisation
        if need.category == "motorisation":
            return len(state.questions_asked) >= 1
        
        # Pour les autres catégories, la catégorie suffit après 1 question ou critère
        return len(state.questions_asked) >= 1 or need.brand_preference or need.connectivity
    
    def get_technical_explanation(
        self, 
        term: str, 
        language: str
    ) -> Optional[str]:
        """Retourne l'explication d'un terme technique"""
        term_lower = term.lower().replace(".", "").replace("-", "")
        
        for key, explanations in TECHNICAL_EXPLANATIONS.items():
            if key in term_lower or term_lower in key:
                return explanations.get(language, explanations.get("fr"))
        
        return None
    
    async def get_product_recommendations(
        self, 
        state: ConversationState,
        limit: int = 5
    ) -> Tuple[List[Dict], Dict]:
        """
        Obtient les recommandations de produits basées sur le besoin
        """
        need = state.user_need
        
        products, metadata = await self.search_engine.search_products(
            category=need.category,
            environment=need.environment,
            connectivity=need.connectivity,
            brand=need.brand_preference,
            budget_max=need.budget_max,
            limit=limit
        )
        
        # Vérifier la compatibilité avec l'environnement
        if need.environment == "exterieur":
            validated_products = []
            warnings = []
            for p in products:
                compatible, warns = self.compatibility.check_outdoor_compatibility(
                    p, need.environment
                )
                if compatible:
                    validated_products.append(p)
                else:
                    warnings.extend(warns)
            
            metadata["compatibility_warnings"] = warnings
            products = validated_products if validated_products else products
        
        return products, metadata
    
    async def get_complementary_products(
        self, 
        product: Dict,
        state: ConversationState
    ) -> List[Dict]:
        """Obtient les produits complémentaires"""
        crosssell = await self.upsell_engine.get_crosssell_suggestions(
            product, 
            language=state.language,
            limit=3
        )
        return [cs["product"] for cs in crosssell]
    
    def format_product_for_response(
        self, 
        product: Dict, 
        why_recommended: str,
        language: str
    ) -> str:
        """Formate un produit pour la réponse"""
        name = product.get("name", "Produit")
        brand = product.get("brand", "")
        price = product.get("price")
        product_id = product.get("id", "")
        
        price_str = f"{price:.3f} DT" if price else ("Prix sur demande" if language == "fr" else "سعر على الطلب")
        
        # Extraire 2-3 caractéristiques clés
        features = []
        desc = product.get("description", "")
        if desc:
            # Prendre les premières caractéristiques utiles
            lines = desc.split("\n")[:3]
            for line in lines:
                if line.strip() and len(line) < 100:
                    features.append(f"• {line.strip()}")
        
        features_text = "\n".join(features[:2]) if features else ""
        
        result = f"""**{name}** — {brand}
{why_recommended}
{features_text}
💰 {price_str}
{{{{PRODUCT_ACTIONS:{product_id}}}}}"""
        
        return result
    
    def determine_phase(self, state: ConversationState, intent: str) -> ConversationPhase:
        """Détermine la phase actuelle de la conversation"""
        
        # Si c'est juste un salut sans critères, greeting
        if state.turn_count == 0 and intent == "greeting" and not state.user_need.category:
            return ConversationPhase.GREETING
        
        if intent == "explain":
            return ConversationPhase.EXPLANATION
        
        if intent == "compare":
            return ConversationPhase.COMPARISON
        
        if intent == "compatibility":
            return ConversationPhase.EXPLANATION
        
        # Si on a assez d'infos, recommandation directe
        if self.has_enough_info(state):
            return ConversationPhase.RECOMMENDATION
        
        # Sinon, phase de découverte
        if not self.has_enough_info(state):
            return ConversationPhase.DISCOVERY
        
        if len(state.products_shown) > 0 and intent in ["number_response", "compare"]:
            return ConversationPhase.COMPARISON
        
        return ConversationPhase.RECOMMENDATION
    
    async def generate_greeting(self, language: str) -> str:
        """Génère le message d'accueil"""
        return GREETING_MESSAGES.get(language, GREETING_MESSAGES["fr"])
    
    async def generate_discovery_response(
        self, 
        state: ConversationState,
        question_data: Tuple[str, str, List[str]]
    ) -> str:
        """Génère une question de découverte"""
        question_id, question_text, options = question_data
        
        response = f"{question_text}\n\n"
        response += "\n".join(options)
        
        if state.language == "fr":
            response += "\n\nRéponds par le numéro ou écris autre chose si tu préfères."
        else:
            response += "\n\nجاوبني بالرقم ولا اكتب شي آخر كيف تحب."
        
        return response
    
    async def generate_recommendation_response(
        self,
        products: List[Dict],
        state: ConversationState,
        metadata: Dict
    ) -> str:
        """Génère la réponse avec les recommandations"""
        lang = state.language
        
        if not products:
            if lang == "fr":
                return "Je n'ai pas trouvé de produits correspondant exactement à vos critères. Pouvez-vous me donner plus de détails ou essayer avec d'autres critères?"
            else:
                return "ما لقيتش منتجات تطابق بالضبط اللي تلوج عليه. تنجم تعطيني تفاصيل أكثر ولا تجرب كريتار آخر؟"
        
        # Intro
        if lang == "fr":
            response = f"Voici {len(products)} produits que je te recommande:\n\n"
        else:
            response = f"هاو {len(products)} منتجات نقترحهم عليك:\n\n"
        
        # Produits
        for i, product in enumerate(products[:5], 1):
            why = self._generate_why_recommended(product, state, lang)
            response += self.format_product_for_response(product, why, lang)
            response += "\n\n"
        
        # Avertissements de compatibilité
        warnings = metadata.get("compatibility_warnings", [])
        if warnings:
            response += "\n" + "\n".join(warnings) + "\n"
        
        # Options de suite
        if lang == "fr":
            response += """\n**Que veux-tu faire?**
1) Comparer ces produits
2) Voir les produits complémentaires
3) Plus de détails sur un produit
0) Autre recherche

Réponds par le numéro ou pose-moi une question."""
        else:
            response += """\n**شنوة تحب تعمل؟**
1) قارن بين المنتجات
2) شوف منتجات مكملة
3) تفاصيل أكثر على منتج
0) بحث آخر

جاوبني بالرقم ولا اسألني سؤال."""
        
        return response
    
    def _generate_why_recommended(
        self, 
        product: Dict, 
        state: ConversationState,
        language: str
    ) -> str:
        """Génère l'explication de pourquoi ce produit est recommandé"""
        need = state.user_need
        reasons = []
        
        # Basé sur l'environnement
        name_lower = product.get("name", "").lower()
        if need.environment == "exterieur":
            if any(kw in name_lower for kw in ["ip65", "ip66", "ip67", "extérieur"]):
                reasons.append("adapté pour l'extérieur" if language == "fr" else "مناسب للخارج")
        
        # Basé sur la connectivité
        attrs = product.get("attributes_norm", {})
        conn = attrs.get("connectivity", "")
        if need.connectivity == "wifi" and "Sans fil" in conn:
            reasons.append("WiFi intégré" if language == "fr" else "WiFi مدمج")
        elif need.connectivity == "filaire" and "Filaire" in conn:
            reasons.append("connexion filaire stable" if language == "fr" else "اتصال سلكي ثابت")
        
        # Basé sur la marque
        if need.brand_preference and product.get("brand", "").lower() == need.brand_preference.lower():
            reasons.append(f"marque {need.brand_preference}" if language == "fr" else f"ماركة {need.brand_preference}")
        
        if reasons:
            return "✓ " + ", ".join(reasons)
        return "✓ " + ("Produit de qualité" if language == "fr" else "منتج بجودة عالية")
