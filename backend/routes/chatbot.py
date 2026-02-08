"""
MyDar Chatbot - Assistant Shopping Intelligent
Avec système avancé de compréhension des requêtes utilisateur
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Set, Tuple
from datetime import datetime, timezone
import os
import uuid
import re
import unicodedata
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')


# ============ SYSTÈME DE NORMALISATION ET COMPRÉHENSION ============

# Dictionnaire de corrections orthographiques et variations communes
SPELLING_CORRECTIONS: Dict[str, str] = {
    # Vidéophonie - variations courantes
    "videophone": "visiophone",
    "vidéophone": "visiophone",
    "viseophone": "visiophone",
    "visophone": "visiophone",
    "videophon": "visiophone",
    "visiophon": "visiophone",
    "vidéophon": "visiophone",
    "interphon": "interphone",
    "interfone": "interphone",
    "portier video": "visiophone",
    "sonnette video": "visiophone",
    "sonnette vidéo": "visiophone",
    
    # Caméras - variations
    "camera": "caméra",
    "camra": "caméra",
    "cam": "caméra",
    "kamera": "caméra",
    "cámera": "caméra",
    "webcam surveillance": "caméra",
    "cam de surveillance": "caméra",
    "cam surveillance": "caméra",
    
    # Enregistreurs
    "enregisteur": "enregistreur",
    "enregitreur": "enregistreur",
    "recorder": "enregistreur",
    "dvr": "enregistreur xvr",
    
    # Alarme
    "alarme": "alarme",
    "alrme": "alarme",
    "allarme": "alarme",
    "systeme alarme": "alarme",
    "système alarme": "alarme",
    "detecteur": "détecteur",
    "détectuer": "détecteur",
    "capteur mouvement": "détecteur mouvement",
    "sensor": "détecteur",
    
    # Interrupteurs
    "interupteur": "interrupteur",
    "interuptuer": "interrupteur",
    "bouton": "interrupteur",
    "switch lumiere": "interrupteur",
    "switch lumière": "interrupteur",
    
    # Motorisation
    "moteur volet": "motorisation volet",
    "volet roulant": "motorisation volet",
    "store banne": "motorisation store",
    "moteur store": "motorisation store",
    "moteur portail": "motorisation portail",
    "porte garage": "motorisation garage",
    "moteur garage": "motorisation garage",
    
    # Contrôle d'accès
    "controle acces": "contrôle accès",
    "controle d'acces": "contrôle accès",
    "pointeuse": "pointeuse",
    "pointage": "pointeuse",
    "badgeuse": "pointeuse",
    "lecteur badge": "contrôle accès badge",
    "lecteur empreinte": "contrôle accès empreinte",
    "biometrique": "empreinte",
    "biométrique": "empreinte",
    
    # Réseau
    "switch reseau": "switch réseau",
    "switch ethernet": "switch réseau",
    "routeur wifi": "routeur",
    "router": "routeur",
    "acces point": "point accès wifi",
    "access point": "point accès wifi",
    "borne wifi": "point accès wifi",
    
    # Marques - corrections
    "dahwa": "dahua",
    "dahoua": "dahua",
    "hikvision": "hikvision",
    "hikvision": "hikvision",
    "somfi": "somfy",
    "zktecho": "zkteco",
    "zktek": "zkteco",
}

# Synonymes métier - expansion de recherche
BUSINESS_SYNONYMS: Dict[str, List[str]] = {
    "visiophone": ["vidéophone", "interphone vidéo", "portier vidéo", "sonnette vidéo", "parlophone vidéo", "interphone"],
    "interphone": ["parlophone", "portier audio", "sonnette", "visiophone"],
    "caméra": ["camera", "cam", "vidéosurveillance", "surveillance", "cctv"],
    "caméra dôme": ["dome", "dôme", "camera dome", "ipc-hdw", "hac-hdw"],
    "caméra bullet": ["bullet", "tube", "camera tube", "ipc-hfw", "hac-hfw"],
    "caméra ptz": ["ptz", "speed dome", "motorisée", "rotative"],
    "enregistreur": ["nvr", "dvr", "xvr", "recorder", "stockage vidéo"],
    "nvr": ["enregistreur ip", "enregistreur réseau", "network video recorder"],
    "alarme": ["système alarme", "anti-intrusion", "sécurité", "protection"],
    "détecteur": ["capteur", "sensor", "détection", "mouvement", "présence"],
    "sirène": ["alarme sonore", "avertisseur", "klaxon"],
    "interrupteur": ["switch", "commutateur", "bouton", "va-et-vient"],
    "prise": ["socket", "plug", "prise électrique", "prise murale"],
    "motorisation": ["moteur", "automatisme", "motorisé"],
    "volet roulant": ["volet", "store", "rideau", "persienne"],
    "portail": ["portail automatique", "portail coulissant", "portail battant"],
    "contrôle accès": ["accès", "badge", "biométrique", "empreinte", "pointeuse"],
    "pointeuse": ["badgeuse", "horodateur", "gestion temps", "présence"],
    "switch réseau": ["commutateur réseau", "switch ethernet", "switch poe"],
    "routeur": ["router", "modem", "box internet"],
    "wifi": ["wi-fi", "wireless", "sans fil"],
}

# Catégories avec leurs mots-clés associés (pour inférence)
CATEGORY_INFERENCE: Dict[str, List[str]] = {
    "Vidéophonie": ["visiophone", "vidéophone", "interphone", "portier", "sonnette", "parlophone"],
    "Vidéosurveillance": ["caméra", "camera", "nvr", "dvr", "enregistreur", "surveillance", "cctv", "bullet", "dome", "ptz"],
    "Alarme": ["alarme", "détecteur", "sirène", "centrale", "capteur", "intrusion", "mouvement"],
    "Contrôle d'Accès": ["accès", "badge", "empreinte", "pointeuse", "biométrique", "lecteur", "rfid"],
    "Motorisation": ["moteur", "volet", "store", "portail", "garage", "somfy", "automatisme"],
    "Interrupteur": ["interrupteur", "bouton", "commutateur", "va-et-vient", "poussoir"],
    "Prise": ["prise", "socket", "plug", "électrique", "usb", "schuko"],
    "Réseau": ["switch réseau", "switch poe", "switch ethernet", "routeur", "wifi", "ethernet", "poe", "réseau", "access point", "ruijie"],
    "Éclairage": ["ampoule", "lampe", "led", "lumière", "éclairage", "spot"],
    "Domotique": ["smart", "connecté", "intelligent", "automatisation", "maison connectée"],
}


def normalize_text(text: str) -> str:
    """Normalise le texte: supprime accents, met en minuscules"""
    text = text.lower().strip()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text


def correct_spelling(text: str) -> Tuple[str, List[str]]:
    """
    Corrige les fautes d'orthographe et retourne le texte corrigé + corrections appliquées.
    Utilise une approche par mot pour éviter les corrections en cascade.
    """
    corrections_applied = []
    words = text.lower().split()
    corrected_words = []
    
    for word in words:
        word_normalized = normalize_text(word)
        corrected = word
        
        # Chercher une correction pour ce mot
        for wrong, correct in SPELLING_CORRECTIONS.items():
            wrong_normalized = normalize_text(wrong)
            # Match exact du mot ou partie significative
            if word_normalized == wrong_normalized or (len(wrong_normalized) > 4 and wrong_normalized in word_normalized):
                if word != correct:
                    corrections_applied.append(f"{word} → {correct}")
                    corrected = correct
                    break
        
        corrected_words.append(corrected)
    
    return ' '.join(corrected_words), corrections_applied


def expand_with_synonyms(keywords: List[str]) -> Set[str]:
    """Étend la liste de mots-clés avec des synonymes métier"""
    expanded = set(keywords)
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        # Chercher dans les synonymes
        for main_term, synonyms in BUSINESS_SYNONYMS.items():
            if keyword_lower == main_term or keyword_lower in synonyms:
                expanded.add(main_term)
                expanded.update(synonyms)
    
    return expanded


def infer_categories(keywords: List[str], full_query: str = "") -> List[Tuple[str, float]]:
    """
    Infère les catégories probables basées sur les mots-clés et la requête complète.
    Retourne une liste de (catégorie, score de confiance)
    """
    category_scores: Dict[str, float] = {}
    query_normalized = normalize_text(full_query) if full_query else ""
    
    # D'abord, vérifier les expressions complètes dans la requête (priorité haute)
    for category, cat_keywords in CATEGORY_INFERENCE.items():
        for cat_kw in cat_keywords:
            cat_kw_normalized = normalize_text(cat_kw)
            # Match dans la requête complète (expressions multi-mots)
            if len(cat_kw.split()) > 1 and cat_kw_normalized in query_normalized:
                category_scores[category] = category_scores.get(category, 0) + 5.0
    
    # Ensuite, analyser les mots-clés individuels
    for keyword in keywords:
        keyword_lower = normalize_text(keyword)
        for category, cat_keywords in CATEGORY_INFERENCE.items():
            for cat_kw in cat_keywords:
                cat_kw_normalized = normalize_text(cat_kw)
                # Match exact
                if keyword_lower == cat_kw_normalized:
                    category_scores[category] = category_scores.get(category, 0) + 2.0
                # Match partiel
                elif cat_kw_normalized in keyword_lower or keyword_lower in cat_kw_normalized:
                    category_scores[category] = category_scores.get(category, 0) + 1.0
    
    # Bonus: combinaisons spécifiques
    if "switch" in query_normalized and ("poe" in query_normalized or "reseau" in query_normalized or "ethernet" in query_normalized):
        category_scores["Réseau"] = category_scores.get("Réseau", 0) + 5.0
    
    # Trier par score décroissant
    sorted_categories = sorted(category_scores.items(), key=lambda x: -x[1])
    return sorted_categories


def extract_keywords(text: str) -> List[str]:
    """Extrait les mots-clés significatifs du texte"""
    # Mots à ignorer (stop words français)
    stop_words = {
        "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
        "un", "une", "des", "le", "la", "les", "de", "du", "au", "aux",
        "et", "ou", "mais", "donc", "car", "ni", "que", "qui", "quoi",
        "ce", "cette", "ces", "mon", "ma", "mes", "ton", "ta", "tes",
        "son", "sa", "ses", "notre", "votre", "leur", "leurs",
        "pour", "avec", "sans", "dans", "sur", "sous", "par", "chez",
        "veux", "voudrais", "cherche", "besoin", "faut", "peux", "peut",
        "avoir", "être", "faire", "voir", "trouver", "acheter",
        "bonjour", "bonsoir", "salut", "merci", "svp", "stp",
        "comment", "combien", "quand", "pourquoi", "quel", "quelle",
        "très", "plus", "moins", "bien", "bon", "bonne", "meilleur"
    }
    
    # Nettoyer et extraire les mots
    words = re.findall(r'\b[a-zA-ZÀ-ÿ0-9]+\b', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords


def analyze_user_query(message: str) -> Dict:
    """
    Analyse complète de la requête utilisateur.
    Retourne un dictionnaire avec toutes les informations extraites.
    """
    result = {
        "original_query": message,
        "corrected_query": "",
        "normalized_query": "",
        "corrections_applied": [],
        "keywords": [],
        "expanded_keywords": [],
        "probable_categories": [],
        "detected_brand": None,
        "detected_price": None,
        "detected_features": [],
        "search_suggestions": [],
        "intent_type": "search"  # search, comparison, installation, info
    }
    
    # 1. Correction orthographique
    corrected, corrections = correct_spelling(message)
    result["corrected_query"] = corrected
    result["corrections_applied"] = corrections
    
    # 2. Normalisation
    result["normalized_query"] = normalize_text(corrected)
    
    # 3. Extraction des mots-clés
    keywords = extract_keywords(corrected)
    result["keywords"] = keywords
    
    # 4. Expansion avec synonymes
    expanded = expand_with_synonyms(keywords)
    result["expanded_keywords"] = list(expanded)
    
    # 5. Inférence de catégories (avec la requête complète pour les expressions)
    all_keywords = list(expanded) + keywords
    categories = infer_categories(all_keywords, corrected)
    result["probable_categories"] = [{"category": cat, "confidence": score} for cat, score in categories[:3]]
    
    # 6. Détection de marque
    for brand in KNOWN_BRANDS:
        if brand in corrected:
            result["detected_brand"] = brand
            break
    
    # 7. Détection de prix/budget
    price_patterns = [
        r"moins de (\d+)", r"max (\d+)", r"budget (\d+)", 
        r"(\d+)\s*dt", r"(\d+)\s*dinars?", r"environ (\d+)"
    ]
    for pattern in price_patterns:
        match = re.search(pattern, corrected)
        if match:
            result["detected_price"] = float(match.group(1))
            break
    
    # 8. Détection de caractéristiques techniques
    features = []
    feature_patterns = {
        "resolution": r"(\d+)\s*mp|(\d+)\s*megapixel|4k|1080p|720p",
        "connectivity": r"wifi|wi-fi|bluetooth|zigbee|ethernet|poe|filaire|sans fil",
        "location": r"extérieur|intérieur|outdoor|indoor|ip67|ip65|étanche",
        "channels": r"(\d+)\s*voies|(\d+)\s*canaux|(\d+)\s*ch",
        "ports": r"(\d+)\s*ports?"
    }
    for feature_type, pattern in feature_patterns.items():
        match = re.search(pattern, corrected, re.IGNORECASE)
        if match:
            features.append({"type": feature_type, "value": match.group(0)})
    result["detected_features"] = features
    
    # 9. Type d'intention
    if any(w in corrected for w in ["comparer", "vs", "ou", "différence", "versus"]):
        result["intent_type"] = "comparison"
    elif any(w in corrected for w in ["installer", "installation", "monter", "pose", "câblage"]):
        result["intent_type"] = "installation"
    elif any(w in corrected for w in ["comment", "qu'est-ce", "c'est quoi", "expliquer"]):
        result["intent_type"] = "info"
    
    # 10. Suggestions de recherche alternatives
    suggestions = set()
    for keyword in keywords[:3]:
        if keyword in BUSINESS_SYNONYMS:
            suggestions.update(BUSINESS_SYNONYMS[keyword][:3])
    for cat_info in result["probable_categories"][:2]:
        cat = cat_info["category"]
        if cat in CATEGORY_INFERENCE:
            suggestions.update(CATEGORY_INFERENCE[cat][:3])
    result["search_suggestions"] = list(suggestions)[:5]
    
    return result


# ============ CONFIGURATION PRODUITS ============

# Mots-clés à EXCLURE (accessoires)
EXCLUDE_KEYWORDS: Set[str] = {
    "support", "câble", "cable", "adaptateur", "alimentation", "fixation",
    "vis", "connecteur", "rallonge", "pile", "batterie", "chargeur",
    "télécommande seule", "bouton seul", "accessoire", "disque", "hdd", "ssd",
    "seagate", "western digital", "wd", "st10", "st8", "st6", "st4", "st2",
    "mounting", "bracket", "power supply"
}

# Configuration des types de produits par catégorie
PRODUCT_TYPE_CONFIG: Dict[str, Dict] = {
    # Vidéosurveillance - Caméras
    "caméra": {
        "category": "Vidéosurveillance",
        "must_contain": ["caméra", "camera", "ipc", "hac", "hdw", "hfw", "bullet", "dome", "ptz", "tourelle", "eyeball"],
        "must_not_contain": ["support", "câble", "nvr", "dvr", "xvr", "disque", "hdd", "seagate", "clavier", "centrale", "carte", "enregistreur"]
    },
    "camera": {
        "category": "Vidéosurveillance",
        "must_contain": ["caméra", "camera", "ipc", "hac", "hdw", "hfw", "bullet", "dome", "ptz", "tourelle", "eyeball"],
        "must_not_contain": ["support", "câble", "nvr", "dvr", "xvr", "disque", "hdd", "seagate", "clavier", "centrale", "carte", "enregistreur"]
    },
    "كاميرا": {
        "category": "Vidéosurveillance",
        "must_contain": ["caméra", "camera", "ipc", "hac", "hdw", "hfw", "bullet", "dome", "ptz"],
        "must_not_contain": ["support", "câble", "nvr", "dvr", "xvr", "disque", "hdd", "clavier", "centrale"]
    },
    "bullet": {
        "category": "Vidéosurveillance",
        "must_contain": ["ipc", "hac", "hfw", "bullet"],
        "must_not_contain": ["nvr", "dvr", "xvr", "disque", "clavier"]
    },
    "dome": {
        "category": "Vidéosurveillance",
        "must_contain": ["ipc", "hac", "hdw", "dome"],
        "must_not_contain": ["nvr", "dvr", "xvr", "disque", "clavier"]
    },
    
    # Vidéosurveillance - Enregistreurs
    "nvr": {
        "category": "Vidéosurveillance",
        "must_contain": ["nvr", "enregistreur", "network video"],
        "must_not_contain": ["support", "câble", "disque", "caméra", "camera"]
    },
    "dvr": {
        "category": "Vidéosurveillance",
        "must_contain": ["dvr", "xvr", "enregistreur"],
        "must_not_contain": ["support", "câble", "disque", "caméra"]
    },
    "enregistreur": {
        "category": "Vidéosurveillance",
        "must_contain": ["nvr", "dvr", "xvr", "enregistreur"],
        "must_not_contain": ["support", "câble", "disque"]
    },
    
    # Alarme
    "alarme": {
        "category": "Alarme",
        "must_contain": ["centrale", "détecteur", "sirène", "capteur", "alarme", "inim", "zone"],
        "must_not_contain": ["pile", "câble", "support", "caméra"]
    },
    "détecteur": {
        "category": "Alarme",
        "must_contain": ["détecteur", "capteur", "pir", "mouvement", "ouverture"],
        "must_not_contain": ["pile", "câble", "support"]
    },
    "sirène": {
        "category": "Alarme", 
        "must_contain": ["sirène", "alarme sonore"],
        "must_not_contain": ["pile", "câble"]
    },
    
    # Interrupteurs
    "interrupteur": {
        "category": "Interrupteur",
        "must_contain": ["interrupteur", "switch", "bouton", "commande", "va-et-vient", "poussoir"],
        "must_not_contain": ["plaque", "cadre", "enjoliveur", "prise"]
    },
    "switch": {
        "category": "Interrupteur",
        "must_contain": ["interrupteur", "switch", "bouton", "commande"],
        "must_not_contain": ["plaque", "cadre", "enjoliveur", "réseau", "network"]
    },
    
    # Prises
    "prise": {
        "category": "Prise",
        "must_contain": ["prise", "socket", "plug", "schuko", "2p+t"],
        "must_not_contain": ["plaque", "cadre", "interrupteur"]
    },
    
    # Motorisation
    "motorisation": {
        "category": "Motorisation",
        "must_contain": ["moteur", "motor", "volet", "store", "portail", "garage", "somfy", "tubulaire"],
        "must_not_contain": ["télécommande seule", "support", "câble"]
    },
    "volet": {
        "category": "Motorisation",
        "must_contain": ["volet", "moteur", "tubulaire", "somfy", "store"],
        "must_not_contain": ["télécommande seule", "support"]
    },
    "store": {
        "category": "Motorisation",
        "must_contain": ["store", "moteur", "bras", "somfy"],
        "must_not_contain": ["télécommande seule", "support"]
    },
    "portail": {
        "category": "Motorisation",
        "must_contain": ["portail", "coulissant", "battant", "moteur", "automatisme"],
        "must_not_contain": ["télécommande seule"]
    },
    "garage": {
        "category": "Motorisation",
        "must_contain": ["garage", "porte", "moteur", "dexxo", "gdk"],
        "must_not_contain": ["télécommande seule"]
    },
    
    # Vidéophonie
    "visiophone": {
        "category": "Vidéophonie",
        "must_contain": ["visiophone", "vidéophone", "interphone", "portier", "vidéo", "moniteur", "class", "akuvox", "hikvision"],
        "must_not_contain": ["support", "câble"]
    },
    "vidéophone": {
        "category": "Vidéophonie",
        "must_contain": ["visiophone", "vidéophone", "interphone", "portier", "kit", "class", "akuvox"],
        "must_not_contain": ["support", "câble"]
    },
    "videophone": {
        "category": "Vidéophonie",
        "must_contain": ["visiophone", "vidéophone", "interphone", "portier", "kit", "class", "akuvox"],
        "must_not_contain": ["support", "câble"]
    },
    "interphone": {
        "category": "Vidéophonie",
        "must_contain": ["interphone", "portier", "audio", "parlophone", "visiophone", "vidéophone"],
        "must_not_contain": ["support", "câble"]
    },
    
    # Contrôle d'accès
    "contrôle d'accès": {
        "category": "Contrôle d'Accès",
        "must_contain": ["lecteur", "badge", "empreinte", "clavier", "accès", "zkteco", "sf"],
        "must_not_contain": ["support"]
    },
    "badge": {
        "category": "Contrôle d'Accès",
        "must_contain": ["lecteur", "badge", "rfid", "mifare", "proximity"],
        "must_not_contain": ["support"]
    },
    "pointeuse": {
        "category": "Contrôle d'Accès",
        "must_contain": ["pointeuse", "temps", "présence", "empreinte", "zkteco"],
        "must_not_contain": []
    },
    
    # Réseau
    "réseau": {
        "category": "Réseau",
        "must_contain": ["switch", "routeur", "access point", "wifi", "poe", "ruijie"],
        "must_not_contain": ["interrupteur"]
    },
    "switch réseau": {
        "category": "Réseau",
        "must_contain": ["switch", "poe", "port", "gigabit", "ruijie", "omada", "tp-link"],
        "must_not_contain": ["interrupteur", "bouton", "declutch", "somfy"]
    },
    "switch poe": {
        "category": "Réseau",
        "must_contain": ["switch", "poe", "port", "gigabit", "ruijie", "omada", "tp-link", "dahua"],
        "must_not_contain": ["interrupteur", "bouton", "declutch", "somfy"]
    },
    "switch ethernet": {
        "category": "Réseau",
        "must_contain": ["switch", "poe", "port", "gigabit", "ruijie", "omada", "tp-link", "ethernet"],
        "must_not_contain": ["interrupteur", "bouton", "declutch", "somfy"]
    },
    "routeur": {
        "category": "Réseau",
        "must_contain": ["routeur", "router", "wifi", "4g", "lte", "access point"],
        "must_not_contain": []
    },
    
    # Télécommandes
    "télécommande": {
        "category": "Motorisation",
        "must_contain": ["télécommande", "remote", "keygo", "situo", "smoove"],
        "must_not_contain": []
    }
}

# Mapping catégorie keywords vers catégorie DB
CATEGORY_KEYWORDS: Dict[str, str] = {
    "caméra": "Vidéosurveillance", "camera": "Vidéosurveillance", "كاميرا": "Vidéosurveillance",
    "surveillance": "Vidéosurveillance", "nvr": "Vidéosurveillance", "dvr": "Vidéosurveillance",
    "enregistreur": "Vidéosurveillance",
    "alarme": "Alarme", "détecteur": "Alarme", "sirène": "Alarme", "انذار": "Alarme",
    "interrupteur": "Interrupteur", "bouton": "Interrupteur",
    "prise": "Prise", "plug": "Prise", "socket": "Prise",
    "volet": "Motorisation", "store": "Motorisation", "rideau": "Motorisation", 
    "moteur": "Motorisation", "portail": "Motorisation", "garage": "Motorisation",
    "motorisation": "Motorisation", "somfy": "Motorisation",
    "ampoule": "Éclairage", "lampe": "Éclairage", "led": "Éclairage", "lumière": "Éclairage",
    "visiophone": "Vidéophonie", "vidéophone": "Vidéophonie", "videophone": "Vidéophonie",
    "interphone": "Vidéophonie", "parlophone": "Vidéophonie", "portier": "Vidéophonie",
    "contrôle d'accès": "Contrôle d'Accès", "badge": "Contrôle d'Accès", "lecteur": "Contrôle d'Accès",
    "pointeuse": "Contrôle d'Accès", "empreinte": "Contrôle d'Accès",
    "réseau": "Réseau", "routeur": "Réseau", "wifi": "Réseau", "switch réseau": "Réseau",
    "switch poe": "Réseau", "switch ethernet": "Réseau",
    "plaque": "Plaque", "cadre": "Plaque",
    "télécommande": "Motorisation"
}

# Marques connues
KNOWN_BRANDS: List[str] = [
    "dahua", "somfy", "zkteco", "hikvision", "somef", "inim", 
    "ruijie", "schutz", "tuya", "sonoff", "legrand", "schneider"
]

# Technologies connues
KNOWN_TECHNOLOGIES: Dict[str, str] = {
    "wifi": "WiFi", "wi-fi": "WiFi", "wireless": "WiFi",
    "zigbee": "Zigbee",
    "bluetooth": "Bluetooth", "ble": "Bluetooth",
    "rts": "RTS",
    "io": "IO", "io-homecontrol": "IO",
    "poe": "PoE", "power over ethernet": "PoE",
    "rf": "RF 433MHz", "433": "RF 433MHz",
    "filaire": "Filaire", "wired": "Filaire"
}

# Patterns de modèles de produits pour le matching
MODEL_PATTERNS: List[str] = [
    r'ipc-[a-z0-9\-]+',
    r'hac-[a-z0-9\-]+',
    r'hdw-[a-z0-9\-]+',
    r'hfw-[a-z0-9\-]+',
    r'nvr[a-z0-9\-]*',
    r'xvr[a-z0-9\-]*',
    r'dvr[a-z0-9\-]*',
    r'dhi-[a-z0-9\-]+',
    r'dh-[a-z0-9\-]+',
    r'sf[0-9]+',
    r'zk-[a-z0-9]+',
]


# ============ FONCTIONS DE RECHERCHE ============

async def search_products_smart(query: str, filters: Dict = None) -> Tuple[List[Dict], Dict]:
    """
    Recherche intelligente de produits - v2 Gemini2 schema.
    Utilise les nouveaux champs: search.keywords, ai.summary, ranking.quality_score
    """
    metadata = {
        "search_method": "strict",
        "alternatives_used": False,
        "expanded_search": False,
        "suggestions": []
    }
    
    try:
        # v2 schema: use image_missing instead of checking image field
        base_query = {"active": True, "image_missing": False}
        
        # Utiliser la requête directement
        search_query = query.lower()
        
        # Détecter le type de produit avec le système amélioré
        detected_config = None
        sorted_keywords = sorted(PRODUCT_TYPE_CONFIG.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword in search_query:
                detected_config = PRODUCT_TYPE_CONFIG[keyword]
                break
        
        # v2: utiliser category_path_ids pour recherche hiérarchique
        if detected_config:
            # Map old category names to new category IDs
            category_mapping = {
                "Vidéosurveillance": "videosurveillance",
                "Vidéophonie": "videophonie",
                "Alarme": "alarme",
                "Contrôle d'Accès": "controle-d-accès",
                "Motorisation": "motorisation",
                "Interrupteur": "interrupteur",
                "Prise": "prise",
                "Réseau": "reseau",
                "Éclairage": "eclairage",
                "Domotique": "domotique"
            }
            old_cat = detected_config["category"]
            new_cat_id = category_mapping.get(old_cat, old_cat.lower().replace(" ", "-").replace("'", "-"))
            base_query["category_path_ids"] = new_cat_id
        elif filters and filters.get("category"):
            # Utiliser la catégorie des filtres si disponible
            category_mapping = {
                "Vidéosurveillance": "videosurveillance",
                "Vidéophonie": "videophonie",
                "Alarme": "alarme",
                "Contrôle d'Accès": "controle-d-accès",
                "Motorisation": "motorisation",
                "Interrupteur": "interrupteur",
                "Prise": "prise",
                "Réseau": "reseau",
                "Éclairage": "eclairage",
                "Domotique": "domotique"
            }
            cat = filters["category"]
            new_cat_id = category_mapping.get(cat, cat.lower().replace(" ", "-").replace("'", "-"))
            base_query["category_path_ids"] = new_cat_id
        
        # Appliquer les filtres additionnels
        if filters:
            if filters.get("brand"):
                base_query["brand"] = {"$regex": filters["brand"], "$options": "i"}
            if filters.get("technology"):
                tech = filters["technology"]
                # v2: search in attributes_norm.technologies
                base_query["$or"] = [
                    {"attributes_norm.technologies": {"$regex": tech, "$options": "i"}},
                    {"name": {"$regex": tech, "$options": "i"}},
                    {"search.keywords": {"$regex": tech, "$options": "i"}}
                ]
            if filters.get("max_price"):
                base_query["price"] = {"$lte": filters["max_price"]}
            if filters.get("connectivity"):
                # Map WiFi to "Sans fil"
                conn_map = {"wifi": "Sans fil", "filaire": "Filaire", "hybride": "Hybride"}
                conn_value = conn_map.get(filters["connectivity"].lower(), filters["connectivity"])
                base_query["attributes_norm.connectivity"] = conn_value
        
        # v2: Sort by quality_score for better results
        products = await db.products.find(
            base_query, {"_id": 0}
        ).sort([("ranking.quality_score", -1), ("featured", -1)]).limit(50).to_list(50)
        
        # Filtrage post-recherche
        filtered = []
        for product in products:
            if _is_product_valid(product, detected_config):
                filtered.append(product)
                if len(filtered) >= 10:
                    break
        
        # Si pas de résultats, tenter une recherche élargie avec synonymes
        if len(filtered) == 0 and analysis and analysis.get("expanded_keywords"):
            metadata["search_method"] = "expanded"
            metadata["expanded_search"] = True
            
            # Construire une recherche OR sur les mots-clés étendus (v2: use search.keywords)
            expanded_keywords = analysis["expanded_keywords"][:5]
            or_conditions = []
            for kw in expanded_keywords:
                or_conditions.append({"name": {"$regex": kw, "$options": "i"}})
                or_conditions.append({"search.keywords": {"$regex": kw, "$options": "i"}})
            
            expanded_query = {
                "active": True,
                "image_missing": False,
                "$or": or_conditions
            }
            
            # Garder le filtre de catégorie si disponible
            if base_query.get("category_path_ids"):
                expanded_query["category_path_ids"] = base_query["category_path_ids"]
            
            # Garder le filtre de connectivité si disponible
            if base_query.get("attributes_norm.connectivity"):
                expanded_query["attributes_norm.connectivity"] = base_query["attributes_norm.connectivity"]
            
            products = await db.products.find(
                expanded_query, {"_id": 0}
            ).sort([("ranking.quality_score", -1)]).limit(30).to_list(30)
            
            # Filtrage moins strict pour la recherche élargie
            for product in products:
                if not any(kw in product.get("name", "").lower() for kw in EXCLUDE_KEYWORDS):
                    filtered.append(product)
                    if len(filtered) >= 10:
                        break
        
        # Si toujours pas de résultats, proposer des alternatives
        if len(filtered) == 0:
            metadata["alternatives_used"] = True
            if analysis and analysis.get("probable_categories"):
                for cat_info in analysis["probable_categories"][:2]:
                    cat_id = cat_info["category"].lower().replace(" ", "-").replace("'", "-")
                    alt_products = await db.products.find(
                        {"category_path_ids": cat_id, "active": True, "image_missing": False},
                        {"_id": 0}
                    ).sort([("ranking.quality_score", -1)]).limit(5).to_list(5)
                    for p in alt_products:
                        if p not in filtered:
                            filtered.append(p)
                    if len(filtered) >= 5:
                        break
                metadata["suggestions"] = [f"Produits similaires de la catégorie {cat_info['category']}" 
                                           for cat_info in analysis["probable_categories"][:2]]
        
        print(f"[Search] Query: '{query[:30]}', Method: {metadata['search_method']}, Results: {len(filtered)}")
        return filtered, metadata
        
    except Exception as e:
        print(f"[Search Error] {e}")
        return [], metadata


async def search_products_strict(query: str, filters: Dict = None) -> List[Dict]:
    """
    Recherche de produits avec filtrage STRICT (legacy).
    Wrapper autour de search_products_smart pour compatibilité.
    """
    products, _ = await search_products_smart(query, filters)
    return products


def _is_product_valid(product: Dict, config: Dict = None) -> bool:
    """Vérifie si un produit est valide (pas un accessoire et correspond aux critères)"""
    name = product.get("name", "").lower()
    desc = product.get("description", "").lower()
    combined = f"{name} {desc}"
    
    # Exclure les accessoires - SEULEMENT basé sur le NOM (pas la description)
    # Car les descriptions contiennent souvent des mots techniques comme "alimentation", "vis"
    if any(kw in name for kw in EXCLUDE_KEYWORDS):
        return False
    
    # Si pas de config spécifique, accepter le produit
    if not config:
        return True
    
    # Vérifier les mots-clés obligatoires (sur le nom + description)
    has_required = any(kw in combined for kw in config.get("must_contain", []))
    # Vérifier les exclusions spécifiques (SEULEMENT sur le nom)
    has_excluded = any(kw in name for kw in config.get("must_not_contain", []))
    
    return has_required and not has_excluded


async def get_categories_summary() -> Dict[str, int]:
    """Récupère le résumé des catégories avec comptages"""
    try:
        pipeline = [
            {"$match": {"image": {"$exists": True, "$ne": None, "$ne": ""}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = await db.products.aggregate(pipeline).to_list(50)
        return {r["_id"]: r["count"] for r in result if r["_id"]}
    except Exception:
        return {}


async def get_brands_summary() -> Dict[str, int]:
    """Récupère le résumé des marques avec comptages"""
    try:
        pipeline = [
            {"$match": {"image": {"$exists": True, "$ne": None, "$ne": ""}}},
            {"$group": {"_id": "$brand", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = await db.products.aggregate(pipeline).to_list(50)
        return {r["_id"]: r["count"] for r in result if r["_id"]}
    except Exception:
        return {}


# ============ EXTRACTION D'INTENTION ============

def extract_search_intent(message: str) -> Dict:
    """Extrait l'intention de recherche du message utilisateur"""
    msg_lower = message.lower()
    
    intent = {
        "query": message,
        "category": None,
        "brand": None,
        "technology": None,
        "connectivity": None,
        "max_price": None,
        "is_comparison": False,
        "is_installation": False
    }
    
    # Détecter la connectivité
    wifi_keywords = ["wifi", "wi-fi", "sans fil", "ويفي", "واي فاي", "بلا خيط"]
    filaire_keywords = ["filaire", "câble", "ethernet", "poe", "بالخيط", "سلكي"]
    
    if any(kw in msg_lower for kw in wifi_keywords):
        intent["connectivity"] = "wifi"
    elif any(kw in msg_lower for kw in filaire_keywords):
        intent["connectivity"] = "filaire"
    
    # Détecter la catégorie - Trier par longueur décroissante pour priorité aux termes spécifiques
    sorted_cat_keywords = sorted(CATEGORY_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_cat_keywords:
        if keyword in msg_lower:
            intent["category"] = CATEGORY_KEYWORDS[keyword]
            break
    
    # Détecter la marque
    for brand in KNOWN_BRANDS:
        if brand in msg_lower:
            intent["brand"] = brand
            break
    
    # Détecter la technologie - Utiliser word boundaries pour éviter les faux positifs
    # (ex: "io" dans "visiophone" ne doit pas matcher)
    for tech_key, tech_value in KNOWN_TECHNOLOGIES.items():
        # Créer un pattern avec word boundaries
        pattern = r'\b' + re.escape(tech_key) + r'\b'
        if re.search(pattern, msg_lower):
            intent["technology"] = tech_value
            break
    
    # Détecter le budget
    price_patterns = [r"moins de (\d+)", r"max (\d+)", r"budget (\d+)", r"(\d+)\s*dt"]
    for pattern in price_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            intent["max_price"] = float(match.group(1))
            break
    
    # Détecter les intentions spéciales
    intent["is_comparison"] = any(kw in msg_lower for kw in ["comparer", "vs", "ou", "différence", "مقارنة"])
    intent["is_installation"] = any(kw in msg_lower for kw in ["installer", "installation", "monter", "تركيب"])
    
    return intent


# ============ HISTORIQUE ============

async def get_chat_history(session_id: str, limit: int = 10) -> List[Dict]:
    """Récupère l'historique de chat pour une session"""
    try:
        messages = await db.chat_history.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        messages.reverse()
        return messages
    except Exception:
        return []


async def save_chat_message(session_id: str, role: str, content: str):
    """Sauvegarde un message dans l'historique"""
    try:
        await db.chat_history.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc)
        })
    except Exception as e:
        print(f"[Save Error] {e}")


