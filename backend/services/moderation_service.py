"""
Annonce Moderation Service - Auto-validation for MyDar
Automatically detects and rejects inappropriate content
"""
import re
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============

# Valid categories for MyDar (Smart Home related)
VALID_CATEGORIES = [
    "domotique", "alarme", "vidéosurveillance", "surveillance", "caméra", "camera",
    "serrure", "contrôle d'accès", "controle d'acces", "accès", "acces",
    "éclairage", "eclairage", "lumière", "lumiere", "led", "ampoule",
    "thermostat", "climatisation", "chauffage", "température", "temperature",
    "volet", "store", "rideau", "motorisation", "portail", "garage",
    "réseau", "reseau", "wifi", "internet", "câblage", "cablage", "fibre",
    "interphone", "visiophone", "sonnette",
    "capteur", "détecteur", "detecteur", "mouvement", "présence", "presence",
    "audio", "multiroom", "sonorisation", "enceinte",
    "assistant", "vocal", "alexa", "google home", "siri",
    "scénario", "scenario", "automatisation", "programmation",
    "sécurité", "securite", "protection", "intrusion",
    "station météo", "meteo", "arrosage", "jardin",
    "prise", "connectée", "connectee", "smart", "intelligent",
    "système d'alarme", "systeme", "centrale",
    "installation", "configuration", "maintenance", "dépannage", "depannage",
    "audit", "conseil", "expertise"
]

# Off-topic keywords (services not related to smart home)
OFF_TOPIC_KEYWORDS = [
    # Plomberie
    "plomberie", "plombier", "fuite", "robinet", "tuyau", "canalisation", "évier", "evier",
    "wc", "toilette", "chasse d'eau", "baignoire", "douche", "lavabo", "siphon",
    # Électricité générale (non domotique)
    "tableau électrique", "disjoncteur", "prise murale", "interrupteur simple",
    # Maçonnerie
    "maçon", "macon", "maçonnerie", "maconnerie", "ciment", "béton", "beton", "mur", "carrelage",
    # Peinture
    "peinture", "peintre", "peindre", "tapisserie",
    # Menuiserie classique
    "menuisier", "menuiserie", "porte", "fenêtre", "fenetre", "parquet",
    # Déménagement
    "déménagement", "demenagement", "déménageur", "demenageur",
    # Nettoyage
    "nettoyage", "femme de ménage", "menage", "entretien ménager",
    # Jardinage (non connecté)
    "jardinier", "taille", "pelouse", "tonte", "élagage", "elagage",
    # Cuisine
    "cuisinier", "traiteur", "restauration",
    # Autres
    "coiffeur", "coiffure", "esthétique", "massage", "garde d'enfants", "baby-sitting",
    "cours particuliers", "soutien scolaire", "traduction"
]

# Insults and profanity (French)
INSULTS_FR = [
    "con", "connard", "connasse", "pute", "putain", "merde", "enculé", "encule",
    "salaud", "salope", "bâtard", "batard", "nique", "niquer", "fdp", "pd",
    "taré", "tare", "débile", "debile", "crétin", "cretin", "abruti",
    "imbécile", "imbecile", "enfoiré", "enfoire", "ordure", "pourri", "dégueulasse",
    "degueulasse", "clochard", "racaille", "bouffon", "casse-toi", "va te faire"
]

# Insults and profanity (Tunisian Arabic - transliterated)
INSULTS_AR_TN = [
    "zebi", "zab", "kahba", "kelb", "kalb", "hmar", "bagra", "9ahba",
    "nik", "nayek", "miboun", "zamel", "koss", "kiss", "tefl", "tofla",
    "manyak", "manyouk", "sharmouta", "charmou6a", "weld el", "bent el",
    "ya 7mar", "ya kelb", "tfou", "a7chek"
]

# Advertising keywords
ADVERTISING_KEYWORDS = [
    "promotion", "promo", "solde", "réduction", "reduction", "remise", "-50%", "-30%", "-20%",
    "gratuit", "offre spéciale", "offre speciale", "meilleur prix", "pas cher",
    "visitez notre", "cliquez", "achetez maintenant", "commandez",
    "livraison gratuite", "satisfait ou remboursé", "exclusif",
    "dernière chance", "derniere chance", "offre limitée", "offre limitee",
    "profitez maintenant", "bénéficiez de", "beneficiez de", "gagnez", "loterie", "concours",
    "prix cassé", "prix casse", "braderie", "destockage", "liquidation"
]

