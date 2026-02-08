"""
MyDar Chatbot IA - E-commerce Tunisie (FR / Tounsi)
Version 3.0 - Flux complet avec choix modèle IA admin
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os
import uuid
import re
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'mydar_db')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# ============ MODÈLES IA DISPONIBLES ============
AI_MODELS = {
    "gpt-5.2": {"provider": "openai", "model": "gpt-5.2"},
    "gpt-4o": {"provider": "openai", "model": "gpt-4o"},
    "gpt-4o-mini": {"provider": "openai", "model": "gpt-4o-mini"},
    "gemini-2": {"provider": "gemini", "model": "gemini-2.0-flash"},
    "gemini-2-lite": {"provider": "gemini", "model": "gemini-2.0-flash"},
    "gemini-3-flash": {"provider": "gemini", "model": "gemini-3-flash"},
    "claude-sonnet": {"provider": "anthropic", "model": "claude-sonnet-4-5"},
}

DEFAULT_MODEL = "gpt-5.2"

# ============ MESSAGES STATIQUES ============

# ÉTAPE 1: Message de bienvenue - CHOIX DE LANGUE
WELCOME_LANGUAGE_MSG = """Bienvenue 👋 / Mar7bé 👋

Choisis ta langue / Khtar loughetak :
🇫🇷 1 - Français
🇹🇳 2 - Tounsi (arabizi)"""

# ÉTAPE 2: Choix du mode - FRANÇAIS
MODE_MSG_FR = """Parfait ! Comment puis-je t'aider ?

1️⃣ Suivre une commande
2️⃣ Poser une question sur un produit
3️⃣ T'aider à choisir un produit

Réponds : 1, 2 ou 3"""

# ÉTAPE 2: Choix du mode - TUNISIEN
MODE_MSG_TN = """Behhi ! Kifech nnejm n3awnek ?

1️⃣ Ttabba3 commande
2️⃣ So2él 3la produit
3️⃣ N3awnek tkhtar produit mneseb

Jaweb : 1, 2 wella 3"""

# Messages Option 1 - Suivi commande
ORDER_MSG_FR = """Pour suivre ta commande, donne-moi :
- Ton numéro de commande (ex: CMD-12345)
- Ou ton email / téléphone"""

ORDER_MSG_TN = """Bech nttabba3 el commande mte3ek, 3tini :
- Numero commande (ex: CMD-12345)
- Wella email / telephone mte3ek"""

# Messages Option 2 - Question produit
PRODUCT_Q_MSG_FR = """Quel produit t'intéresse ?
Donne-moi le nom ou le code du produit."""

PRODUCT_Q_MSG_TN = """Chnou el produit eli y3ajbek ?
3tini esm wella code el produit."""

# Messages Option 3 - Aide au choix
HELP_MSG_FR = """Super ! Explique-moi ce que tu cherches.
Dis-moi ton besoin, et je te poserai quelques questions pour trouver le produit idéal."""

HELP_MSG_TN = """Behhi ! Fassarli chnou tlouj 3lih.
9olli chnou t7eb, w bech nes2lek chwaya as2la bech nel9aw el produit el mneseb."""

# Message fin de réponse
END_MSG_FR = """
---
Tu veux suivre une commande, poser une question produit ou que je t'aide à choisir ? (1 / 2 / 3)"""

END_MSG_TN = """
---
T7eb ttabba3 commande, tes2el 3la produit, wella n3awnek tkhtar ? (1 / 2 / 3)"""

# ============ SYSTEM PROMPTS ============

SYSTEM_PROMPT_FR = """Tu es un assistant e-commerce intelligent pour MyDar.tn (Tunisie).

🎯 TON RÔLE selon le MODE actuel:

**MODE SUIVI COMMANDE:**
- Aide à suivre les commandes
- Demande numéro commande / email / téléphone
- Donne le statut, état livraison, transporteur

**MODE QUESTION PRODUIT:**
- Réponds aux questions sur les produits du catalogue
- Donne les caractéristiques, spécifications
- Compare si demandé
- NE PROPOSE PAS de produits, réponds juste aux questions

**MODE AIDE AU CHOIX:**
- Comprends le besoin du client
- Pose des questions ciblées (budget, usage, environnement, connexion, installation)
- Propose 3-5 produits MAX avec:
  - Nom produit
  - Prix (si disponible)
  - 3 avantages clés max
  - Utilise {{PRODUCT_CARD:product_id}} pour chaque produit

📋 RÈGLES STRICTES:
1. NE JAMAIS inventer: prix, stock, caractéristiques, compatibilité, délais
2. Si info non disponible → dis-le clairement
3. Utilise UNIQUEMENT les infos du catalogue fourni
4. Réponds en FRANÇAIS uniquement (le client a choisi français)
5. Sois concis mais complet

{context}

⚠️ TERMINE TOUJOURS par: "Tu veux suivre une commande, poser une question produit ou que je t'aide à choisir ? (1 / 2 / 3)"
"""