# ============ MATCHING PRODUITS ============

def extract_products_from_response(response: str, search_results: List[Dict]) -> List[Dict]:
    """
    Extrait les produits mentionnés dans la réponse de l'IA.
    Retourne UNIQUEMENT les produits explicitement nommés.
    """
    if not search_results:
        return []
    
    response_lower = response.lower()
    
    # Vérifier si la réponse contient des recommandations (pas juste des questions)
    is_question_only = all(ind in response for ind in ["1)", "2)"]) and "—" not in response
    has_products = "**" in response and "—" in response
    
    if is_question_only or not has_products:
        return []
    
    # Extraire les modèles mentionnés
    mentioned_models = set()
    for pattern in MODEL_PATTERNS:
        matches = re.findall(pattern, response_lower)
        mentioned_models.update(matches)
    
    # Matcher avec les résultats de recherche
    matched_products = []
    for product in search_results:
        name_lower = product.get("name", "").lower()
        
        # Vérifier si le modèle est mentionné
        is_mentioned = False
        
        # Méthode 1: Match par modèle
        for model in mentioned_models:
            model_clean = model.replace("-", "")
            name_clean = name_lower.replace("-", "").replace(" ", "")
            if model_clean in name_clean:
                is_mentioned = True
                break
        
        # Méthode 2: Match par nom (premiers mots)
        if not is_mentioned:
            name_parts = name_lower.split()[:2]
            for part in name_parts:
                if len(part) > 4 and part in response_lower:
                    is_mentioned = True
                    break
        
        if is_mentioned:
            matched_products.append({
                "id": product.get("id"),
                "name": product.get("name"),
                "price": product.get("price"),
                "category": product.get("category"),
                "brand": product.get("brand"),
                "image": product.get("image"),
                "technology": product.get("technology"),
                "youtube_url": product.get("youtube_url")
            })
            
            if len(matched_products) >= 5:
                break
    
    return matched_products