# Phone number patterns (Tunisian and international)
PHONE_PATTERNS = [
    r'\+216\s*\d{2}\s*\d{3}\s*\d{3}',  # +216 XX XXX XXX
    r'\+216\d{8}',                       # +216XXXXXXXX
    r'00216\s*\d{8}',                    # 00216XXXXXXXX
    r'\b[2-9]\d{7}\b',                   # 8 digits starting with 2-9 (local TN)
    r'\b\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b', # XX XXX XXX or XX-XXX-XXX
    r'\b\d{3}[\s.-]?\d{3}[\s.-]?\d{3}\b', # XXX XXX XXX
    r'tel\s*:\s*\d+',                    # tel: XXXXX
    r'telephone\s*:\s*\d+',              # telephone: XXXXX
    r'appel\w*\s+\d+',                   # appelez XXXXX
    r'num[ée]ro\s*:\s*\d+',              # numéro: XXXXX
]

# Email pattern
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# URL pattern
URL_PATTERN = r'https?://[^\s]+|www\.[^\s]+'


# ============ MODERATION FUNCTIONS ============

def check_phone_numbers(text: str) -> Tuple[bool, List[str]]:
    """Check for phone numbers in text"""
    found = []
    text_lower = text.lower()
    
    for pattern in PHONE_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        found.extend(matches)
    
    return len(found) > 0, found


def check_emails(text: str) -> Tuple[bool, List[str]]:
    """Check for email addresses in text"""
    matches = re.findall(EMAIL_PATTERN, text, re.IGNORECASE)
    return len(matches) > 0, matches


def check_urls(text: str) -> Tuple[bool, List[str]]:
    """Check for URLs in text"""
    matches = re.findall(URL_PATTERN, text, re.IGNORECASE)
    return len(matches) > 0, matches


def check_insults(text: str) -> Tuple[bool, List[str]]:
    """Check for insults and profanity"""
    found = []
    text_lower = text.lower()
    
    # Split into words for exact matching
    words = re.findall(r'\b\w+\b', text_lower)
    
    # Check French insults - require word boundary matching
    for insult in INSULTS_FR:
        # Use word boundary to avoid matching parts of words
        pattern = r'\b' + re.escape(insult) + r'\b'
        if re.search(pattern, text_lower):
            # Additional check: make sure it's not part of a longer word
            if insult in words:
                found.append(insult)
    
    # Check Tunisian Arabic insults
    for insult in INSULTS_AR_TN:
        pattern = r'\b' + re.escape(insult) + r'\b'
        if re.search(pattern, text_lower):
            if insult in words:
                found.append(insult)
    
    return len(found) > 0, list(set(found))


def check_advertising(text: str) -> Tuple[bool, List[str]]:
    """Check for advertising/promotional content"""
    found = []
    text_lower = text.lower()
    
    for keyword in ADVERTISING_KEYWORDS:
        if keyword.lower() in text_lower:
            found.append(keyword)
    
    return len(found) > 0, list(set(found))


def check_off_topic(text: str, category: str) -> Tuple[bool, List[str], str]:
    """
    Check if content is off-topic (not related to smart home/domotique)
    Returns: (is_off_topic, found_keywords, suggested_message)
    """
    found = []
    text_lower = text.lower()
    category_lower = category.lower() if category else ""
    combined_text = f"{text_lower} {category_lower}"
    
    # Check for off-topic keywords
    for keyword in OFF_TOPIC_KEYWORDS:
        if keyword.lower() in combined_text:
            found.append(keyword)
    
    # Check if any valid category keyword is present
    has_valid_category = False
    for valid_cat in VALID_CATEGORIES:
        if valid_cat.lower() in combined_text:
            has_valid_category = True
            break
    
    # If off-topic keywords found and no valid category
    if found and not has_valid_category:
        suggestion = "MyDar est spécialisé dans la domotique et les maisons intelligentes. " \
                    "Pour ce type de service, nous vous recommandons de contacter un professionnel spécialisé."
        return True, list(set(found)), suggestion
    
    return False, [], ""