SYSTEM_PROMPT_TN = """Enti assistant e-commerce dhki lel MyDar.tn (Tounes).

🎯 DAWREK 7asb el MODE:

**MODE SUIVI COMMANDE:**
- 3awen bech ytabba3 les commandes
- Es2el 3la numero commande / email / telephone
- 3ti statut, 7alet livraison, transporteur

**MODE QUESTION PRODUIT:**
- Jaweb 3la les questions 3al produits
- 3ti caractéristiques, spécifications
- Compare ken taleb
- MA TA9TAR7CH produits, jaweb bark 3al as2la

**MODE AIDE AU CHOIX:**
- Efhem chnou y7eb el client
- Es2el as2la (budget, usage, environnement, connexion, installation)
- E9tar7 3-5 produits MAX:
  - Esm produit
  - Prix (ken mawjoud)
  - 3 avantages max
  - Esta3mel {{PRODUCT_CARD:product_id}} lkol produit

📋 9AWE3ED:
1. MA TKHTAR3CH: prix, stock, caractéristiques, compatibilité, délais
2. Ken el info mouch mawjouda → 9ol bel wadhe7
3. Esta3mel BARK el infos mel catalogue
4. Jaweb bel TOUNSI (latin letters) BARK
5. Les mots français 7othom fi () aw " "

{context}

⚠️ AKHER KLEMTEK DIMA: "T7eb ttabba3 commande, tes2el 3la produit, wella n3awnek tkhtar ? (1 / 2 / 3)"
"""

# ============ MODELS ============

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    phase: str
    mode: Optional[str] = None
    products: List[Dict] = []

class AIModelSettings(BaseModel):
    model_id: str

# ============ HELPER FUNCTIONS ============

async def get_ai_model() -> Dict:
    """Récupère le modèle IA configuré par l'admin"""
    settings = await db.chatbot_settings.find_one({"key": "ai_model"})
    if settings and settings.get("value") in AI_MODELS:
        return AI_MODELS[settings["value"]]
    return AI_MODELS[DEFAULT_MODEL]

async def get_ai_model_name() -> str:
    """Récupère le nom du modèle IA configuré"""
    settings = await db.chatbot_settings.find_one({"key": "ai_model"})
    if settings and settings.get("value") in AI_MODELS:
        return settings["value"]
    return DEFAULT_MODEL

def detect_language(message: str) -> str:
    """Détecte si le message est en français ou tunisien (arabizi)"""
    msg_lower = message.lower()
    
    # Si juste un chiffre, on ne peut pas détecter
    if msg_lower in ["1", "2", "3"]:
        return None  # Pas de détection
    
    # Patterns tunisiens (arabizi) - mots typiques
    tunisian_words = [
        "mar7", "3andi", "n7eb", "chnou", "kifech", "bech", "mte3", "wella", 
        "ken", "barcha", "saye", "behhi", "nnejm", "t7eb", "3la", "9olli",
        "kherej", "dekhel", "3awni", "tkhtar", "mneseb", "ttabba3", "so2el"
    ]
    
    # Compter les mots tunisiens
    tunisian_count = sum(1 for word in tunisian_words if word in msg_lower)
    
    # Si chiffres arabes utilisés comme lettres (3, 7, 9, 5) ET mots tunisiens
    has_arabic_numbers = any(c in msg_lower for c in ['3', '7', '9', '5'])
    
    if tunisian_count >= 1 or (has_arabic_numbers and len(msg_lower) > 3):
        return "tn"
    
    # Vérifier si c'est de l'arabe script
    if re.search(r'[\u0600-\u06FF]', message):
        return "tn"  # On convertit mentalement en tunisien
    
    # Par défaut français
    return "fr"

async def get_session_state(session_id: str) -> Dict:
    """Récupère l'état de la session"""
    state = await db.chat_sessions_v3.find_one({"session_id": session_id})
    if state:
        return {
            "language": state.get("language"),  # None, "fr", "tn"
            "mode": state.get("mode"),  # None, "order", "question", "help"
            "phase": state.get("phase", "welcome"),  # welcome, mode_choice, conversation
            "criteria": state.get("criteria", {}),
            "turn_count": state.get("turn_count", 0),
            "products_shown": state.get("products_shown", []),
            "last_search": state.get("last_search", []),
        }
    return {
        "language": None,
        "mode": None,
        "phase": "welcome",
        "criteria": {},
        "turn_count": 0,
        "products_shown": [],
        "last_search": [],
    }

