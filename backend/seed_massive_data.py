import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# ============ DONNÉES DE BASE ============

VILLES_TUNISIE = [
    "Tunis", "Sfax", "Sousse", "Kairouan", "Bizerte", "Gabès", "Ariana", 
    "Gafsa", "Monastir", "Ben Arous", "La Marsa", "Hammamet", "Nabeul",
    "Médenine", "Kasserine", "Tataouine", "Béja", "Jendouba", "Le Kef",
    "Mahdia", "Sidi Bouzid", "Siliana", "Zaghouan", "Tozeur", "Kébili",
    "Manouba", "Carthage", "Sidi Bou Said", "Gammarth", "Rades", "Megrine",
    "La Goulette", "Le Bardo", "Mourouj", "Hammam Lif", "Borj Cedria",
    "Soliman", "Grombalia", "Menzel Temime", "Kelibia", "Korba", "El Haouaria",
    "Tebourba", "Mateur", "Menzel Bourguiba", "Tabarka", "Ain Draham",
    "Douz", "El Jem", "Msaken", "Kalaa Kebira", "Enfidha", "Hergla"
]

QUARTIERS = [
    "Centre-ville", "Zone industrielle", "Cité", "Résidence", "Lotissement",
    "Avenue principale", "Rue commerçante", "Zone touristique", "Médina",
    "Nouvelle ville", "Zone résidentielle", "Quartier populaire"
]

CATEGORIES_ANNONCES = [
    "Installation Caméra",
    "Système d'Alarme", 
    "Domotique",
    "Éclairage Connecté",
    "Serrure Connectée",
    "Réseau WiFi/Câblage",
    "Autre"
]

STATUTS_ANNONCES = ["EN_ATTENTE", "PUBLIEE", "PUBLIEE", "PUBLIEE", "ATTRIBUEE", "CLOTUREE"]

