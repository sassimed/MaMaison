"""
Product Data Enrichment Service
Analyzes and enriches product data with proper categories, brands, and technologies
"""
import asyncio
import re
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# =============================================================================
# MASTER CATEGORY TAXONOMY
# =============================================================================
MASTER_CATEGORIES = {
    # Sécurité
    "Vidéosurveillance": {
        "keywords": ["caméra", "camera", "nvr", "dvr", "enregistreur", "surveillance", "hdcvi", "ptz", "dome", "bullet", "ip cam"],
        "subcategories": ["Caméra IP", "Caméra HDCVI", "Caméra PTZ", "NVR/DVR", "Accessoires Vidéo"]
    },
    "Alarme": {
        "keywords": ["alarme", "détecteur", "sirène", "centrale", "intrusion", "mouvement", "pir", "contact", "magnétique"],
        "subcategories": ["Centrale Alarme", "Détecteur", "Sirène", "Clavier", "Accessoires Alarme"]
    },
    "Contrôle d'Accès": {
        "keywords": ["contrôle accès", "access control", "lecteur", "badge", "biométrique", "empreinte", "facial", "pointeuse", "tripod", "tourniquet", "zkteco"],
        "subcategories": ["Lecteur Biométrique", "Lecteur Badge", "Pointeuse", "Tourniquet", "Accessoires Accès"]
    },
    "Vidéophonie": {
        "keywords": ["visiophone", "vidéophone", "interphone", "platine", "moniteur", "portier", "akuvox"],
        "subcategories": ["Platine de Rue", "Moniteur", "Kit Vidéophone", "Accessoires Vidéophonie"]
    },
    "Incendie": {
        "keywords": ["incendie", "fumée", "smoke", "fire", "détecteur incendie", "sprinkler", "extincteur"],
        "subcategories": ["Détecteur Fumée", "Centrale Incendie", "Extincteur", "Accessoires Incendie"]
    },
    
    # Électricité & Appareillage
    "Interrupteur": {
        "keywords": ["interrupteur", "switch", "va-et-vient", "poussoir", "bouton", "commutateur", "allumage"],
        "subcategories": ["Simple Allumage", "Double Allumage", "Va-et-Vient", "Poussoir", "Variateur"]
    },
    "Prise": {
        "keywords": ["prise", "socket", "schuko", "usb", "rj45", "tv", "téléphone", "prise courant"],
        "subcategories": ["Prise Courant", "Prise USB", "Prise RJ45", "Prise TV", "Prise Téléphone"]
    },
    "Plaque": {
        "keywords": ["plaque", "facade", "finition", "enjoliveur", "cadre"],
        "subcategories": ["Plaque Simple", "Plaque Double", "Plaque Triple", "Plaque Quadruple"]
    },
    "Coffret & Tableau": {
        "keywords": ["coffret", "tableau", "armoire", "boîtier", "modulaire", "disjoncteur", "différentiel"],
        "subcategories": ["Coffret Électrique", "Disjoncteur", "Différentiel", "Armoire"]
    },
    "Boîte & Monture": {
        "keywords": ["boîte", "boite", "monture", "encastrement", "saillie", "apparente"],
        "subcategories": ["Boîte Encastrement", "Boîte Saillie", "Monture", "Boîte Étanche"]
    },
    
    # Éclairage
    "Éclairage": {
        "keywords": ["éclairage", "eclairage", "lampe", "led", "spot", "projecteur", "luminaire", "ampoule", "downlight", "plafonnier"],
        "subcategories": ["Éclairage Intérieur", "Éclairage Extérieur", "Spot LED", "Projecteur", "Ampoule"]
    },
    
    # Domotique & Automatisme
    "Domotique": {
        "keywords": ["domotique", "smart", "connecté", "wifi", "zigbee", "z-wave", "automation", "intelligent", "sonoff", "thermostat"],
        "subcategories": ["Interrupteur Connecté", "Prise Connectée", "Capteur", "Hub Domotique", "Thermostat"]
    },
    "Motorisation": {
        "keywords": ["motorisation", "moteur", "volet", "store", "portail", "garage", "rideau", "pergola", "somfy", "rts", "io"],
        "subcategories": ["Moteur Volet", "Moteur Portail", "Moteur Garage", "Télécommande", "Accessoires Moteur"]
    },
    
    # Réseaux & IT
    "Réseau": {
        "keywords": ["réseau", "network", "switch", "routeur", "router", "wifi", "ap", "access point", "câble", "rj45", "patch", "ruijie"],
        "subcategories": ["Switch", "Routeur", "Point d'Accès WiFi", "Câblage", "Accessoires Réseau"]
    },
    
    # Autres
    "Accessoire": {
        "keywords": ["accessoire", "alimentation", "transformateur", "câble", "connecteur", "adaptateur"],
        "subcategories": ["Alimentation", "Câble", "Connecteur", "Support"]
    }
}