async def save_session_state(session_id: str, state: Dict):
    """Sauvegarde l'état de la session"""
    await db.chat_sessions_v3.update_one(
        {"session_id": session_id},
        {"$set": {
            **state,
            "session_id": session_id,
            "updated_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )

async def save_message(session_id: str, role: str, content: str):
    """Sauvegarde un message"""
    await db.chat_history.insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc)
    })

async def get_session_history(session_id: str, limit: int = 10) -> List[Dict]:
    """Récupère l'historique de la session"""
    messages = await db.chat_history.find(
        {"session_id": session_id}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    messages.reverse()
    return [{"role": m.get("role"), "content": m.get("content")} for m in messages]

# ============ PRODUCT SEARCH API ============

async def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    environment: Optional[str] = None,
    connectivity: Optional[str] = None,
    brand: Optional[str] = None,
    budget_max: Optional[float] = None,
    limit: int = 5
) -> List[Dict]:
    """API recherche catalogue"""
    mongo_query = {"active": True, "image_missing": False}
    
    # Recherche textuelle
    if query:
        mongo_query["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"sku": {"$regex": query, "$options": "i"}},
        ]
    
    # Filtres
    if category:
        mongo_query["category_path_ids"] = {"$regex": category, "$options": "i"}
    
    if brand:
        mongo_query["brand"] = {"$regex": brand, "$options": "i"}
    
    if connectivity:
        mongo_query["attributes_norm.connectivity"] = {"$in": [connectivity, "Hybride"]}
    
    if environment == "exterieur":
        if "$or" in mongo_query:
            # Combiner avec AND
            existing_or = mongo_query.pop("$or")
            mongo_query["$and"] = [
                {"$or": existing_or},
                {"$or": [
                    {"name": {"$regex": "ext[ée]rieur|outdoor|ip6[567]|bullet", "$options": "i"}},
                    {"description": {"$regex": "ext[ée]rieur|outdoor|ip6[567]", "$options": "i"}},
                ]}
            ]
        else:
            mongo_query["$or"] = [
                {"name": {"$regex": "ext[ée]rieur|outdoor|ip6[567]|bullet", "$options": "i"}},
                {"description": {"$regex": "ext[ée]rieur|outdoor|ip6[567]", "$options": "i"}},
            ]
    
    if budget_max and budget_max > 0:
        mongo_query["price"] = {"$gt": 0, "$lte": budget_max}
    
    products = await db.products.find(
        mongo_query, {"_id": 0}
    ).sort([("ranking.quality_score", -1), ("featured", -1)]).limit(limit * 2).to_list(limit * 2)
    
    # Filtrer les accessoires
    exclude = ["support", "câble", "cable", "adaptateur", "alimentation", "vis", "connecteur"]
    filtered = []
    for p in products:
        name_lower = p.get("name", "").lower()
        if not any(excl in name_lower for excl in exclude):
            filtered.append(p)
            if len(filtered) >= limit:
                break
    
    return filtered