# ============ SYSTEM PROMPT ============

SYSTEM_PROMPT = """Tu es un assistant e-commerce. Tu aides l'utilisateur à choisir des produits et à comprendre leurs caractéristiques en t'appuyant EXCLUSIVEMENT sur le catalogue produits.

🌍 LANGUE OBLIGATOIRE: 
- Si le client écrit en arabe tunisien (عسلامة، شنوة، نحب، فمّا، أعطيني) → Réponds UNIQUEMENT en arabe tunisien
- Si le client écrit en français → Réponds en français
- GARDE TOUJOURS la même langue que le dernier message du client, même s'il répond par un numéro

========================
MODE EXPLICATION PRODUIT
========================
Si le client demande des informations sur un produit spécifique (ex: "نحب أكثر معلومات", "explique-moi ce produit", "c'est quoi ce produit"):

1) Si le PRODUIT EST FOURNI dans le contexte (PRODUIT_CONTEXTE ci-dessous), utilise ces informations pour:
   - Présenter le produit avec ses caractéristiques principales
   - Expliquer à quoi il sert et ses avantages
   - Mentionner les spécifications techniques importantes
   - Puis demander: "عندك سؤال معين على المنتج هذا؟" / "As-tu une question spécifique sur ce produit?"

2) Si AUCUN produit n'est fourni, demande au client:
   - "أعطيني اسم المنتج ولا الكود متاعو باش نعاونك" / "Donne-moi le nom du produit ou son code pour que je puisse t'aider"

3) Quand le client pose une question sur le produit:
   - Réponds de manière claire et concise
   - Utilise les spécifications du produit pour répondre
   - Si tu ne connais pas la réponse, dis-le honnêtement

========================
MODE RECHERCHE PRODUIT
========================
1) Si le message du client contient DÉJÀ les critères (ex: "كاميرا خارجية wifi" ou "caméra extérieure wifi"), 
   PROPOSE DIRECTEMENT DES PRODUITS sans poser de questions supplémentaires.

2) Sinon, pose UNE SEULE question à la fois pour clarifier:
   - Type de produit si pas clair
   - Environnement (intérieur/extérieur) si pertinent et pas mentionné
   - Connectivité (WiFi/filaire) si pertinent et pas mentionné

3) Format des questions avec numéros:
   1) option1
   2) option2
   0) معنديش تفضيل (ou "Pas de préférence" en français)
   
   Termine par: "جاوبني بالرقم ولا اكتب شي آخر كيف تحب." (ou "Réponds par le numéro ou écris autre chose si tu préfères.")

4) MÉMOIRE: Regarde l'historique - NE REPOSE JAMAIS une question déjà répondue!

5) Catalogue uniquement: Ne propose QUE des produits du catalogue fourni.

========================
FORMAT DES RECOMMANDATIONS
========================
Pour chaque produit:

**[Nom]** — [Marque]
• [Point clé 1]
• [Point clé 2]
{{PRODUCT_ACTIONS:product_id}}

IMPORTANT: Utilise {{PRODUCT_ACTIONS:ID_DU_PRODUIT}} pour générer les boutons.

Après les produits, propose:
1) قارن بين المنتجات / Comparer
2) شوف منتجات مكملة / Produits complémentaires
0) معنديش تفضيل / Pas de préférence

========================
APRÈS LES RECOMMANDATIONS
========================
Propose ces options DANS LA MÊME LANGUE que ta réponse:

Si français:
1) Comparer les produits
2) Voir produits complémentaires  
0) Pas de préférence

Réponds par le numéro ou écris autre chose si tu préfères.

Si arabe tunisien:
1) قارن بين المنتجات
2) شوف منتجات مكملة
0) معنديش تفضيل

جاوبني بالرقم ولا اكتب شي آخر كيف تحب.

========================
📦 CATALOGUE: {catalog_summary}

🔍 PRODUITS DISPONIBLES (UTILISE CES PRODUITS):
{search_results}

📜 HISTORIQUE: 
{history}
========================

💬 SUPPORT: Livraison Tunisie 2-5j, 7 DT (gratuit >250 DT), Paiement à la livraison, Garantie 1 an"""