# Templates d'annonces par catégorie
ANNONCES_TEMPLATES = {
    "Installation Caméra": [
        ("Installation caméras surveillance {lieu}", "Besoin d'installer {nb} caméras de surveillance pour {lieu}. {details}"),
        ("Vidéosurveillance {type_bien}", "Recherche installateur pour système vidéosurveillance complet. {details}"),
        ("Caméras extérieures {lieu}", "Installation de caméras extérieures avec vision nocturne pour {lieu}. {details}"),
        ("Remplacement système caméras", "Mise à niveau de mon ancien système de caméras vers du 4K. {details}"),
        ("Caméra PTZ motorisée", "Installation d'une caméra PTZ pour surveillance périmétrique. {details}"),
    ],
    "Système d'Alarme": [
        ("Alarme {type_bien} neuf", "Installation système d'alarme complet pour {type_bien}. {details}"),
        ("Mise à niveau alarme", "Remplacement de mon ancien système d'alarme par un système connecté. {details}"),
        ("Alarme avec télésurveillance", "Besoin d'un système d'alarme avec option télésurveillance 24/7. {details}"),
        ("Détecteurs mouvement {lieu}", "Ajout de détecteurs de mouvement dans {lieu}. {details}"),
        ("Alarme anti-intrusion", "Installation alarme anti-intrusion avec sirène extérieure. {details}"),
    ],
    "Domotique": [
        ("Domotique {type_bien} complet", "Projet de domotisation complète de mon {type_bien}. {details}"),
        ("Centralisation volets roulants", "Motorisation et centralisation de {nb} volets roulants. {details}"),
        ("Automatisation portail", "Installation automatisme portail avec contrôle smartphone. {details}"),
        ("Scénarios domotiques", "Configuration de scénarios domotiques personnalisés. {details}"),
        ("Intégration assistant vocal", "Intégration Alexa/Google Home pour contrôle vocal. {details}"),
    ],
    "Éclairage Connecté": [
        ("Éclairage intelligent {lieu}", "Installation éclairage connecté dans {lieu}. {details}"),
        ("Remplacement ampoules connectées", "Passage à l'éclairage intelligent pour {nb} points lumineux. {details}"),
        ("Éclairage extérieur automatique", "Installation éclairage extérieur avec détection présence. {details}"),
        ("Variateurs connectés", "Installation de variateurs intelligents dans le salon. {details}"),
        ("Ruban LED décoratif", "Installation ruban LED RGB avec contrôle application. {details}"),
    ],
    "Serrure Connectée": [
        ("Serrure connectée porte entrée", "Remplacement serrure par modèle connecté avec code et empreinte. {details}"),
        ("Contrôle accès {type_bien}", "Installation contrôle d'accès connecté pour {type_bien}. {details}"),
        ("Interphone vidéo connecté", "Installation visiophone avec ouverture à distance. {details}"),
        ("Badge et digicode", "Système d'accès par badge et digicode connecté. {details}"),
        ("Serrure biométrique", "Installation serrure à empreinte digitale. {details}"),
    ],
    "Réseau WiFi/Câblage": [
        ("WiFi mesh {type_bien}", "Installation réseau WiFi mesh pour couverture complète {type_bien}. {details}"),
        ("Câblage réseau {lieu}", "Câblage Ethernet catégorie 6 pour {lieu}. {details}"),
        ("Amélioration couverture WiFi", "Points morts WiFi à éliminer dans {type_bien} de {surface}m². {details}"),
        ("Installation baie de brassage", "Mise en place baie de brassage professionnelle. {details}"),
        ("Réseau professionnel", "Déploiement réseau pour {nb} postes de travail. {details}"),
    ],
    "Autre": [
        ("Thermostat connecté", "Installation thermostat intelligent pour chauffage central. {details}"),
        ("Station météo connectée", "Installation station météo avec intégration domotique. {details}"),
        ("Arrosage automatique intelligent", "Système d'arrosage connecté pour jardin {surface}m². {details}"),
        ("Prise connectée installation", "Installation de prises connectées avec mesure consommation. {details}"),
        ("Audit domotique", "Besoin d'un audit pour projet domotique global. {details}"),
    ]
}

DETAILS_TEMPLATES = [
    "Surface totale environ {surface}m².",
    "Budget prévu entre {budget_min} et {budget_max} DT.",
    "Travaux à réaliser rapidement.",
    "Disponible pour visite technique en semaine.",
    "Devis détaillé souhaité avant intervention.",
    "Préférence pour matériel de marque reconnue.",
    "Installation dans construction neuve.",
    "Rénovation en cours.",
    "Besoin de conseils sur le choix du matériel.",
    "Possibilité de travaux le week-end.",
]

TYPES_BIENS = ["maison", "villa", "appartement", "local commercial", "bureau", "entrepôt", "restaurant", "hôtel", "clinique", "école"]
LIEUX = ["salon", "cuisine", "jardin", "garage", "entrée", "chambre", "terrasse", "piscine", "parking", "bureau", "commerce", "entrepôt"]

# ============ PRODUITS ============

MARQUES = ["Tuya", "Sonoff", "Aqara", "Shelly", "Dahua", "Hikvision", "Leelen", "Xiaomi", "TP-Link", "Ezviz", "Reolink", "Imou", "Tapo", "Innr", "Philips Hue", "IKEA Tradfri"]
TECHNOLOGIES = ["WiFi", "Zigbee", "WiFi/Zigbee", "Z-Wave", "Bluetooth", "LoRa"]