async def get_product_details(product_id: str) -> Optional[Dict]:
    """API détails produit"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    return product

async def search_product_by_name(name: str) -> List[Dict]:
    """Recherche produit par nom/code modèle/sku"""
    # Clean the search term
    search_term = name.strip()
    
    products = await db.products.find({
        "active": True,
        "$or": [
            {"model_code": {"$regex": search_term, "$options": "i"}},
            {"name": {"$regex": search_term, "$options": "i"}},
            {"sku": {"$regex": search_term, "$options": "i"}},
            {"id": {"$regex": search_term, "$options": "i"}},
        ]
    }, {"_id": 0}).limit(5).to_list(5)
    return products

# ============ ORDER TRACKING API ============

async def track_order(identifier: str) -> Optional[Dict]:
    """API suivi commande - Cherche dans purchase_requests"""
    # Nettoyer l'identifiant (enlever # et espaces)
    clean_id = identifier.strip().upper().replace("#", "").replace(" ", "")
    
    # Chercher dans purchase_requests par ID partiel (8 premiers caractères) ou email/phone
    purchase_request = await db.purchase_requests.find_one({
        "$or": [
            # Recherche par les 8 premiers caractères de l'ID
            {"id": {"$regex": f"^{clean_id}", "$options": "i"}},
            # Recherche par email
            {"user_email": {"$regex": identifier.strip(), "$options": "i"}},
            # Recherche par téléphone
            {"user_phone": {"$regex": identifier.strip(), "$options": "i"}},
        ]
    }, {"_id": 0})
    
    if purchase_request:
        # Mapper le statut en français lisible
        status_map = {
            "EN_ATTENTE": "En attente de validation",
            "EN_COURS": "En cours de traitement",
            "VALIDEE": "Validée ✓",
            "REFUSEE": "Refusée"
        }
        
        delivery_map = {
            "EN_ATTENTE": "En attente",
            "EN_COURS": "Préparation en cours",
            "VALIDEE": "Prête pour livraison",
            "REFUSEE": "Annulée"
        }
        
        status = purchase_request.get("status", "EN_ATTENTE")
        order_id = purchase_request.get("id", "")[:8].upper()
        
        return {
            "order_number": f"#{order_id}",
            "status": status_map.get(status, status),
            "delivery_status": delivery_map.get(status, "En attente"),
            "carrier": "À définir" if status != "VALIDEE" else "Aramex",
            "tracking_number": purchase_request.get("tracking_number") or ("En attente" if status != "VALIDEE" else f"ARX{order_id}TN"),
            "estimated_delivery": "2-3 jours ouvrables après validation" if status != "VALIDEE" else "2-3 jours ouvrables",
            "items_count": len(purchase_request.get("items", [])),
            "total": purchase_request.get("total_estimated", 0),
        }
    
    return None

# ============ RESPONSE FORMATTING ============

def format_product_card(product: Dict, lang: str) -> str:
    """Formate un produit en carte"""
    name = product.get("name", "Produit")
    brand = product.get("brand", "")
    price = product.get("price")
    product_id = product.get("id", "")
    
    # Prix
    if price and price > 0:
        price_str = f"{price:.3f} DT"
    else:
        price_str = "Prix sur demande" if lang == "fr" else "(prix) 3la talab"
    
    # 3 avantages clés
    benefits = []
    desc = product.get("description", "")
    attrs = product.get("attributes_norm", {})
    
    if attrs.get("connectivity"):
        benefits.append(f"Connectivité: {attrs['connectivity']}")
    if "ip67" in name.lower() or "ip65" in name.lower():
        benefits.append("Protection extérieur" if lang == "fr" else "(IP67) lel kherej")
    if "colorvu" in name.lower():
        benefits.append("Vision couleur nuit" if lang == "fr" else "(ColorVu) alwen bellil")
    if "micro" in name.lower():
        benefits.append("Micro intégré" if lang == "fr" else "(Micro) integré")
    if "poe" in name.lower():
        benefits.append("Alimentation PoE" if lang == "fr" else "(PoE) cable we7ed")
    
    benefits = benefits[:3]
    benefits_text = "\n".join([f"  ✓ {b}" for b in benefits]) if benefits else ""
    
    card = f"""