# ============ MODÈLES ============

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    cart_product_ids: Optional[List[str]] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    products_mentioned: List[dict] = []


# ============ ENDPOINT PRINCIPAL ============

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal du chatbot avec analyse intelligente des requêtes"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Récupérer l'historique
        history = await get_chat_history(session_id)
        
        # 1. ANALYSE INTELLIGENTE DE LA REQUÊTE
        query_analysis = analyze_user_query(request.message)
        
        # Log des corrections appliquées
        if query_analysis["corrections_applied"]:
            print(f"[Query Analysis] Corrections: {query_analysis['corrections_applied']}")
        
        # Extraire l'intention (legacy + nouveau système)
        intent = extract_search_intent(query_analysis["corrected_query"])
        
        # Enrichir avec l'analyse avancée
        if not intent["category"] and query_analysis["probable_categories"]:
            intent["category"] = query_analysis["probable_categories"][0]["category"]
        if not intent["brand"] and query_analysis["detected_brand"]:
            intent["brand"] = query_analysis["detected_brand"]
        if not intent["max_price"] and query_analysis["detected_price"]:
            intent["max_price"] = query_analysis["detected_price"]
        
        # Si réponse numérique, hériter du contexte précédent
        if request.message.strip() in [str(i) for i in range(1, 11)]:
            for msg in reversed(history):
                if msg.get("role") == "user":
                    prev_analysis = analyze_user_query(msg.get("content", ""))
                    prev_intent = extract_search_intent(prev_analysis["corrected_query"])
                    if prev_intent.get("category"):
                        intent["category"] = prev_intent["category"]
                    if prev_intent.get("brand"):
                        intent["brand"] = prev_intent["brand"]
                    break
        
        # Construire les filtres
        filters = {}
        if intent["category"]:
            filters["category"] = intent["category"]
        if intent["brand"]:
            filters["brand"] = intent["brand"]
        if intent["technology"]:
            filters["technology"] = intent["technology"]
        if intent["connectivity"]:
            filters["connectivity"] = intent["connectivity"]
        if intent["max_price"]:
            filters["max_price"] = intent["max_price"]
        
        # 2. RECHERCHE INTELLIGENTE avec le nouveau système
        search_results, search_metadata = await search_products_smart(
            query_analysis["corrected_query"], 
            filters if filters else None
        )
        
        # 3. FORMATER LES RÉSULTATS POUR L'IA
        if search_results:
            formatted_results = []
            for p in search_results[:10]:
                price = p.get('price')
                price_str = f"{price:.3f} DT" if price else "Prix sur demande"
                desc = (p.get('description') or '')[:80]
                formatted_results.append(
                    f"• **{p.get('name')}** — {price_str} — {p.get('brand', 'N/A')}\n"
                    f"  ID: {p.get('id')} | {desc}"
                )
            results_text = "\n".join(formatted_results)
            
            # Ajouter info si recherche élargie
            if search_metadata.get("expanded_search"):
                results_text = "🔍 Recherche élargie avec synonymes:\n" + results_text
            elif search_metadata.get("alternatives_used"):
                results_text = "💡 Alternatives suggérées:\n" + results_text
        else:
            # Pas de résultats - proposer des suggestions
            suggestions = query_analysis.get("search_suggestions", [])
            criteria = [f"{k}: {v}" for k, v in filters.items() if v]
            results_text = f"⚠️ AUCUN PRODUIT trouvé"
            if criteria:
                results_text += f" pour: {', '.join(criteria)}"
            if suggestions:
                results_text += f"\n💡 Suggestions: essayez '{', '.join(suggestions[:3])}'"
            results_text += "\nPropose des alternatives ou demande plus de détails au client."
        
        # Récupérer le résumé du catalogue
        categories = await get_categories_summary()
        brands = await get_brands_summary()
        
        catalog_summary = f"Catégories: {', '.join(list(categories.keys())[:10])}\nMarques: {', '.join(list(brands.keys())[:10])}"
        
        # Formater l'historique avec plus de contexte - IMPORTANT pour éviter répétitions
        history_entries = []
        detected_lang = "fr"  # Default
        criteria_collected = []  # Track des critères déjà collectés
        
        for m in history[-10:]:  # Plus d'historique pour mieux suivre la conversation
            role = 'Client' if m.get('role') == 'user' else 'Assistant'
            content = m.get('content', '')[:250]  # Plus de contenu
            history_entries.append(f"{role}: {content}")
            
            # Détecter la langue du dernier message utilisateur NON-NUMÉRIQUE
            if m.get('role') == 'user':
                content_stripped = content.strip()
                # Ne pas changer la langue si c'est juste un numéro
                if content_stripped not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', content))
                    if arabic_chars > 2:
                        detected_lang = "ar"
                    elif len(content) > 3:  # Ignorer les réponses très courtes
                        detected_lang = "fr"
            
            # Détecter les critères déjà répondus dans les réponses de l'assistant
            if m.get('role') == 'assistant':
                content_lower = content.lower()
                if any(x in content_lower for x in ['intérieur', 'extérieur', 'داخل', 'برا', 'خارج']):
                    if 'environnement' not in criteria_collected:
                        criteria_collected.append('environnement')
                if any(x in content_lower for x in ['wifi', 'filaire', 'ويفي', 'سلكي', 'خيط']):
                    if 'connectivité' not in criteria_collected:
                        criteria_collected.append('connectivité')
        
        history_text = "\n".join(history_entries) or "Nouvelle conversation"
        
        # Détection de langue sur le MESSAGE ACTUEL (priorité sur l'historique)
        current_msg = request.message.strip()
        arabic_chars_current = len(re.findall(r'[\u0600-\u06FF]', current_msg))
        
        # Si le message actuel contient de l'arabe, c'est arabe
        if arabic_chars_current > 2:
            detected_lang = "ar"
        # Si le message actuel est en français (pas de caractères arabes et assez long)
        elif len(current_msg) > 5 and arabic_chars_current == 0:
            detected_lang = "fr"
        # Sinon garder la langue détectée de l'historique
        
        # Ajouter indication de langue et critères collectés
        extra_instructions = ""
        if detected_lang == "ar":
            extra_instructions += "\n⚠️ LANGUE: Arabe tunisien - Réponds UNIQUEMENT en arabe tunisien!"
        else:
            extra_instructions += "\n⚠️ LANGUE: Français - Réponds UNIQUEMENT en français!"
        
        if criteria_collected:
            extra_instructions += f"\n✅ CRITÈRES DÉJÀ COLLECTÉS: {', '.join(criteria_collected)} - NE REPOSE PAS ces questions!"
        
        # Construire le prompt
        full_prompt = SYSTEM_PROMPT.format(
            catalog_summary=catalog_summary,
            search_results=results_text,
            history=history_text + extra_instructions
        )
        
        # Appeler l'IA
        chat_instance = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"mydar-{session_id}",
            system_message=full_prompt
        ).with_model("gemini", "gemini-2.0-flash")
        
        response_text = await chat_instance.send_message(UserMessage(text=request.message))
        
        # Traiter les balises d'action produit {{PRODUCT_ACTIONS:product_id}} ou {PRODUCT_ACTIONS:id}
        action_pattern = r'\{+PRODUCT_ACTIONS:([a-zA-Z0-9\-]+)\}+'
        
        def replace_action(match):
            product_id = match.group(1)
            # Générer les boutons en format markdown avec liens
            return f'\n🔍 [Voir détails](/produit/{product_id}) | 🛒 [Ajouter au panier](ADD_TO_CART:{product_id})\n'
        
        response_text = re.sub(action_pattern, replace_action, response_text)
        
        # Sauvegarder les messages
        await save_chat_message(session_id, "user", request.message)
        await save_chat_message(session_id, "assistant", response_text)
        
        # Extraire les produits mentionnés
        products_mentioned = extract_products_from_response(response_text, search_results)
        
        print(f"[Chat] Session: {session_id[:8]}, Products: {len(products_mentioned)}")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            products_mentioned=products_mentioned
        )
        
    except Exception as e:
        print(f"[Chat Error] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============ ENDPOINTS ADDITIONNELS ============

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Récupère l'historique d'une session"""
    history = await get_chat_history(session_id, limit=50)
    return {
        "session_id": session_id,
        "messages": [
            {"role": m.get("role"), "content": m.get("content"), 
             "timestamp": m.get("timestamp").isoformat() if m.get("timestamp") else None}
            for m in history
        ]
    }


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Efface l'historique d'une session"""
    result = await db.chat_history.delete_many({"session_id": session_id})
    return {"deleted": result.deleted_count}


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
    
    return {
        "total_conversations": len(sessions),
        "total_messages": len(messages),
        "avg_messages_per_conv": round(len(messages) / max(len(sessions), 1), 1)
    }


@router.get("/admin/conversations")
async def get_conversations(range: str = "7d", limit: int = 50):
    """Get chatbot conversations for admin"""
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    date_filters = {"1d": 1, "7d": 7, "30d": 30, "all": 365}
    days = date_filters.get(range, 7)
    date_filter = now - timedelta(days=days)
    
    # Aggregate conversations
    pipeline = [
        {"$match": {"timestamp": {"$gte": date_filter}}},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$session_id",
            "message_count": {"$sum": 1},
            "last_activity": {"$first": "$timestamp"},
            "first_message": {"$last": "$content"},
            "last_message": {"$first": "$content"},
            "messages": {"$push": {"role": "$role", "content": "$content", "timestamp": "$timestamp"}}
        }},
        {"$sort": {"last_activity": -1}},
        {"$limit": limit}
    ]
    
    conversations_raw = await db.chat_history.aggregate(pipeline).to_list(limit)
    
    conversations = []
    for conv in conversations_raw:
        # Detect language from messages
        all_text = " ".join([m.get("content", "") for m in conv.get("messages", [])])
        arabic_pattern = r'[\u0600-\u06FF]'
        import re
        has_arabic = bool(re.search(arabic_pattern, all_text))
        language = "AR 🇹🇳" if has_arabic else "FR 🇫🇷"
        
        conversations.append({
            "session_id": conv["_id"],
            "message_count": conv["message_count"],
            "last_activity": conv["last_activity"].isoformat() if conv.get("last_activity") else None,
            "first_message": conv.get("first_message", "")[:100],
            "last_message": conv.get("last_message", "")[:100],
            "language": language
        })
    
    return {"conversations": conversations, "total": len(conversations)}
async def analyze_query(message: str):
    """
    Analyse une requête utilisateur sans effectuer de recherche.
    Utile pour debugger et comprendre comment le système interprète les requêtes.
    """
    analysis = analyze_user_query(message)
    return {
        "input": message,
        "analysis": analysis,
        "interpretation": {
            "corrected": analysis["corrected_query"],
            "normalized": analysis["normalized_query"],
            "corrections": analysis["corrections_applied"],
            "keywords": analysis["keywords"],
            "synonyms_added": list(set(analysis["expanded_keywords"]) - set(analysis["keywords"])),
            "categories": analysis["probable_categories"],
            "brand": analysis["detected_brand"],
            "price": analysis["detected_price"],
            "features": analysis["detected_features"],
            "intent": analysis["intent_type"],
            "suggestions": analysis["search_suggestions"]
        }
    }
