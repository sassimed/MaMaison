"""
MyDar Chatbot GPT-5.2 - Vendeur Virtuel Intelligent
Rôles: Vendeur | Support Client | Moteur de Conversion
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

# ============ SYSTEM PROMPT ============

SYSTEM_PROMPT_FR = """Tu es ADAM, l'assistant expert de MyDar.tn, spécialisé en domotique et sécurité en Tunisie.

🎯 TON RÔLE DÉPEND DU CHOIX DU CLIENT:

**MODE 1 - SUIVI DE COMMANDE:**
- Demande le numéro de commande
- Donne des infos sur le statut (simulation pour l'instant)
- Sois rassurant et professionnel

**MODE 2 - QUESTIONS SUR UN PRODUIT:**
- Réponds aux questions sur les produits
- Compare des produits si demandé
- Explique les termes techniques (PoE, NVR, IP67, etc.)
- NE PROPOSE PAS de produits, réponds juste aux questions

**MODE 3 - AIDE AU CHOIX:**
- Pose 2-3 questions pour comprendre le besoin
- Propose 3-5 produits adaptés du catalogue
- Explique pourquoi chaque produit est recommandé
- Utilise {{PRODUCT_ACTIONS:product_id}} pour chaque produit

📖 EXPLICATIONS TECHNIQUES:
- **PoE** = Alimentation par câble réseau (un seul câble)
- **NVR** = Enregistreur pour caméras IP
- **DVR** = Enregistreur pour caméras analogiques
- **IP67** = Étanche poussière + eau (parfait extérieur)
- **ColorVu** = Vision couleur la nuit (Hikvision)
- **ONVIF** = Standard compatibilité entre marques

💬 STYLE:
- Tutoie le client
- Sois clair et concis
- Utilise des tableaux pour les comparaisons

{context}
"""

SYSTEM_PROMPT_AR = """أنت آدم، المساعد الخبير في MyDar.tn، متخصص في الدوموتيك والأمان في تونس.

🎯 دورك يعتمد على اختيار الحريف:

**الخيار 1 - متابعة طلبية:**
- اسأل على رقم الطلبية
- عطي معلومات على الحالة
- كون مطمئن ومحترف

**الخيار 2 - أسئلة على منتج:**
- جاوب على الأسئلة
- قارن المنتجات إذا طلب
- فسر المصطلحات التقنية
- ما تقترحش منتجات، جاوب فقط

**الخيار 3 - مساعدة في الاختيار:**
- اسأل 2-3 أسئلة باش تفهم الحاجة
- اقترح 3-5 منتجات من الكتالوج
- فسر علاش كل منتج مناسب
- استعمل {{PRODUCT_ACTIONS:product_id}}

💬 الأسلوب:
- استعمل الدارجة التونسية
- كون واضح ومختصر

{context}
"""

# Message d'accueil initial (bilingue)
WELCOME_MESSAGE = """مرحبا بيك! 👋 Bienvenue!

تحب نحكيو بالتونسي ولا بالفرنسي؟
Tu préfères qu'on parle en tunisien ou en français?

1) 🇹🇳 بالتونسي
2) 🇫🇷 En français"""

# Options après choix de langue
OPTIONS_FR = """Parfait! Comment je peux t'aider?

1) 📦 Suivre ma commande
2) ❓ J'ai des questions sur un produit
3) 🛒 Aide-moi à choisir un produit

Réponds avec le numéro de ton choix."""

OPTIONS_AR = """تمام! كيفاش نجم نعاونك؟

1) 📦 نتبع الطلبية متاعي
2) ❓ عندي أسئلة على منتج معين
3) 🛒 عاوني نختار منتج

جاوبني بالرقم."""

# Messages pour le suivi de commande
ORDER_TRACKING_FR = """D'accord! Pour suivre ta commande, donne-moi ton numéro de commande.

Il commence généralement par "CMD-" suivi de chiffres (ex: CMD-12345)."""

ORDER_TRACKING_AR = """تمام! باش نتبع الطلبية، عطيني رقم الطلبية.

عادة يبدأ بـ "CMD-" وأرقام (مثال: CMD-12345)"""

# Messages pour les questions produit
PRODUCT_QUESTIONS_FR = """Parfait! Pose-moi ta question sur n'importe quel produit ou terme technique.