📦 **{name}** — {brand}
💰 {price_str}
{benefits_text}
🔍 [Voir détails](/produit/{product_id}) | 🛒 [Ajouter au panier](ADD_TO_CART:{product_id})
"""
    return card

def process_response(response: str, lang: str) -> str:
    """Traite la réponse pour les cartes produits"""
    # Convertir {{PRODUCT_CARD:id}} en format carte
    pattern = r'\{+PRODUCT_CARD:([a-zA-Z0-9\-]+)\}+'
    
    async def replace_card(match):
        product_id = match.group(1)
        product = await get_product_details(product_id)
        if product:
            return format_product_card(product, lang)
        return ""
    
    # Pour l'instant, on garde le pattern et on le traite après
    return response

def extract_product_ids(response: str) -> List[str]:
    """Extrait les IDs de produits de la réponse"""
    patterns = [
        r'/produit/([a-zA-Z0-9\-]+)',
        r'ADD_TO_CART:([a-zA-Z0-9\-]+)',
        r'PRODUCT_CARD:([a-zA-Z0-9\-]+)'
    ]
    ids = []
    for pattern in patterns:
        ids.extend(re.findall(pattern, response))
    return list(set(ids))

# ============ MAIN CHAT ENDPOINT ============

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal du chatbot IA
    Flux: Language Choice → Mode Choice → Conversation
    """
    try:
        # 1. Session
        session_id = request.session_id or str(uuid.uuid4())
        state = await get_session_state(session_id)
        msg = request.message.strip().lower()
        msg_original = request.message.strip()
        
        response_text = ""
        products_mentioned = []
        
        # ============ PHASE 1: CHOIX DE LANGUE (première interaction) ============
        if state["phase"] == "welcome" or (state["phase"] == "language_choice" and state["language"] is None):
            # Si c'est le premier message ou "start", afficher le choix de langue
            if state["turn_count"] == 0 or msg in ["start", "bonjour", "hello", "salut", "mar7ba", "مرحبا"]:
                response_text = WELCOME_LANGUAGE_MSG
                state["phase"] = "language_choice"
                state["turn_count"] += 1
                
                await save_session_state(session_id, state)
                if msg not in ["start", ""]:
                    await save_message(session_id, "user", msg_original)
                await save_message(session_id, "assistant", response_text)
                
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    phase="language_choice",
                    mode=None,
                    products=[]
                )
        
        # ============ PHASE 2: CHOIX DE LANGUE → MODE ============
        if state["phase"] == "language_choice":
            # Déterminer la langue choisie
            if msg == "1" or any(kw in msg for kw in ["français", "francais", "french", "fr"]):
                state["language"] = "fr"
                response_text = MODE_MSG_FR
                state["phase"] = "mode_choice"
            elif msg == "2" or any(kw in msg for kw in ["tounsi", "tunisien", "arabizi", "arabe", "tn", "تونسي"]):
                state["language"] = "tn"
                response_text = MODE_MSG_TN
                state["phase"] = "mode_choice"
            else:
                # Langue non reconnue, redemander
                response_text = WELCOME_LANGUAGE_MSG
                await save_session_state(session_id, state)
                await save_message(session_id, "user", msg_original)
                await save_message(session_id, "assistant", response_text)
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    phase="language_choice",
                    mode=None,
                    products=[]
                )
            
            state["turn_count"] += 1
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg_original)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase="mode_choice",
                mode=None,
                products=[]
            )
        
        # ============ PHASE 3: CHOIX DU MODE ============
        if state["phase"] == "mode_choice":
            lang = state["language"] or "fr"
            
            # Déterminer le mode choisi
            if msg == "1" or any(kw in msg for kw in ["suiv", "command", "ttabba3", "commande"]):
                state["mode"] = "order"
                response_text = ORDER_MSG_FR if lang == "fr" else ORDER_MSG_TN
                state["phase"] = "conversation"
            elif msg == "2" or any(kw in msg for kw in ["question", "so2el", "produit"]):
                state["mode"] = "question"
                response_text = PRODUCT_Q_MSG_FR if lang == "fr" else PRODUCT_Q_MSG_TN
                state["phase"] = "conversation"
            elif msg == "3" or any(kw in msg for kw in ["aide", "chois", "n3awn", "tkhtar", "help"]):
                state["mode"] = "help"
                response_text = HELP_MSG_FR if lang == "fr" else HELP_MSG_TN
                state["phase"] = "conversation"
            else:
                # Mode non reconnu, redemander
                response_text = MODE_MSG_FR if lang == "fr" else MODE_MSG_TN
                await save_session_state(session_id, state)
                await save_message(session_id, "user", msg_original)
                await save_message(session_id, "assistant", response_text)
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    phase="mode_choice",
                    mode=None,
                    products=[]
                )
            
            state["turn_count"] += 1
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg_original)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase="conversation",
                mode=state["mode"],
                products=[]
            )
        
        # ============ PHASE CONVERSATION ============
        lang = state["language"] or "fr"
        mode = state["mode"] or "question"
        
        # Vérifier si l'utilisateur veut changer de mode
        if msg in ["1", "2", "3"]:
            if msg == "1":
                state["mode"] = "order"
                mode = "order"
                response_text = ORDER_MSG_FR if lang == "fr" else ORDER_MSG_TN
            elif msg == "2":
                state["mode"] = "question"
                mode = "question"
                response_text = PRODUCT_Q_MSG_FR if lang == "fr" else PRODUCT_Q_MSG_TN
            elif msg == "3":
                state["mode"] = "help"
                mode = "help"
                response_text = HELP_MSG_FR if lang == "fr" else HELP_MSG_TN
            
            state["turn_count"] += 1
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg_original)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase="conversation",
                mode=mode,
                products=[]
            )
        
        # ===== MODE SUIVI COMMANDE =====
        if mode == "order":
            order_info = await track_order(msg_original)
            
            if order_info:
                if lang == "fr":
                    response_text = f"""✅ **Commande {order_info['order_number']}**

📋 **Statut:** {order_info['status']}
🚚 **Livraison:** {order_info['delivery_status']}
📦 **Transporteur:** {order_info.get('carrier', 'Non assigné')}
🔗 **N° suivi:** {order_info.get('tracking_number', 'Non disponible')}
⏰ **Délai estimé:** {order_info.get('estimated_delivery', 'Non disponible')}

{END_MSG_FR}"""
                else:
                    response_text = f"""✅ **Commande {order_info['order_number']}**

📋 **(Statut):** {order_info['status']}
🚚 **(Livraison):** {order_info['delivery_status']}
📦 **(Transporteur):** {order_info.get('carrier', 'Mouch ma3rouf')}
🔗 **(Numero suivi):** {order_info.get('tracking_number', 'Mouch disponible')}
⏰ **(Delai):** {order_info.get('estimated_delivery', 'Mouch disponible')}

{END_MSG_TN}"""
            else:
                if lang == "fr":
                    response_text = f"""❌ Je n'ai pas trouvé de commande avec "{msg_original}".

Vérifie le numéro et réessaie, ou donne-moi ton email/téléphone.

{END_MSG_FR}"""
                else:
                    response_text = f"""❌ Ma l9itch commande b "{msg_original}".

Tathabet mel numero w 3awed, wella 3tini email/telephone mte3ek.

{END_MSG_TN}"""
            
            state["turn_count"] += 1
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg_original)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase="conversation",
                mode=mode,
                products=[]
            )
        
        # ===== MODE QUESTION PRODUIT =====
        if mode == "question":
            # Vérifier si on a un produit en contexte
            last_products = state.get("last_search", [])
            
            # Détecter les codes modèles dans le message (format: XXX-XXXX)
            import re
            model_code_pattern = r'\b([A-Z]{2,4}-[A-Z0-9]{4})\b'
            found_codes = re.findall(model_code_pattern, msg_original.upper())
            
            # Chercher les produits additionnels mentionnés par code
            additional_products = []
            if found_codes:
                for code in found_codes:
                    # Vérifier si ce code n'est pas déjà dans last_products
                    existing_codes = [p.get('model_code', '').upper() for p in last_products]
                    if code not in existing_codes:
                        found = await db.products.find({
                            "model_code": {"$regex": f"^{code}", "$options": "i"}
                        }, {"_id": 0}).limit(1).to_list(1)
                        if found:
                            additional_products.extend(found)
            
            # Combiner les produits existants et additionnels
            all_context_products = last_products + additional_products
            
            # Si on a trouvé de nouveaux produits, les ajouter au contexte
            if additional_products:
                state["last_search"] = all_context_products
            
            # Déterminer si c'est une question de suivi ou une nouvelle recherche
            is_follow_up_question = len(last_products) > 0 and not any(
                msg.startswith(prefix) for prefix in ["1", "2", "3", "4", "5"]
            ) and len(msg) > 3
            
            if is_follow_up_question and all_context_products:
                # C'est une question - utiliser l'IA avec les specs de tous les produits en contexte
                response_text = await call_ai_for_response(msg_original, state, all_context_products, mode)
                
                # Retirer le message de fin si présent
                if END_MSG_FR in response_text:
                    response_text = response_text.replace(END_MSG_FR, "")
                if END_MSG_TN in response_text:
                    response_text = response_text.replace(END_MSG_TN, "")
                
                # Ajouter un message pour continuer
                if lang == "fr":
                    response_text += "\n\n💬 As-tu d'autres questions ?"
                else:
                    response_text += "\n\n💬 3andek as2la okhra ?"
                
                state["turn_count"] += 1
                await save_session_state(session_id, state)
                await save_message(session_id, "user", msg_original)
                await save_message(session_id, "assistant", response_text)
                
                products_mentioned = [{
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "brand": p.get("brand"),
                    "price": p.get("price"),
                    "image": p.get("image_url") or p.get("image"),
                } for p in all_context_products[:3]]
                
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    phase="conversation",
                    mode=mode,
                    products=products_mentioned
                )
            
            # Rechercher le produit (nouveau ou numéro de sélection)
            products = []
            
            # Si c'est un numéro et on a plusieurs produits en attente
            if msg.isdigit() and len(last_products) > 1:
                idx = int(msg) - 1
                if 0 <= idx < len(last_products):
                    products = [last_products[idx]]
            
            # Sinon, rechercher par nom/code
            if not products:
                products = await search_product_by_name(msg_original)
            
            if len(products) == 0:
                # Pas trouvé, utiliser l'IA pour répondre à la question technique
                response_text = await call_ai_for_response(msg_original, state, last_products, mode)
            elif len(products) == 1:
                # Un seul produit trouvé
                product = products[0]
                state["last_search"] = [product]
                
                if lang == "fr":
                    response_text = f"""📦 **{product.get('name')}**

**Catégorie:** {product.get('category', 'N/A')}

Pose-moi tes questions sur ce produit !"""
                else:
                    response_text = f"""📦 **{product.get('name')}**

**(Categorie):** {product.get('category', 'N/A')}

Es2elni 3la hedha el produit !"""
                
                products_mentioned = [{
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "brand": product.get("brand"),
                    "price": product.get("price"),
                    "image": product.get("image_url") or product.get("image"),
                }]
            else:
                # Plusieurs produits trouvés
                state["last_search"] = products
                
                if lang == "fr":
                    response_text = f"J'ai trouvé {len(products)} produits. Lequel t'intéresse ?\n\n"
                    for i, p in enumerate(products, 1):
                        response_text += f"{i}) **{p.get('name')}** — {p.get('brand', '')}\n"
                    response_text += "\nRéponds avec le numéro."
                else:
                    response_text = f"L9it {len(products)} produits. Chnou y3ajbek ?\n\n"
                    for i, p in enumerate(products, 1):
                        response_text += f"{i}) **{p.get('name')}** — {p.get('brand', '')}\n"
                    response_text += "\nJaweb bel numero."
            
            state["turn_count"] += 1
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg_original)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase="conversation",
                mode=mode,
                products=products_mentioned
            )
        
        # ===== MODE AIDE AU CHOIX =====
        if mode == "help":
            # Extraire les critères du message
            criteria = extract_criteria_from_message(msg_original)
            state["criteria"].update(criteria)
            
            # Rechercher des produits si on a assez de critères
            products = []
            if state["criteria"].get("category"):
                products = await search_products(
                    category=state["criteria"].get("category"),
                    environment=state["criteria"].get("environment"),
                    connectivity=state["criteria"].get("connectivity"),
                    brand=state["criteria"].get("brand"),
                    budget_max=state["criteria"].get("budget"),
                    limit=5
                )
            
            # Appeler l'IA pour générer la réponse
            response_text = await call_ai_for_response(msg_original, state, products, mode)
            
            # Extraire les produits mentionnés
            mentioned_ids = extract_product_ids(response_text)
            for pid in mentioned_ids[:5]:
                product = await get_product_details(pid)
                if product:
                    products_mentioned.append({
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "brand": product.get("brand"),
                        "price": product.get("price"),
                        "image": product.get("image_url") or product.get("image"),
                    })
            
            # Si pas de produits dans la réponse mais on en a trouvé
            if not products_mentioned and products:
                for p in products[:5]:
                    response_text += format_product_card(p, lang)
                    products_mentioned.append({
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "brand": p.get("brand"),
                        "price": p.get("price"),
                        "image": p.get("image_url") or p.get("image"),
                    })
            
            # Ajouter le message de fin
            end_msg = END_MSG_FR if lang == "fr" else END_MSG_TN
            if end_msg not in response_text:
                response_text += end_msg
            
            state["turn_count"] += 1
            state["products_shown"].extend([p["id"] for p in products_mentioned])
            
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg_original)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase="conversation",
                mode=mode,
                products=products_mentioned
            )
        
        # Fallback - Retourner au choix de langue
        response_text = WELCOME_LANGUAGE_MSG
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            phase="language_choice",
            mode=None,
            products=[]
        )
        
    except Exception as e:
        print(f"[Chatbot Error] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============ AI CALL FUNCTION ============

async def call_ai_for_response(message: str, state: Dict, products: List[Dict], mode: str) -> str:
    """Appelle l'IA pour générer une réponse"""
    lang = state.get("language", "fr")
    
    # Récupérer le modèle configuré
    ai_config = await get_ai_model()
    ai_model_name = await get_ai_model_name()
    
    # Formater les produits pour le contexte AVEC SPECIFICATIONS
    if products:
        product_lines = []
        for p in products:
            price = p.get('price')
            price_str = f"{price:.3f} DT" if price else "Prix sur demande"
            
            # Construire les specs du produit
            specs_text = ""
            specifications = p.get('specifications', [])
            if specifications:
                specs_lines = []
                for section in specifications:  # Toutes les sections
                    section_name = section.get('name', '')
                    specs = section.get('specs', [])  # Toutes les specs
                    for spec in specs:
                        key = spec.get('key', '').strip().rstrip(':')
                        value = spec.get('value', '').strip()
                        if key and value and value != '–' and value != '-':
                            specs_lines.append(f"    • {key}: {value}")
                if specs_lines:
                    specs_text = "\n" + "\n".join(specs_lines)
            
            # Ajouter attributs normalisés si pas de specs
            if not specs_text:
                attrs = p.get('attributes_norm', {})
                if attrs:
                    attrs_lines = []
                    for k, v in attrs.items():
                        if v and v != 'N/A':
                            attrs_lines.append(f"    • {k}: {v}")
                    if attrs_lines:
                        specs_text = "\n" + "\n".join(attrs_lines[:6])
            
            product_lines.append(f"""
📦 **{p.get('name')}**
  - Marque: {p.get('brand', 'N/A')}
  - Prix: {price_str}
  - Code: {p.get('model_code', p.get('sku', 'N/A'))}
  - Catégorie: {p.get('category', 'N/A')}
  - ID: {p.get('id')}{specs_text}
""")
        products_text = "\n".join(product_lines)
    else:
        products_text = "Aucun produit trouvé pour cette recherche."
    
    # Historique
    history = await get_session_history(state.get("session_id", ""), limit=6)
    history_text = "\n".join([f"{m['role']}: {m['content'][:150]}" for m in history[-4:]])
    
    # Contexte
    context = f"""
📦 CATALOGUE DISPONIBLE (avec spécifications techniques):
{products_text}

📊 CRITÈRES CLIENT:
{state.get('criteria', {})}

💬 HISTORIQUE:
{history_text}

🎯 MODE: {mode.upper()}

⚠️ IMPORTANT: Utilise les spécifications techniques ci-dessus pour répondre aux questions. Ne demande pas d'infos que tu as déjà !
"""
    
    # Sélectionner le prompt
    system_prompt = SYSTEM_PROMPT_TN if lang == "tn" else SYSTEM_PROMPT_FR
    full_prompt = system_prompt.format(context=context)
    
    # Appeler l'IA
    try:
        chat_instance = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"mydar-v3-{state.get('session_id', 'new')}",
            system_message=full_prompt
        ).with_model(ai_config["provider"], ai_config["model"])
        
        response = await chat_instance.send_message(UserMessage(text=message))
        print(f"[AI] Model: {ai_model_name}, Provider: {ai_config['provider']}")
        return response
    except Exception as e:
        print(f"[AI Error] {e}")
        # Fallback message
        if lang == "fr":
            return f"Désolé, je n'ai pas pu traiter ta demande. Réessaie ou choisis une autre option.{END_MSG_FR}"
        else:
            return f"Msamahni, ma njemtch n3awen. 3awed wella khtar option okhra.{END_MSG_TN}"