def moderate_annonce(title: str, description: str, category: str) -> dict:
    """
    Main moderation function - checks an annonce for all issues
    
    Returns:
        dict with:
        - approved: bool
        - rejection_reasons: list of reasons if rejected
        - details: dict with specific findings
    """
    combined_text = f"{title} {description}"
    
    result = {
        "approved": True,
        "rejection_reasons": [],
        "details": {
            "phone_numbers": [],
            "emails": [],
            "urls": [],
            "insults": [],
            "advertising": [],
            "off_topic": []
        }
    }
    
    # Check for phone numbers
    has_phone, phones = check_phone_numbers(combined_text)
    if has_phone:
        result["approved"] = False
        result["rejection_reasons"].append(
            "Numéros de téléphone détectés. Les coordonnées sont partagées après validation."
        )
        result["details"]["phone_numbers"] = phones
    
    # Check for emails
    has_email, emails = check_emails(combined_text)
    if has_email:
        result["approved"] = False
        result["rejection_reasons"].append(
            "Adresses email détectées. Les coordonnées sont partagées après validation."
        )
        result["details"]["emails"] = emails
    
    # Check for URLs
    has_url, urls = check_urls(combined_text)
    if has_url:
        result["approved"] = False
        result["rejection_reasons"].append(
            "Liens web détectés. Les publicités ne sont pas autorisées."
        )
        result["details"]["urls"] = urls
    
    # Check for insults
    has_insults, insults = check_insults(combined_text)
    if has_insults:
        result["approved"] = False
        result["rejection_reasons"].append(
            "Contenu inapproprié détecté. Veuillez reformuler votre annonce de manière respectueuse."
        )
        result["details"]["insults"] = insults
    
    # Check for advertising
    has_ads, ads = check_advertising(combined_text)
    if has_ads:
        result["approved"] = False
        result["rejection_reasons"].append(
            "Contenu publicitaire détecté. Les annonces promotionnelles ne sont pas autorisées."
        )
        result["details"]["advertising"] = ads
    
    # Check for off-topic content
    is_off_topic, off_topic_keywords, suggestion = check_off_topic(combined_text, category)
    if is_off_topic:
        result["approved"] = False
        result["rejection_reasons"].append(
            f"Contenu hors sujet détecté ({', '.join(off_topic_keywords[:3])}). {suggestion}"
        )
        result["details"]["off_topic"] = off_topic_keywords
    
    logger.info(f"Moderation result: approved={result['approved']}, reasons={len(result['rejection_reasons'])}")
    
    return result


def get_rejection_message(moderation_result: dict) -> str:
    """Format rejection message for user"""
    if moderation_result["approved"]:
        return ""
    
    reasons = moderation_result["rejection_reasons"]
    if len(reasons) == 1:
        return f"❌ Annonce refusée : {reasons[0]}"
    
    message = "❌ Annonce refusée pour les raisons suivantes :\n"
    for i, reason in enumerate(reasons, 1):
        message += f"  {i}. {reason}\n"
    
    return message.strip()


async def moderate_annonce_with_ai(title: str, description: str, category: str) -> dict:
    """
    Combined moderation: Rule-based first, then AI for subtle cases
    
    Returns:
        dict with:
        - approved: bool
        - rejection_reasons: list
        - details: dict
        - ai_analysis: dict (if AI was used)
    """
    # First, run rule-based moderation
    rule_result = moderate_annonce(title, description, category)
    
    # If rule-based already rejected, return immediately
    if not rule_result["approved"]:
        rule_result["ai_analysis"] = {"ai_used": False, "reason": "Rejeté par règles"}
        return rule_result
    
    # If rule-based passed, use AI to detect subtle issues
    try:
        from services.ai_moderation_service import ai_moderate_annonce, get_ai_rejection_message
        
        ai_result = await ai_moderate_annonce(title, description, category)
        rule_result["ai_analysis"] = ai_result
        
        # If AI rejected with high confidence
        if not ai_result.get("approved", True) and ai_result.get("confidence", 0) >= 0.7:
            rule_result["approved"] = False
            ai_message = await get_ai_rejection_message(ai_result)
            if ai_message:
                rule_result["rejection_reasons"].append(ai_result.get("reason", "Contenu non approprié"))
            
            # Add category suggestion if available
            if ai_result.get("category_suggestion"):
                rule_result["details"]["ai_suggestion"] = ai_result["category_suggestion"]
        
        logger.info(f"AI moderation: approved={ai_result.get('approved')}, confidence={ai_result.get('confidence')}")
        
    except Exception as e:
        logger.error(f"AI moderation failed: {e}")
        rule_result["ai_analysis"] = {"ai_used": False, "error": str(e)}
    
    return rule_result