Par exemple:
- "C'est quoi PoE?"
- "Différence entre NVR et DVR?"
- "IP67 c'est suffisant pour l'extérieur?"

Je suis là pour t'expliquer! 😊"""

PRODUCT_QUESTIONS_AR = """تمام! اسألني على أي منتج ولا مصطلح تقني.

مثلاً:
- "شنوة PoE؟"
- "الفرق بين NVR و DVR؟"
- "IP67 يكفي للخارج؟"

موجود باش نفسرلك! 😊"""

# Messages pour l'aide au choix
HELP_CHOOSE_FR = """Super! Je vais t'aider à trouver le bon produit.

Tu cherches quoi exactement?
1) 📹 Caméras de surveillance
2) 🚨 Système d'alarme
3) 🚪 Visiophone / Interphone
4) 🔐 Contrôle d'accès (pointeuse, badge)
5) 🏠 Motorisation (volets, portail)
6) 🔌 Autre chose

Réponds avec le numéro ou décris ce que tu cherches."""

HELP_CHOOSE_AR = """ممتاز! باش نعاونك تلقى المنتج المناسب.

شنوة تلوج عليه بالضبط؟
1) 📹 كاميرات مراقبة
2) 🚨 نظام إنذار
3) 🚪 فيزيوفون / إنترفون
4) 🔐 تحكم في الدخول (بوانتوز، باج)
5) 🏠 موتوريزاسيون (ستور، بورتاي)
6) 🔌 حاجة أخرى

جاوبني بالرقم ولا وصفلي شنوة تحب."""

# ============ MODELS ============

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    phase: str
    products: List[Dict] = []
    suggested_actions: List[str] = []

# ============ HELPER FUNCTIONS ============

def detect_language(message: str) -> str:
    """Détecte français ou arabe tunisien"""
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', message))
    return "ar" if arabic_chars > 2 else "fr"

def extract_category(message: str) -> Optional[str]:
    """Extrait la catégorie du message"""
    msg_lower = message.lower()
    
    categories = {
        "videosurveillance": ["caméra", "camera", "كاميرا", "nvr", "dvr", "surveillance", "مراقبة"],
        "videophonie": ["visiophone", "interphone", "sonnette", "فيزيوفون", "جرس"],
        "alarme": ["alarme", "détecteur", "intrusion", "إنذار", "انذار"],
        "controle-d-accès": ["pointeuse", "badge", "accès", "empreinte", "بصمة", "باج"],
        "motorisation": ["volet", "store", "portail", "moteur", "somfy", "ستور", "بورتاي"],
        "reseau": ["switch", "routeur", "wifi", "réseau", "شبكة"],
    }
    
    for cat, keywords in categories.items():
        if any(kw in msg_lower for kw in keywords):
            return cat
    return None

def extract_criteria(message: str) -> Dict:
    """Extrait les critères de recherche"""
    msg_lower = message.lower()
    criteria = {}
    
    # Environnement
    if any(kw in msg_lower for kw in ["extérieur", "exterieur", "outdoor", "خارج", "برا"]):
        criteria["environment"] = "exterieur"
    elif any(kw in msg_lower for kw in ["intérieur", "interieur", "indoor", "داخل"]):
        criteria["environment"] = "interieur"
    
    # Connectivité
    if any(kw in msg_lower for kw in ["wifi", "wi-fi", "sans fil", "ويفي"]):
        criteria["connectivity"] = "Sans fil"
    elif any(kw in msg_lower for kw in ["filaire", "câble", "poe", "بالخيط"]):
        criteria["connectivity"] = "Filaire"
    
    # Marque
    brands = ["dahua", "hikvision", "somfy", "zkteco", "inim", "ruijie", "ajax"]
    for brand in brands:
        if brand in msg_lower:
            criteria["brand"] = brand
            break
    
    return criteria