PRODUITS_TEMPLATES = {
    "Vidéosurveillance": [
        ("Caméra Dôme {res} {marque}", "Caméra dôme intérieure {res} avec vision nocturne IR {ir}m, détection mouvement IA, audio bidirectionnel.", 150, 350),
        ("Caméra Bullet Extérieure {res}", "Caméra bullet étanche IP67 {res}, vision nocturne couleur, détection véhicules et personnes.", 180, 400),
        ("Caméra PTZ {res} {marque}", "Caméra motorisée pan/tilt/zoom {res}, suivi automatique, zoom optique {zoom}x.", 250, 600),
        ("Mini Caméra Discrète {res}", "Caméra compacte {res} discrète, idéale pour surveillance intérieure.", 80, 180),
        ("Caméra Fisheye 360°", "Caméra panoramique 360° pour couverture complète d'une pièce.", 200, 450),
        ("NVR {canaux} Canaux", "Enregistreur vidéo réseau {canaux} canaux, disque dur {hdd}TB inclus, compression H.265+.", 300, 800),
        ("Kit Vidéosurveillance {nb} Caméras", "Kit complet {nb} caméras + NVR + câbles + alimentation.", 500, 1500),
        ("Caméra Solaire Sans Fil", "Caméra autonome panneau solaire, batterie rechargeable, 100% sans fil.", 180, 350),
        ("Sonnette Vidéo Connectée", "Visiophone connecté avec caméra HD, détection mouvement, audio 2 voies.", 120, 280),
        ("Caméra Cachée WiFi", "Caméra espion discrète dans objet décoratif, détection mouvement.", 60, 150),
    ],
    "Alarme": [
        ("Kit Alarme {marque} {nb} Zones", "Kit alarme complet: centrale + {nb} détecteurs + sirène + télécommandes.", 250, 600),
        ("Détecteur Mouvement PIR", "Détecteur infrarouge passif, angle {angle}°, portée {portee}m.", 25, 60),
        ("Détecteur Ouverture Porte/Fenêtre", "Capteur magnétique sans fil pour portes et fenêtres.", 15, 40),
        ("Sirène Intérieure {db}dB", "Sirène puissante {db}dB avec flash LED stroboscopique.", 35, 80),
        ("Sirène Extérieure Solaire", "Sirène extérieure étanche avec panneau solaire intégré.", 60, 140),
        ("Clavier Alarme Tactile", "Clavier de commande tactile rétroéclairé avec lecteur badge.", 50, 120),
        ("Détecteur Fumée Connecté", "Détecteur de fumée photoélectrique avec alerte smartphone.", 30, 70),
        ("Détecteur Inondation", "Capteur de fuite d'eau avec alarme sonore et notification.", 25, 55),
        ("Détecteur Bris de Vitre", "Capteur acoustique détection bris de vitre.", 30, 65),
        ("Télécommande Alarme 4 Boutons", "Télécommande porte-clés pour armement/désarmement.", 20, 45),
    ],
    "Éclairage": [
        ("Ampoule LED RGBW E27", "Ampoule connectée {watts}W, 16 millions de couleurs + blanc variable.", 15, 35),
        ("Ampoule LED Blanc Variable E27", "Ampoule {watts}W blanc chaud à froid 2700K-6500K.", 12, 28),
        ("Ampoule LED GU10 Couleur", "Spot GU10 connecté RGB + blanc, compatible variateur.", 18, 40),
        ("Ruban LED RGB {longueur}m", "Ruban LED flexible {longueur}m, modes musique et scènes.", 35, 90),
        ("Spot Encastrable Connecté", "Spot LED encastrable {watts}W, blanc variable, dimming.", 25, 55),
        ("Plafonnier LED Connecté", "Plafonnier {watts}W design moderne, blanc variable + couleurs.", 60, 150),
        ("Applique Murale Connectée", "Applique LED intérieure/extérieure avec détecteur.", 45, 110),
        ("Lampe de Table Connectée", "Lampe d'ambiance RGB contrôlable par application.", 40, 95),
        ("Projecteur LED Extérieur", "Projecteur {watts}W étanche IP65 avec détecteur mouvement.", 50, 130),
        ("Bandeau LED Escalier", "Kit éclairage escalier automatique avec détecteur.", 80, 180),
    ],
    "Module": [
        ("Hub Zigbee 3.0 Universal", "Passerelle Zigbee compatible {nb} appareils, Matter ready.", 60, 120),
        ("Hub WiFi Multi-protocole", "Hub central WiFi/Zigbee/Bluetooth pour centralisation.", 80, 160),
        ("Module Relais WiFi {canaux}CH", "Module relais {canaux} canaux, montage rail DIN.", 35, 80),
        ("Module Variateur WiFi", "Variateur encastrable pour ampoules dimmables.", 30, 65),
        ("Module Volet Roulant", "Module pour motorisation volet existante.", 40, 85),
        ("Module Contact Sec", "Module relais contact sec pour intégration.", 25, 55),
        ("Passerelle IR Universal", "Télécommande universelle IR vers WiFi.", 25, 50),
        ("Module Mesure Énergie", "Compteur d'énergie connecté rail DIN.", 45, 100),
        ("Contrôleur RGB/RGBW", "Contrôleur pour rubans LED RGB/RGBW.", 20, 45),
        ("Module Scène 4 Boutons", "Télécommande murale sans fil 4 scènes.", 30, 60),
    ],
    "Interrupteur": [
        ("Interrupteur Tactile {touches} Touches", "Interrupteur mural verre trempé {touches} touches, rétroéclairé.", 40, 90),
        ("Interrupteur Variateur Rotatif", "Variateur rotatif intelligent, compatible LED.", 55, 110),
        ("Interrupteur Double Va-et-Vient", "Interrupteur connecté pour montage va-et-vient.", 45, 95),
        ("Interrupteur Volet Roulant", "Commande murale pour volet roulant motorisé.", 35, 75),
        ("Interrupteur Sans Neutre", "Interrupteur WiFi ne nécessitant pas de neutre.", 50, 100),
        ("Interrupteur Extérieur IP55", "Interrupteur étanche pour extérieur.", 55, 115),
        ("Bouton Poussoir Connecté", "Bouton sans fil programmable multi-actions.", 25, 50),
        ("Interrupteur Scène", "Interrupteur 4 boutons pour scènes domotiques.", 40, 85),
        ("Détecteur Présence Encastré", "Interrupteur avec détecteur mouvement intégré.", 45, 95),
        ("Interrupteur Minuterie", "Interrupteur avec minuterie programmable.", 35, 70),
    ],
    "Prise": [
        ("Prise Connectée Mesure Énergie", "Prise WiFi 16A avec mesure consommation temps réel.", 20, 45),
        ("Prise Connectée Compacte", "Mini prise WiFi discrète 10A.", 15, 35),
        ("Multiprise Connectée {prises} Prises", "Multiprise intelligente {prises} prises contrôlables + USB.", 50, 110),
        ("Prise Extérieure IP44", "Prise connectée étanche pour extérieur.", 30, 65),
        ("Prise Murale Double USB", "Prise encastrée avec 2 ports USB intégrés.", 25, 55),
        ("Prise Programmable", "Prise avec programmateur horaire hebdomadaire.", 22, 48),
        ("Adaptateur Prise 16A", "Adaptateur connecté haute puissance 16A/3680W.", 28, 58),
        ("Prise avec Veilleuse", "Prise connectée avec veilleuse LED intégrée.", 25, 52),
        ("Rallonge Connectée {prises}m", "Rallonge intelligente {prises}m avec protection.", 40, 90),
        ("Bloc Prise Bureau", "Bloc multiprise encastrable pour bureau.", 55, 120),
    ],
    "Volet": [
        ("Moteur Volet Roulant Tubulaire", "Moteur tubulaire {nm}Nm pour volet jusqu'à {surface}m².", 90, 200),
        ("Module Volet WiFi", "Module WiFi pour motorisation existante.", 40, 85),
        ("Télécommande Volet 16 Canaux", "Télécommande centralisée pour 16 volets.", 60, 130),
        ("Capteur Soleil/Vent", "Capteur météo pour automatisation volets.", 70, 150),
        ("Interrupteur Volet Centralisé", "Commande générale tous volets.", 45, 95),
        ("Kit Motorisation Store Banne", "Kit complet motorisation store extérieur.", 150, 350),
        ("Moteur Rideau Électrique", "Moteur pour rideaux et voilages.", 80, 180),
        ("Récepteur Volet 2 Canaux", "Récepteur radio pour 2 volets.", 50, 100),
        ("Horloge Programmateur Volet", "Programmateur horaire pour volets.", 55, 110),
        ("Émetteur Mural Volet", "Émetteur mural sans fil pour volet.", 35, 70),
    ],
    "Écran": [
        ("Écran Tactile Mural {pouces}\"", "Écran contrôle tactile {pouces} pouces, affichage météo/heure.", 120, 280),
        ("Tablette Domotique Murale", "Tablette Android encastrée pour domotique.", 180, 400),
        ("Interphone Vidéo Connecté", "Moniteur interphone 7\" avec contrôle accès.", 150, 350),
        ("Écran E-Ink Connecté", "Afficheur e-paper pour informations domotiques.", 80, 180),
        ("Cadre Photo Connecté", "Cadre numérique avec intégration domotique.", 100, 220),
        ("Miroir Connecté", "Miroir intelligent avec affichage informations.", 250, 550),
        ("Station Météo Écran Couleur", "Station météo avec grand écran couleur.", 60, 140),
        ("Réveil Connecté", "Réveil intelligent avec simulation lever soleil.", 50, 110),
        ("Écran Contrôle Thermostat", "Thermostat avec écran tactile couleur.", 130, 280),
        ("Visiophone 2 Fils", "Moniteur visiophone installation 2 fils.", 140, 320),
    ],
}