# =============================================================================
# BRAND DETECTION RULES
# =============================================================================
BRAND_RULES = {
    # Exact matches (case-insensitive)
    "exact": {
        "somfy": "Somfy",
        "dahua": "Dahua",
        "hikvision": "Hikvision",
        "zkteco": "ZKTeco",
        "inim": "INIM",
        "legrand": "Legrand",
        "somef": "SOMEF",
        "ruijie": "Ruijie",
        "reyee": "Ruijie",
        "tp-link": "TP-Link",
        "tplink": "TP-Link",
        "eaton": "Eaton",
        "schneider": "Schneider",
        "siemens": "Siemens",
        "abb": "ABB",
        "hager": "Hager",
        "avs": "AVS",
        "sonoff": "Sonoff",
        "akuvox": "Akuvox",
        "imou": "Imou",
        "schutz": "Schutz",
        "zavag": "Zavag",
        "mutlusan": "Mutlusan",
        "langbrug": "Langbrug",
        "swipe": "Swipe",
        "cooper": "Cooper",
    },
    # Pattern matches
    "patterns": [
        (r"\b(DH|IPC|NVR|XVR|HAC|HDW|HFW)\d", "Dahua"),
        (r"\b(DS-|HIK)\d", "Hikvision"),
        (r"\bLT\s?\d{2}", "Somfy"),
        (r"\b(Elixo|Dexxo|Keytis|Keygo|Smoove|Sonesse)", "Somfy"),
        (r"\b(ZK-|SF\d{3}|MB\d{3}|F\d{2}|K\d{2})", "ZKTeco"),
        (r"\b(Smarti|Joy|Air|Smart-i)", "INIM"),
        (r"\b(RG-|EG-|EW-)", "Ruijie"),
        (r"\b(TL-|Archer|Deco)", "TP-Link"),
    ]
}

# =============================================================================
# TECHNOLOGY DETECTION
# =============================================================================
TECHNOLOGY_RULES = {
    # Wireless protocols
    "WiFi": ["wifi", "wi-fi", "wireless", "sans fil", "2.4ghz", "5ghz", "802.11"],
    "Zigbee": ["zigbee", "zigbee 3.0"],
    "Z-Wave": ["z-wave", "zwave"],
    "Bluetooth": ["bluetooth", "ble", "bt"],
    "RF 433MHz": ["433mhz", "433 mhz", "rf"],
    
    # Somfy protocols
    "RTS": ["rts", "radio technology somfy"],
    "io-homecontrol": ["io-homecontrol", "io homecontrol", "io protocol"],
    
    # Video protocols
    "IP": ["ip camera", "ip cam", "poe", "onvif", "rtsp"],
    "HDCVI": ["hdcvi", "hd-cvi"],
    "AHD": ["ahd"],
    "TVI": ["tvi", "hd-tvi"],
    "Analogique": ["analogique", "cvbs", "bnc"],
    
    # Smart home
    "Tuya": ["tuya", "smart life"],
    "Matter": ["matter"],
    "HomeKit": ["homekit", "apple home"],
    "Google Home": ["google home", "google assistant"],
    "Alexa": ["alexa", "amazon echo"],
    
    # Bus systems
    "KNX": ["knx"],
    "Modbus": ["modbus"],
    "BACnet": ["bacnet"],
    "RS485": ["rs485", "rs-485"],
    
    # Network
    "PoE": ["poe", "power over ethernet"],
    "Gigabit": ["gigabit", "1000mbps", "1gbps"],
    "10G": ["10g", "10gbps", "10 gigabit"],
}


def detect_category(product: Dict) -> Tuple[str, str]:
    """
    Detect the main category and subcategory for a product
    Returns (main_category, subcategory)
    """
    name = (product.get('name', '') or '').lower()
    description = (product.get('description', '') or '').lower()
    current_category = (product.get('category', '') or '').lower()
    source = (product.get('source', '') or '').lower()
    
    text = f"{name} {description} {current_category}"
    
    # Score each category
    scores = {}
    for cat_name, cat_data in MASTER_CATEGORIES.items():
        score = 0
        for keyword in cat_data['keywords']:
            if keyword.lower() in text:
                score += 1
                # Boost score for keywords in name
                if keyword.lower() in name:
                    score += 2
        if score > 0:
            scores[cat_name] = score
    
    # Special rules based on source
    if source == 'somfy':
        scores['Motorisation'] = scores.get('Motorisation', 0) + 5
    elif source == 'tus':
        if 'zkteco' in text or 'access' in text:
            scores['Contrôle d\'Accès'] = scores.get('Contrôle d\'Accès', 0) + 3
    
    # Get best match
    if scores:
        main_category = max(scores, key=scores.get)
    else:
        main_category = "Accessoire"
    
    # Determine subcategory
    subcategory = ""
    if main_category in MASTER_CATEGORIES:
        for subcat in MASTER_CATEGORIES[main_category].get('subcategories', []):
            if subcat.lower() in text:
                subcategory = subcat
                break
    
    return main_category, subcategory