async def search_products(
    category: Optional[str] = None,
    environment: Optional[str] = None,
    connectivity: Optional[str] = None,
    brand: Optional[str] = None,
    limit: int = 6
) -> List[Dict]:
    """Recherche les produits selon les critères"""
    query = {"active": True, "image_missing": False}
    
    if category:
        query["category_path_ids"] = category
    
    if brand:
        query["brand"] = {"$regex": brand, "$options": "i"}
    
    # Connectivité - être plus flexible
    if connectivity:
        if connectivity == "Sans fil":
            # Inclure WiFi et Hybride
            query["attributes_norm.connectivity"] = {"$in": ["Sans fil", "Hybride"]}
        else:
            query["attributes_norm.connectivity"] = {"$in": [connectivity, "Hybride"]}
    
    # Filtre environnement - extérieur = IP65+ ou mention extérieur
    and_conditions = []
    if environment == "exterieur":
        and_conditions.append({
            "$or": [
                {"name": {"$regex": "ext[ée]rieur|outdoor|ip6[567]|bullet|tube", "$options": "i"}},
                {"description": {"$regex": "ext[ée]rieur|outdoor|ip6[567]", "$options": "i"}},
            ]
        })
    
    if and_conditions:
        query["$and"] = and_conditions
    
    products = await db.products.find(
        query, {"_id": 0}
    ).sort([
        ("ranking.quality_score", -1),
        ("featured", -1)
    ]).limit(limit).to_list(limit)
    
    # Si pas assez de résultats, élargir la recherche
    if len(products) < 3 and category:
        fallback_query = {"active": True, "image_missing": False, "category_path_ids": category}
        if brand:
            fallback_query["brand"] = {"$regex": brand, "$options": "i"}
        products = await db.products.find(
            fallback_query, {"_id": 0}
        ).sort([("ranking.quality_score", -1)]).limit(limit).to_list(limit)
    
    return products

def format_products_for_prompt(products: List[Dict], language: str) -> str:
    """Formate les produits pour le contexte du prompt"""
    if not products:
        return "Aucun produit trouvé." if language == "fr" else "ما لقيت حتى منتج."
    
    lines = []
    for p in products:
        price = p.get("price")
        price_str = f"{price:.3f} DT" if price else "Prix sur demande"
        
        line = f"- **{p.get('name')}** | {p.get('brand', 'N/A')} | {price_str} | ID: {p.get('id')}"
        lines.append(line)
    
    return "\n".join(lines)

async def get_session_history(session_id: str, limit: int = 10) -> List[Dict]:
    """Récupère l'historique de la session"""
    messages = await db.chat_history.find(
        {"session_id": session_id}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    messages.reverse()
    return [{"role": m.get("role"), "content": m.get("content")} for m in messages]

async def save_message(session_id: str, role: str, content: str):
    """Sauvegarde un message"""
    await db.chat_history.insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc)
    })

async def get_session_state(session_id: str) -> Dict:
    """Récupère l'état de la session"""
    state = await db.chat_sessions_gpt.find_one({"session_id": session_id})
    if state:
        return {
            "language": state.get("language"),  # None = pas encore choisi
            "mode": state.get("mode"),  # None, "order", "questions", "help"
            "category": state.get("category"),
            "criteria": state.get("criteria", {}),
            "turn_count": state.get("turn_count", 0),
            "products_shown": state.get("products_shown", []),
            "phase": state.get("phase", "welcome")  # welcome, language_choice, mode_choice, conversation
        }
    return {
        "language": None,
        "mode": None,
        "category": None,
        "criteria": {},
        "turn_count": 0,
        "products_shown": [],
        "phase": "welcome"
    }

