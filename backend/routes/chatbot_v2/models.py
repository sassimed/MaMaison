"""
Modèles Pydantic pour le Chatbot Conseiller
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class ConversationPhase(str, Enum):
    """Phases de la conversation de vente"""
    GREETING = "greeting"           # Accueil initial
    DISCOVERY = "discovery"         # Découverte du besoin
    RECOMMENDATION = "recommendation"  # Proposition de produits
    COMPARISON = "comparison"       # Comparaison de produits
    EXPLANATION = "explanation"     # Explication technique
    UPSELL = "upsell"              # Produits complémentaires
    CLOSING = "closing"            # Finalisation


class ProductCategory(str, Enum):
    """Catégories principales de produits"""
    VIDEOSURVEILLANCE = "videosurveillance"
    VIDEOPHONIE = "videophonie"
    ALARME = "alarme"
    CONTROLE_ACCES = "controle-d-accès"
    MOTORISATION = "motorisation"
    RESEAU = "reseau"
    INTERRUPTEUR = "interrupteur"
    PRISE = "prise"
    ECLAIRAGE = "eclairage"


class UserNeed(BaseModel):
    """Besoin identifié de l'utilisateur"""
    category: Optional[str] = None
    subcategory: Optional[str] = None
    environment: Optional[str] = None  # interieur / exterieur
    connectivity: Optional[str] = None  # wifi / filaire / hybride
    brand_preference: Optional[str] = None
    budget_max: Optional[float] = None
    quantity: Optional[int] = None
    specific_features: List[str] = []
    use_case: Optional[str] = None  # maison / commerce / bureau
    technical_level: Optional[str] = None  # debutant / intermediaire / expert


class ConversationState(BaseModel):
    """État de la conversation"""
    session_id: str
    phase: ConversationPhase = ConversationPhase.GREETING
    language: str = "fr"  # fr / ar
    user_need: UserNeed = UserNeed()
    questions_asked: List[str] = []
    products_shown: List[str] = []
    cart_items: List[str] = []
    last_search_results: List[Dict] = []
    context_history: List[Dict] = []
    turn_count: int = 0


class ChatRequest(BaseModel):
    """Requête de chat"""
    message: str
    session_id: Optional[str] = None


class ProductRecommendation(BaseModel):
    """Recommandation de produit"""
    product_id: str
    name: str
    brand: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None
    why_recommended: str  # Explication pourquoi ce produit
    key_features: List[str] = []
    compatibility_notes: List[str] = []


class ChatResponse(BaseModel):
    """Réponse du chatbot"""
    response: str
    session_id: str
    phase: str
    products: List[Dict] = []
    suggested_questions: List[str] = []
    compatibility_warnings: List[str] = []