def extract_criteria_from_message(message: str) -> Dict:
    """Extrait les critères de recherche du message"""
    msg_lower = message.lower()
    criteria = {}
    
    # Catégorie
    category_map = {
        "videosurveillance": ["caméra", "camera", "nvr", "dvr", "surveillance", "enregistreur"],
        "alarme": ["alarme", "détecteur", "intrusion", "sirène"],
        "videophonie": ["visiophone", "interphone", "sonnette"],
        "controle-d-accès": ["pointeuse", "badge", "accès", "empreinte", "biométr"],
        "motorisation": ["volet", "store", "portail", "moteur", "somfy"],
    }
    
    for cat, keywords in category_map.items():
        if any(kw in msg_lower for kw in keywords):
            criteria["category"] = cat
            break
    
    # Environnement
    if any(kw in msg_lower for kw in ["extérieur", "exterieur", "outdoor", "dehors", "kherej", "barra"]):
        criteria["environment"] = "exterieur"
    elif any(kw in msg_lower for kw in ["intérieur", "interieur", "indoor", "dedans", "dekhel"]):
        criteria["environment"] = "interieur"
    
    # Connectivité
    if any(kw in msg_lower for kw in ["wifi", "wi-fi", "sans fil", "wireless"]):
        criteria["connectivity"] = "Sans fil"
    elif any(kw in msg_lower for kw in ["filaire", "câble", "cable", "poe", "ethernet"]):
        criteria["connectivity"] = "Filaire"
    
    # Marque
    brands = ["dahua", "hikvision", "somfy", "zkteco", "inim", "ruijie", "ajax"]
    for brand in brands:
        if brand in msg_lower:
            criteria["brand"] = brand
            break
    
    # Budget
    budget_match = re.search(r'(\d+)\s*(dt|dinars?|tnd)', msg_lower)
    if budget_match:
        criteria["budget"] = float(budget_match.group(1))
    
    return criteria