# ============ GÉNÉRATION ============

def generate_phone():
    prefixes = ["20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "50", "51", "52", "53", "54", "55", "56", "58", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99"]
    return f"+216 {random.choice(prefixes)} {random.randint(100, 999)} {random.randint(100, 999)}"

def generate_annonce(client_id, client_name, client_email, pro_users):
    category = random.choice(CATEGORIES_ANNONCES)
    templates = ANNONCES_TEMPLATES[category]
    title_template, desc_template = random.choice(templates)
    
    ville = random.choice(VILLES_TUNISIE)
    quartier = random.choice(QUARTIERS)
    
    # Variables pour templates
    vars_dict = {
        "lieu": random.choice(LIEUX),
        "type_bien": random.choice(TYPES_BIENS),
        "nb": random.randint(2, 10),
        "surface": random.choice([80, 100, 120, 150, 200, 250, 300, 400, 500]),
        "budget_min": random.choice([500, 800, 1000, 1500, 2000]),
        "budget_max": random.choice([2000, 3000, 4000, 5000, 8000]),
    }
    vars_dict["details"] = random.choice(DETAILS_TEMPLATES).format(**vars_dict)
    
    title = title_template.format(**vars_dict)
    description = desc_template.format(**vars_dict)
    
    status = random.choice(STATUTS_ANNONCES)
    
    # Générer des réponses si publiée
    responses = []
    if status in ["PUBLIEE", "ATTRIBUEE", "CLOTUREE"] and random.random() > 0.3:
        num_responses = random.randint(1, 4)
        for _ in range(num_responses):
            pro = random.choice(pro_users)
            responses.append({
                "id": str(uuid.uuid4()),
                "professional_id": pro["id"],
                "professional_name": pro["full_name"],
                "professional_email": pro["email"],
                "professional_phone": pro.get("phone", generate_phone()),
                "message": random.choice([
                    "Bonjour, je suis disponible pour réaliser cette installation. Contactez-moi pour plus de détails.",
                    "Je peux intervenir rapidement. J'ai une grande expérience dans ce type de projet.",
                    "Devis gratuit et sans engagement. Matériel de qualité garanti.",
                    "Disponible pour une visite technique cette semaine.",
                    "Installation professionnelle avec garantie. N'hésitez pas à me contacter.",
                ]),
                "price_estimate": random.randint(200, 5000) + random.random() * 100,
                "availability": random.choice(["Disponible immédiatement", "Sous 48h", "Cette semaine", "Semaine prochaine", "À convenir"]),
                "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))).isoformat()
            })
    
    created_date = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90))
    
    annonce = {
        "id": str(uuid.uuid4()),
        "client_id": client_id,
        "client_name": client_name,
        "client_email": client_email,
        "client_phone": generate_phone(),
        "title": title,
        "description": description,
        "category": category,
        "city": ville,
        "address": f"{quartier}, {ville}",
        "status": status,
        "responses": responses,
        "selected_response_id": responses[0]["id"] if status == "ATTRIBUEE" and responses else None,
        "created_at": created_date.isoformat(),
        "updated_at": created_date.isoformat(),
    }
    
    if status in ["PUBLIEE", "ATTRIBUEE", "CLOTUREE"]:
        annonce["published_at"] = created_date.isoformat()
    if status == "CLOTUREE":
        annonce["closed_at"] = (created_date + timedelta(days=random.randint(5, 30))).isoformat()
    
    return annonce