async def save_session_state(session_id: str, state: Dict):
    """Sauvegarde l'état de la session"""
    await db.chat_sessions_gpt.update_one(
        {"session_id": session_id},
        {"$set": {
            **state,
            "updated_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )

def process_response(response: str) -> str:
    """Traite la réponse pour ajouter les liens produits"""
    pattern = r'\{+PRODUCT_ACTIONS:([a-zA-Z0-9\-]+)\}+'
    
    def replace_action(match):
        product_id = match.group(1)
        return f'\n🔍 [Voir détails](/produit/{product_id}) | 🛒 [Ajouter au panier](ADD_TO_CART:{product_id})\n'
    
    return re.sub(pattern, replace_action, response)

def extract_product_ids(response: str) -> List[str]:
    """Extrait les IDs de produits de la réponse"""
    patterns = [
        r'/produit/([a-zA-Z0-9\-]+)',
        r'ADD_TO_CART:([a-zA-Z0-9\-]+)',
        r'PRODUCT_ACTIONS:([a-zA-Z0-9\-]+)'
    ]
    
    ids = []
    for pattern in patterns:
        ids.extend(re.findall(pattern, response))
    
    return list(set(ids))

# ============ MAIN CHAT ENDPOINT ============

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal du chatbot GPT-5.2
    Flux: Accueil bilingue → Choix langue → Choix mode → Conversation
    """
    try:
        # 1. Session
        session_id = request.session_id or str(uuid.uuid4())
        state = await get_session_state(session_id)
        msg = request.message.strip()
        
        response_text = ""
        products_mentioned = []
        
        # ============ PHASE 1: ACCUEIL (première interaction) ============
        if state["phase"] == "welcome" and state["turn_count"] == 0:
            response_text = WELCOME_MESSAGE
            state["phase"] = "language_choice"
            state["turn_count"] += 1
            
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase=state["phase"],
                products=[],
                suggested_actions=[]
            )
        
        # ============ PHASE 2: CHOIX DE LANGUE ============
        if state["phase"] == "language_choice":
            if msg in ["1", "تونسي", "tounsi", "tunisien"]:
                state["language"] = "ar"
                response_text = OPTIONS_AR
            elif msg in ["2", "francais", "français", "french", "fr"]:
                state["language"] = "fr"
                response_text = OPTIONS_FR
            else:
                # Détecter automatiquement
                if len(re.findall(r'[\u0600-\u06FF]', msg)) > 2:
                    state["language"] = "ar"
                    response_text = OPTIONS_AR
                else:
                    state["language"] = "fr"
                    response_text = OPTIONS_FR
            
            state["phase"] = "mode_choice"
            state["turn_count"] += 1
            
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase=state["phase"],
                products=[],
                suggested_actions=[]
            )
        
        # ============ PHASE 3: CHOIX DU MODE ============
        if state["phase"] == "mode_choice":
            lang = state["language"] or "fr"
            
            if msg == "1":
                state["mode"] = "order"
                response_text = ORDER_TRACKING_AR if lang == "ar" else ORDER_TRACKING_FR
            elif msg == "2":
                state["mode"] = "questions"
                response_text = PRODUCT_QUESTIONS_AR if lang == "ar" else PRODUCT_QUESTIONS_FR
            elif msg == "3":
                state["mode"] = "help"
                response_text = HELP_CHOOSE_AR if lang == "ar" else HELP_CHOOSE_FR
            else:
                # Réafficher les options
                response_text = OPTIONS_AR if lang == "ar" else OPTIONS_FR
                
                await save_session_state(session_id, state)
                await save_message(session_id, "user", msg)
                await save_message(session_id, "assistant", response_text)
                
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    phase=state["phase"],
                    products=[],
                    suggested_actions=[]
                )
            
            state["phase"] = "conversation"
            state["turn_count"] += 1
            
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase=state["phase"],
                products=[],
                suggested_actions=[]
            )
        
        # ============ PHASE 4: CONVERSATION ============
        lang = state["language"] or "fr"
        mode = state["mode"] or "questions"
        
        # MODE SUIVI COMMANDE
        if mode == "order":
            # Simuler le suivi de commande
            order_match = re.search(r'CMD-?\d+', msg.upper())
            if order_match:
                order_num = order_match.group()
                if lang == "ar":
                    response_text = f"""✅ الطلبية **{order_num}**

📦 الحالة: **في الطريق**
🚚 شركة التوصيل: Aramex
📅 التاريخ المتوقع: خلال 2-3 أيام

تحب تسأل على حاجة أخرى؟"""
                else:
                    response_text = f"""✅ Commande **{order_num}**

📦 Statut: **En cours de livraison**
🚚 Transporteur: Aramex
📅 Date estimée: Dans 2-3 jours

Tu veux savoir autre chose?"""
            else:
                if lang == "ar":
                    response_text = "عطيني رقم الطلبية من فضلك (مثال: CMD-12345)"
                else:
                    response_text = "Donne-moi le numéro de commande (ex: CMD-12345)"
            
            state["turn_count"] += 1
            await save_session_state(session_id, state)
            await save_message(session_id, "user", msg)
            await save_message(session_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                phase="conversation",
                products=[],
                suggested_actions=[]
            )
        
        # MODE QUESTIONS ou AIDE AU CHOIX
        # Extraction catégorie et critères
        category = extract_category(msg)
        if category:
            state["category"] = category
        
        new_criteria = extract_criteria(msg)
        state["criteria"].update(new_criteria)
        
        # Recherche produits si on a une catégorie
        products = []
        if state["category"]:
            products = await search_products(
                category=state["category"],
                environment=state["criteria"].get("environment"),
                connectivity=state["criteria"].get("connectivity"),
                brand=state["criteria"].get("brand"),
                limit=6
            )
        
        # Construire le contexte
        products_text = format_products_for_prompt(products, lang)
        history = await get_session_history(session_id, limit=8)
        
        history_text = ""
        if history:
            history_text = "\n".join([
                f"{m['role'].title()}: {m['content'][:200]}" 
                for m in history[-6:]
            ])
        
        # Instructions selon le mode
        mode_instruction = ""
        if mode == "help" and products:
            mode_instruction = f"""
⚠️ MODE AIDE AU CHOIX ACTIVÉ:
Tu as {len(products)} produits disponibles. Après 2-3 questions, propose des produits!
Pour chaque produit recommandé, utilise: {{{{PRODUCT_ACTIONS:product_id}}}}
"""
        elif mode == "questions":
            mode_instruction = """
⚠️ MODE QUESTIONS ACTIVÉ:
Réponds aux questions sans proposer de produits.
Sois informatif et pédagogue.
"""
        
        lang_instruction = "RÉPONDS EN ARABE TUNISIEN (dialecte)" if lang == "ar" else "Réponds en français"
        
        context = f"""
📦 CATALOGUE ({len(products)} produits):
{products_text if products else "Pas de produits spécifiques."}

💬 HISTORIQUE:
{history_text or 'Début de conversation'}

{mode_instruction}

⚠️ LANGUE: {lang_instruction}!
"""
        
        # Appel GPT-5.2
        system_prompt = SYSTEM_PROMPT_AR if lang == "ar" else SYSTEM_PROMPT_FR
        full_prompt = system_prompt.format(context=context)
        
        chat_instance = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"mydar-gpt-{session_id}",
            system_message=full_prompt
        ).with_model("openai", "gpt-5.2")
        
        response_text = await chat_instance.send_message(UserMessage(text=msg))
        
        # Traitement de la réponse
        response_text = process_response(response_text)
        
        # Extraire les produits mentionnés
        mentioned_ids = extract_product_ids(response_text)
        for pid in mentioned_ids[:6]:
            product = await db.products.find_one({"id": pid}, {"_id": 0})
            if product:
                products_mentioned.append({
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "brand": product.get("brand"),
                    "price": product.get("price"),
                    "image": product.get("image_url") or product.get("image"),
                    "category": product.get("category"),
                })
        
        state["turn_count"] += 1
        state["products_shown"].extend([p["id"] for p in products_mentioned])
        
        await save_session_state(session_id, state)
        await save_message(session_id, "user", msg)
        await save_message(session_id, "assistant", response_text)
        
        print(f"[GPT-5.2] Session: {session_id[:8]}, Mode: {mode}, Products: {len(products_mentioned)}")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            phase="conversation",
            products=products_mentioned,
            suggested_actions=[]
        )
        
    except Exception as e:
        print(f"[GPT-5.2 Error] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
        "messages": [
            {
                "role": m.get("role"),
                "content": m.get("content"),
                "timestamp": m.get("timestamp").isoformat() if m.get("timestamp") else None
            }
            for m in messages
        ]
    }

@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Efface l'historique d'une session"""
    r1 = await db.chat_history.delete_many({"session_id": session_id})
    r2 = await db.chat_sessions_gpt.delete_many({"session_id": session_id})
    
    return {
        "messages_deleted": r1.deleted_count,
        "sessions_deleted": r2.deleted_count
    }

@router.post("/reset/{session_id}")
async def reset_session(session_id: str):
    """Réinitialise une session"""
    await db.chat_history.delete_many({"session_id": session_id})
    await db.chat_sessions_gpt.delete_many({"session_id": session_id})
    
    return {
        "old_session_id": session_id,
        "new_session_id": str(uuid.uuid4()),
        "message": "Session réinitialisée"
    }