def detect_brand(product: Dict) -> str:
    """Detect the brand of a product"""
    name = (product.get('name', '') or '').lower()
    description = (product.get('description', '') or '').lower()
    current_brand = product.get('brand', '')
    source = product.get('source', '')
    
    text = f"{name} {description}"
    
    # Check exact matches first
    for keyword, brand in BRAND_RULES['exact'].items():
        if keyword in text:
            return brand
    
    # Check patterns
    for pattern, brand in BRAND_RULES['patterns']:
        if re.search(pattern, name, re.IGNORECASE):
            return brand
        if re.search(pattern, description, re.IGNORECASE):
            return brand
    
    # Source-based defaults
    source_brands = {
        'somef': 'SOMEF',
        'somfy': 'Somfy',
        'telesys': current_brand if current_brand and current_brand != 'TELESYS' else 'INIM',
        'tus': current_brand if current_brand else 'Dahua',
    }
    
    if source in source_brands:
        return source_brands[source]
    
    return current_brand or "Autre"


def detect_technologies(product: Dict) -> List[str]:
    """Detect technologies used by a product"""
    name = (product.get('name', '') or '').lower()
    description = (product.get('description', '') or '').lower()
    specs = product.get('specifications', {})
    
    text = f"{name} {description} {str(specs)}"
    
    technologies = []
    for tech_name, keywords in TECHNOLOGY_RULES.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                technologies.append(tech_name)
                break
    
    return list(set(technologies))


async def enrich_all_products(db: AsyncIOMotorDatabase, batch_size: int = 100) -> Dict:
    """
    Enrich all products with proper categories, brands, and technologies
    """
    stats = {
        "total": 0,
        "updated": 0,
        "categories_updated": 0,
        "brands_updated": 0,
        "technologies_added": 0,
        "errors": 0
    }
    
    # Get total count
    total = await db.products.count_documents({})
    stats["total"] = total
    logger.info(f"Starting enrichment of {total} products...")
    
    # Process in batches
    skip = 0
    while skip < total:
        products = await db.products.find({}).skip(skip).limit(batch_size).to_list(batch_size)
        
        for product in products:
            try:
                updates = {}
                
                # Detect and update category
                new_category, subcategory = detect_category(product)
                if new_category != product.get('category'):
                    updates['category'] = new_category
                    stats["categories_updated"] += 1
                
                if subcategory:
                    updates['subcategory'] = subcategory
                
                # Detect and update brand
                new_brand = detect_brand(product)
                if new_brand != product.get('brand'):
                    updates['brand'] = new_brand
                    stats["brands_updated"] += 1
                
                # Detect technologies
                technologies = detect_technologies(product)
                if technologies:
                    updates['technologies'] = technologies
                    stats["technologies_added"] += 1
                
                # Apply updates
                if updates:
                    await db.products.update_one(
                        {"_id": product["_id"]},
                        {"$set": updates}
                    )
                    stats["updated"] += 1
                
            except Exception as e:
                logger.error(f"Error enriching product {product.get('name', 'unknown')}: {e}")
                stats["errors"] += 1
        
        skip += batch_size
        logger.info(f"Processed {min(skip, total)}/{total} products...")
    
    logger.info(f"Enrichment complete: {stats}")
    return stats


async def get_category_stats(db: AsyncIOMotorDatabase) -> Dict:
    """Get statistics about product categories"""
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    categories = await db.products.aggregate(pipeline).to_list(100)
    
    pipeline = [
        {"$group": {"_id": "$brand", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 30}
    ]
    brands = await db.products.aggregate(pipeline).to_list(30)
    
    pipeline = [
        {"$unwind": "$technologies"},
        {"$group": {"_id": "$technologies", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    technologies = await db.products.aggregate(pipeline).to_list(50)
    
    return {
        "categories": {c["_id"]: c["count"] for c in categories},
        "brands": {b["_id"]: b["count"] for b in brands},
        "technologies": {t["_id"]: t["count"] for t in technologies}
    }