def generate_product(category):
    templates = PRODUITS_TEMPLATES[category]
    name_template, desc_template, price_min, price_max = random.choice(templates)
    
    marque = random.choice(MARQUES)
    tech = random.choice(TECHNOLOGIES)
    
    vars_dict = {
        "marque": marque,
        "res": random.choice(["2K", "4K", "1080p", "5MP"]),
        "ir": random.choice([20, 30, 50]),
        "zoom": random.choice([4, 8, 16, 20]),
        "canaux": random.choice([4, 8, 16, 32]),
        "hdd": random.choice([1, 2, 4]),
        "nb": random.choice([2, 4, 6, 8]),
        "angle": random.choice([90, 110, 120]),
        "portee": random.choice([8, 10, 12, 15]),
        "db": random.choice([90, 100, 110, 120]),
        "watts": random.choice([5, 7, 9, 10, 12, 15]),
        "longueur": random.choice([3, 5, 10]),
        "touches": random.choice([1, 2, 3, 4]),
        "prises": random.choice([3, 4, 5, 6]),
        "nm": random.choice([10, 15, 20, 30]),
        "surface": random.choice([3, 5, 8, 10]),
        "pouces": random.choice([4, 5, 7, 10]),
    }
    
    name = name_template.format(**vars_dict)
    description = desc_template.format(**vars_dict)
    
    price = round(random.uniform(price_min, price_max), 3)
    
    return {
        "id": str(uuid.uuid4()),
        "name": f"{name} {marque}" if marque not in name else name,
        "description": description,
        "brand": marque,
        "technology": tech,
        "category": category,
        "image_url": f"https://picsum.photos/seed/{uuid.uuid4().hex[:8]}/500/500",
        "gallery_images": [],
        "compatibility": random.sample(["Alexa", "Google Home", "HomeKit", "SmartThings", "IFTTT", "Zigbee 3.0", "Matter"], k=random.randint(2, 4)),
        "usage": random.choice([
            "Usage résidentiel intérieur",
            "Usage résidentiel extérieur", 
            "Usage professionnel",
            "Multi-usage intérieur/extérieur",
            "Installation encastrée",
            "Installation en saillie",
        ]),
        "price": price,
        "featured": random.random() > 0.85,
        "stock_quantity": random.randint(0, 100),
    }

