"""
AI Moderation Service using Gemini
Detects subtle off-topic content and inappropriate announcements
"""
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

MODERATION_PROMPT = """Tu es un modérateur expert pour MyDar, une plateforme tunisienne où les CLIENTS cherchent des PROFESSIONNELS pour la domotique.

DOMAINES ACCEPTÉS (Smart Home uniquement):
- Domotique et automatisation maison
- Vidéosurveillance et caméras
- Alarmes et sécurité
- Éclairage connecté
- Contrôle d'accès (serrures, interphones)
- Réseaux WiFi/câblage
- Volets/portails motorisés
- Capteurs et détecteurs
- Thermostats connectés

ANNONCE À ANALYSER:
Titre: {title}
Description: {description}
Catégorie: {category}

CRITÈRES DE REJET STRICTS:

1. HORS SUJET (rejeter si NON lié à la domotique):
   - Plomberie, électricité générale, maçonnerie, peinture
   - Comptabilité, garde d'enfants, cours particuliers
   - Ménage, jardinage (sauf arrosage connecté), déménagement
   - Restauration, coiffure, massage, etc.

2. PUBLICITÉ/PROMOTION (rejeter si l'auteur VEND au lieu de CHERCHER):
   - "Nous proposons", "Notre entreprise", "Nos services"
   - "Meilleur prix", "Promotion", "Contactez-nous"
   - L'annonce doit être d'un CLIENT qui CHERCHE un pro

3. SPAM/ARNAQUE:
   - Offres trop belles, demandes d'argent suspects

Réponds UNIQUEMENT avec ce JSON:
{{"approved": true/false, "confidence": 0.0-1.0, "reason": "explication courte", "category_suggestion": "domaine suggéré ou null"}}"""


async def ai_moderate_annonce(title: str, description: str, category: str) -> dict:
    """Use Gemini AI to moderate an announcement"""
    
    if not EMERGENT_LLM_KEY:
        logger.warning("EMERGENT_LLM_KEY not set, skipping AI moderation")
        return {"approved": True, "confidence": 0.0, "reason": "", "ai_used": False}
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        prompt = MODERATION_PROMPT.format(
            title=title,
            description=description,
            category=category
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"mod-{hash(title) % 10000}",
            system_message="Réponds uniquement en JSON valide."
        ).with_model("gemini", "gemini-2.0-flash")
        
        user_message = UserMessage(text=prompt)
        response_text = await chat.send_message(user_message)
        
        logger.info(f"AI moderation raw: {response_text[:200]}")
        
        # Parse JSON from response
        clean = response_text.strip()
        
        # Remove markdown code blocks
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0]
        elif "```" in clean:
            parts = clean.split("```")
            for p in parts:
                p = p.strip()
                if p.startswith("{"):
                    clean = p
                    break
        
        clean = clean.strip()
        
        result = json.loads(clean)
        
        return {
            "approved": result.get("approved", True),
            "confidence": float(result.get("confidence", 0.5)),
            "reason": result.get("reason", ""),
            "category_suggestion": result.get("category_suggestion"),
            "ai_used": True
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}, response: {response_text[:100]}")
        return {"approved": True, "confidence": 0.0, "reason": "Parse error", "ai_used": True}
        
    except Exception as e:
        logger.error(f"AI moderation error: {type(e).__name__}: {e}")
        return {"approved": True, "confidence": 0.0, "reason": str(e), "ai_used": False}


async def get_ai_rejection_message(ai_result: dict) -> str:
    """Format AI rejection message for user"""
    if ai_result.get("approved", True):
        return ""
    
    reason = ai_result.get("reason", "Contenu non approprié pour MyDar")
    suggestion = ai_result.get("category_suggestion")
    
    message = f"❌ Annonce refusée : {reason}"
    
    if suggestion:
        message += f"\n💡 Suggestion : Cette demande concerne plutôt \"{suggestion}\". MyDar est spécialisé en domotique."
    
    return message