# ============ ADMIN ENDPOINTS ============

@router.get("/admin/ai-models")
async def get_available_models():
    """Liste des modèles IA disponibles"""
    current = await get_ai_model_name()
    return {
        "current_model": current,
        "available_models": list(AI_MODELS.keys()),
        "models_details": {
            k: {"provider": v["provider"], "model": v["model"]}
            for k, v in AI_MODELS.items()
        }
    }

@router.post("/admin/ai-model")
async def set_ai_model(settings: AIModelSettings):
    """Change le modèle IA utilisé"""
    if settings.model_id not in AI_MODELS:
        raise HTTPException(status_code=400, detail=f"Modèle inconnu. Choix: {list(AI_MODELS.keys())}")
    
    await db.chatbot_settings.update_one(
        {"key": "ai_model"},
        {"$set": {"key": "ai_model", "value": settings.model_id, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    
    return {
        "success": True,
        "model": settings.model_id,
        "details": AI_MODELS[settings.model_id]
    }

# ============ UTILITY ENDPOINTS ============

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Récupère l'historique d'une session"""
    messages = await db.chat_history.find(
        {"session_id": session_id}
    ).sort("timestamp", -1).limit(50).to_list(50)
    messages.reverse()
    return {
        "session_id": session_id,
        "messages": [{"role": m.get("role"), "content": m.get("content")} for m in messages]
    }

@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Efface l'historique d'une session"""
    r1 = await db.chat_history.delete_many({"session_id": session_id})
    r2 = await db.chat_sessions_v3.delete_many({"session_id": session_id})
    return {"messages_deleted": r1.deleted_count, "sessions_deleted": r2.deleted_count}

@router.post("/reset/{session_id}")
async def reset_session(session_id: str):
    """Réinitialise une session"""
    await db.chat_history.delete_many({"session_id": session_id})
    await db.chat_sessions_v3.delete_many({"session_id": session_id})
    return {"new_session_id": str(uuid.uuid4()), "message": "Session réinitialisée"}