async def seed_massive_data():
    """Générer 1000 annonces et 1000 produits"""
    print("🚀 Génération massive de données...")
    print("="*50)
    
    # Récupérer les utilisateurs existants
    users = await db.users.find({}, {"_id": 0}).to_list(100)
    
    if not users:
        print("❌ Aucun utilisateur trouvé. Exécutez d'abord seed_full_data.py")
        return
    
    clients = [u for u in users if u["role"] == "PARTICULIER"]
    pros = [u for u in users if u["role"] == "PROFESSIONNEL"]
    
    if not clients:
        # Créer un client par défaut
        clients = [{"id": str(uuid.uuid4()), "full_name": "Client Test", "email": "client@mydar.tn"}]
    
    if not pros:
        pros = [{"id": str(uuid.uuid4()), "full_name": "Pro Test", "email": "pro@mydar.tn", "phone": "+216 98 765 432"}]
    
    # ============ GÉNÉRER 1000 ANNONCES ============
    print("\n📢 Génération de 1000 annonces...")
    annonces = []
    for i in range(1000):
        client = random.choice(clients)
        annonce = generate_annonce(client["id"], client["full_name"], client["email"], pros)
        annonces.append(annonce)
        if (i + 1) % 100 == 0:
            print(f"   {i + 1}/1000 annonces générées...")
    
    # Insérer par batch
    await db.annonces.delete_many({})
    for i in range(0, len(annonces), 100):
        batch = annonces[i:i+100]
        await db.annonces.insert_many(batch)
    print(f"✅ {len(annonces)} annonces insérées")
    
    # ============ GÉNÉRER 1000 PRODUITS ============
    print("\n📦 Génération de 1000 produits...")
    categories = list(PRODUITS_TEMPLATES.keys())
    products = []
    
    for i in range(1000):
        category = random.choice(categories)
        product = generate_product(category)
        products.append(product)
        if (i + 1) % 100 == 0:
            print(f"   {i + 1}/1000 produits générés...")
    
    # Insérer par batch
    await db.products.delete_many({})
    for i in range(0, len(products), 100):
        batch = products[i:i+100]
        await db.products.insert_many(batch)
    print(f"✅ {len(products)} produits insérés")
    
    # ============ METTRE À JOUR LES COMPTEURS ============
    print("\n📊 Mise à jour des compteurs de catégories...")
    categories_db = await db.categories.find({}, {"_id": 0}).to_list(100)
    for cat in categories_db:
        count = await db.products.count_documents({"category": cat["name"]})
        await db.categories.update_one({"id": cat["id"]}, {"$set": {"product_count": count}})
    
    # ============ STATISTIQUES ============
    print("\n" + "="*50)
    print("🎉 GÉNÉRATION TERMINÉE!")
    print("="*50)
    
    # Stats annonces
    total_annonces = await db.annonces.count_documents({})
    publiees = await db.annonces.count_documents({"status": "PUBLIEE"})
    en_attente = await db.annonces.count_documents({"status": "EN_ATTENTE"})
    attribuees = await db.annonces.count_documents({"status": "ATTRIBUEE"})
    cloturees = await db.annonces.count_documents({"status": "CLOTUREE"})
    
    print(f"\n📢 ANNONCES: {total_annonces}")
    print(f"   - Publiées: {publiees}")
    print(f"   - En attente: {en_attente}")
    print(f"   - Attribuées: {attribuees}")
    print(f"   - Clôturées: {cloturees}")
    
    # Stats par ville (top 10)
    pipeline = [
        {"$group": {"_id": "$city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_villes = await db.annonces.aggregate(pipeline).to_list(10)
    print(f"\n🏙️ TOP 10 VILLES:")
    for v in top_villes:
        print(f"   - {v['_id']}: {v['count']} annonces")
    
    # Stats produits
    total_products = await db.products.count_documents({})
    print(f"\n📦 PRODUITS: {total_products}")
    
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    cats_stats = await db.products.aggregate(pipeline).to_list(20)
    print(f"\n📁 PAR CATÉGORIE:")
    for c in cats_stats:
        print(f"   - {c['_id']}: {c['count']} produits")

if __name__ == "__main__":
    asyncio.run(seed_massive_data())
    client.close()
