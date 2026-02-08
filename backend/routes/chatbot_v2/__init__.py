"""
MyDar Chatbot V2 - Conseiller Vendeur Intelligent
Router principal FastAPI
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, List
from datetime import datetime, timezone
import os
import uuid
import re
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from emergentintegrations.llm.chat import LlmChat, UserMessage

from .models import (
    ChatRequest, ChatResponse, ConversationState, 
    ConversationPhase, UserNeed
)
from .prompts import ADVISOR_SYSTEM_PROMPT, PRODUCTS_CONTEXT_TEMPLATE
from .advisor import AdvisorEngine

load_dotenv()

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'mydar_db')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Initialize advisor engine
advisor = AdvisorEngine(db)


# ============ SESSION MANAGEMENT ============

async def get_session_state(session_id: str) -> ConversationState:
    """Récupère ou crée l'état de session"""
    session = await db.chat_sessions_v2.find_one({"session_id": session_id})
    
    if session:
        return ConversationState(
            session_id=session_id,
            phase=ConversationPhase(session.get("phase", "greeting")),
            language=session.get("language", "fr"),
            user_need=UserNeed(**session.get("user_need", {})),
            questions_asked=session.get("questions_asked", []),
            products_shown=session.get("products_shown", []),
            cart_items=session.get("cart_items", []),
            last_search_results=session.get("last_search_results", []),
            context_history=session.get("context_history", []),
            turn_count=session.get("turn_count", 0)
        )
    
    return ConversationState(session_id=session_id)


async def save_session_state(state: ConversationState):
    """Sauvegarde l'état de session"""
    await db.chat_sessions_v2.update_one(
        {"session_id": state.session_id},
        {"$set": {
            "phase": state.phase.value,
            "language": state.language,
            "user_need": state.user_need.model_dump(),
            "questions_asked": state.questions_asked,
            "products_shown": state.products_shown,
            "cart_items": state.cart_items,
            "last_search_results": state.last_search_results,
            "context_history": state.context_history[-20:],  # Keep last 20
            "turn_count": state.turn_count,
            "updated_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )


async def save_message(session_id: str, role: str, content: str):
    """Sauvegarde un message dans l'historique"""
    await db.chat_history.insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc)
    })


# ============ RESPONSE PROCESSING ============

def process_product_actions(response: str) -> str:
    """Convertit les balises {{PRODUCT_ACTIONS:id}} en liens"""
    pattern = r'\{+PRODUCT_ACTIONS:([a-zA-Z0-9\-]+)\}+'
    
    def replace_action(match):
        product_id = match.group(1)
        return f'\n🔍 [Voir détails](/produit/{product_id}) | 🛒 [Ajouter au panier](ADD_TO_CART:{product_id})\n'
    
    return re.sub(pattern, replace_action, response)


def extract_product_ids_from_response(response: str) -> List[str]:
    """Extrait les IDs de produits de la réponse"""
    ids = []
    patterns = [
        r'/produit/([a-zA-Z0-9\-]+)',
        r'ADD_TO_CART:([a-zA-Z0-9\-]+)',
        r'\{+PRODUCT_ACTIONS:([a-zA-Z0-9\-]+)\}+'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response)
        ids.extend(matches)
    
    return list(set(ids))


# ============ MAIN CHAT ENDPOINT ============

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal du chatbot conseiller intelligent
    """
    try:
        # 1. Session management
        session_id = request.session_id or str(uuid.uuid4())
        state = await get_session_state(session_id)
        
        # 2. Detect language
        detected_lang = advisor.detect_language(request.message)
        if state.turn_count == 0:
            state.language = detected_lang
        elif len(request.message) > 5 and request.message.strip() not in "0123456789":
            state.language = detected_lang
        
        # 3. Detect intent
        intent = advisor.detect_intent(request.message)
        
        # 4. Update state based on message
        if intent == "number_response":
            last_question = state.context_history[-1].get("content") if state.context_history else None
            state.user_need = advisor.process_numeric_response(
                request.message, state, last_question
            )
        else:
            state.user_need = advisor.extract_criteria_from_message(request.message, state)
        
        # 5. Determine conversation phase
        phase = advisor.determine_phase(state, intent)
        state.phase = phase
        
        # 6. Generate response based on phase
        response_text = ""
        products_to_show = []
        suggested_questions = []
        compatibility_warnings = []
        
        if phase == ConversationPhase.GREETING and state.turn_count == 0:
            # First message - greeting
            response_text = await advisor.generate_greeting(state.language)
            
        elif phase == ConversationPhase.EXPLANATION:
            # Technical explanation
            response_text = await handle_explanation(request.message, state)
            
        elif phase == ConversationPhase.DISCOVERY:
            # Need more info - ask a question
            next_q = advisor.get_next_question(state)
            if next_q:
                question_id, _, _ = next_q
                state.questions_asked.append(question_id)
                response_text = await advisor.generate_discovery_response(state, next_q)
            else:
                # Fallback to recommendation
                phase = ConversationPhase.RECOMMENDATION
                state.phase = phase
                
        if phase == ConversationPhase.RECOMMENDATION:
            # Get and show products
            products, metadata = await advisor.get_product_recommendations(state)
            products_to_show = products
            state.products_shown = [p.get("id") for p in products]
            state.last_search_results = products
            compatibility_warnings = metadata.get("compatibility_warnings", [])
            
            if not response_text:
                response_text = await advisor.generate_recommendation_response(
                    products, state, metadata
                )
        
        # 7. If still no response, use Gemini for complex cases
        if not response_text:
            response_text = await generate_gemini_response(request.message, state, products_to_show)
        
        # 8. Process product action tags
        response_text = process_product_actions(response_text)
        
        # 9. Extract mentioned product IDs and fetch details
        mentioned_ids = extract_product_ids_from_response(response_text)
        products_mentioned = []
        if mentioned_ids:
            for pid in mentioned_ids[:6]:
                product = await advisor.search_engine.get_product_by_id(pid)
                if product:
                    products_mentioned.append({
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "brand": product.get("brand"),
                        "price": product.get("price"),
                        "image": product.get("image_url") or product.get("image"),
                        "category": product.get("category"),
                    })
        
        # 10. Update context history
        state.context_history.append({"role": "user", "content": request.message})
        state.context_history.append({"role": "assistant", "content": response_text})
        state.turn_count += 1
        
        # 11. Save state and messages
        await save_session_state(state)
        await save_message(session_id, "user", request.message)
        await save_message(session_id, "assistant", response_text)
        
        print(f"[ChatV2] Session: {session_id[:8]}, Phase: {phase.value}, Products: {len(products_mentioned)}")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            phase=phase.value,
            products=products_mentioned,
            suggested_questions=suggested_questions,
            compatibility_warnings=compatibility_warnings
        )
        
    except Exception as e:
        print(f"[ChatV2 Error] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============ HELPER FUNCTIONS ============

async def handle_explanation(message: str, state: ConversationState) -> str:
    """Gère les demandes d'explication technique"""
    lang = state.language
    
    # Chercher les termes techniques dans le message
    technical_terms = ["poe", "nvr", "dvr", "ip67", "ip65", "onvif", "h265", "h.265", 
                       "rts", "io", "zigbee", "wiegand"]
    
    for term in technical_terms:
        if term in message.lower():
            explanation = advisor.get_technical_explanation(term, lang)
            if explanation:
                if lang == "fr":
                    return f"📖 **{term.upper()}**\n\n{explanation}\n\nAutre question?"
                else:
                    return f"📖 **{term.upper()}**\n\n{explanation}\n\nسؤال آخر؟"
    
    # Fallback to Gemini for complex explanations
    return await generate_gemini_response(message, state, [])


async def generate_gemini_response(
    message: str, 
    state: ConversationState,
    products: List[Dict]
) -> str:
    """Génère une réponse via Gemini pour les cas complexes"""
    
    # Format products for context
    if products:
        products_text = "\n".join([
            f"• **{p.get('name')}** — {p.get('brand')} — {p.get('price', 0):.3f} DT — ID: {p.get('id')}"
            for p in products[:10]
        ])
    else:
        products_text = "Aucun produit trouvé pour cette recherche."
    
    # Format history
    history_text = "\n".join([
        f"{m.get('role', 'user').title()}: {m.get('content', '')[:200]}"
        for m in state.context_history[-6:]
    ])
    
    # Build context
    need = state.user_need
    context = PRODUCTS_CONTEXT_TEMPLATE.format(
        products=products_text,
        category=need.category or "Non définie",
        environment=need.environment or "Non défini",
        connectivity=need.connectivity or "Non définie",
        brand=need.brand_preference or "Pas de préférence",
        budget=f"{need.budget_max} DT" if need.budget_max else "Non défini",
        history=history_text or "Nouvelle conversation"
    )
    
    # Add language instruction
    if state.language == "ar":
        context += "\n\n⚠️ IMPORTANT: Réponds UNIQUEMENT en arabe tunisien!"
    else:
        context += "\n\n⚠️ IMPORTANT: Réponds UNIQUEMENT en français!"
    
    # Build full prompt
    full_prompt = ADVISOR_SYSTEM_PROMPT.format(extra_context=context)
    
    # Call Gemini
    chat_instance = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"mydar-v2-{state.session_id}",
        system_message=full_prompt
    ).with_model("gemini", "gemini-2.0-flash")
    
    response = await chat_instance.send_message(UserMessage(text=message))
    
    return response


# ============ ADDITIONAL ENDPOINTS ============

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
    """Efface l'historique et l'état d'une session"""
    result1 = await db.chat_history.delete_many({"session_id": session_id})
    result2 = await db.chat_sessions_v2.delete_many({"session_id": session_id})
    
    return {
        "messages_deleted": result1.deleted_count,
        "sessions_deleted": result2.deleted_count
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Récupère l'état d'une session"""
    state = await get_session_state(session_id)
    return {
        "session_id": session_id,
        "phase": state.phase.value,
        "language": state.language,
        "user_need": state.user_need.model_dump(),
        "turn_count": state.turn_count,
        "products_shown": len(state.products_shown)
    }


@router.post("/reset/{session_id}")
async def reset_session(session_id: str):
    """Réinitialise une session (nouvelle conversation)"""
    await db.chat_history.delete_many({"session_id": session_id})
    await db.chat_sessions_v2.delete_many({"session_id": session_id})
    
    new_session_id = str(uuid.uuid4())
    return {
        "old_session_id": session_id,
        "new_session_id": new_session_id,
        "message": "Session réinitialisée"
    }


# ============ ADMIN ENDPOINTS ============

@router.get("/admin/stats")
async def get_stats(range: str = "7d"):
    """Statistiques admin du chatbot"""
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    date_filters = {"1d": 1, "7d": 7, "30d": 30}
    days = date_filters.get(range, 7)
    date_filter = now - timedelta(days=days)
    
    messages = await db.chat_history.find(
        {"timestamp": {"$gte": date_filter}}
    ).to_list(10000)
    
    sessions = set(m.get("session_id") for m in messages)
    
    # Stats par phase
    phase_stats = await db.chat_sessions_v2.aggregate([
        {"$group": {"_id": "$phase", "count": {"$sum": 1}}}
    ]).to_list(10)
    
    return {
        "total_conversations": len(sessions),
        "total_messages": len(messages),
        "avg_messages_per_conv": round(len(messages) / max(len(sessions), 1), 1),
        "phase_distribution": {p["_id"]: p["count"] for p in phase_stats}
    }


@router.get("/admin/conversations")
async def get_conversations(range: str = "7d", limit: int = 50):
    """Liste des conversations récentes"""
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    date_filters = {"1d": 1, "7d": 7, "30d": 30, "all": 365}
    days = date_filters.get(range, 7)
    date_filter = now - timedelta(days=days)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": date_filter}}},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$session_id",
            "message_count": {"$sum": 1},
            "last_activity": {"$first": "$timestamp"},
            "first_message": {"$last": "$content"},
            "last_message": {"$first": "$content"},
        }},
        {"$sort": {"last_activity": -1}},
        {"$limit": limit}
    ]
    
    conversations = await db.chat_history.aggregate(pipeline).to_list(limit)
    
    result = []
    for conv in conversations:
        # Detect language
        all_text = f"{conv.get('first_message', '')} {conv.get('last_message', '')}"
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', all_text))
        language = "AR 🇹🇳" if has_arabic else "FR 🇫🇷"
        
        result.append({
            "session_id": conv["_id"],
            "message_count": conv["message_count"],
            "last_activity": conv["last_activity"].isoformat() if conv.get("last_activity") else None,
            "first_message": conv.get("first_message", "")[:100],
            "last_message": conv.get("last_message", "")[:100],
            "language": language
        })
    
    return {"conversations": result, "total": len(result)}
