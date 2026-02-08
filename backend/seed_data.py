import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Services data
SERVICES = [
    {
        "id": "videophone",
        "name": "Vidéophone",
        "slug": "videophone",
        "description": "Contrôlez vos accès avec un système de vidéophonie intelligent",
        "detailed_description": "Notre solution de vidéophonie connectée vous permet de voir et communiquer avec vos visiteurs depuis n'importe où. Compatible avec smartphones et tablettes, elle offre une sécurité optimale pour votre domicile ou entreprise.",
        "advantages": [
            "Vision HD jour et nuit",
            "Communication bidirectionnelle claire",
            "Enregistrement automatique des visites",
            "Ouverture à distance",
            "Notifications instantanées"
        ],
        "use_cases": [
            "Maison individuelle",
            "Immeuble collectif",
            "Entreprise",
            "Résidence sécurisée"
        ],
        "icon": "📹",
        "image_url": None,
        "category": "security",
        "featured": True
    },
    {
        "id": "lighting",
        "name": "Éclairage Intelligent",
        "slug": "eclairage-intelligent",
        "description": "Automatisez et contrôlez votre éclairage pour plus de confort et d'économies",
        "detailed_description": "Transformez votre éclairage en système intelligent. Programmez des scénarios, ajustez l'intensité et la couleur, et contrôlez tout depuis votre smartphone ou par commande vocale.",
        "advantages": [
            "Économies d'énergie jusqu'à 40%",
            "Ambiances personnalisables",
            "Contrôle vocal (Alexa, Google)",
            "Programmation horaire",
            "Détection de présence"
        ],
        "use_cases": [
            "Salon et chambres",
            "Éclairage extérieur",
            "Bureaux professionnels",
            "Commerces"
        ],
        "icon": "💡",
        "image_url": None,
        "category": "automation",
        "featured": True
    },
    {
        "id": "shutters",
        "name": "Centralisation Volets Roulants",
        "slug": "volets-roulants",
        "description": "Centralisez le contrôle de tous vos volets roulants",
        "detailed_description": "Pilotez l'ensemble de vos volets roulants depuis une interface unique. Programmez des ouvertures et fermetures automatiques selon vos horaires et préférences.",
        "advantages": [
            "Ouverture/fermeture automatique",
            "Programmation par horaires",
            "Simulation de présence",
            "Contrôle groupe ou individuel",
            "Intégration météo"
        ],
        "use_cases": [
            "Maison connectée",
            "Appartement",
            "Villa",
            "Bâtiment tertiaire"
        ],
        "icon": "🪟",
        "image_url": None,
        "category": "automation",
        "featured": False
    },
    {
        "id": "control-screens",
        "name": "Écrans de Contrôle",
        "slug": "ecrans-controle",
        "description": "Tableaux de bord tactiles pour piloter toute votre installation",
        "detailed_description": "Des écrans tactiles élégants et intuitifs pour contrôler l'ensemble de votre système domotique. Design moderne s'intégrant parfaitement à votre décoration.",
        "advantages": [
            "Interface intuitive",
            "Design personnalisable",
            "Contrôle centralisé",
            "Affichage météo et infos",
            "Installation murale"
        ],
        "use_cases": [
            "Hall d'entrée",
            "Salon",
            "Bureau",
            "Cuisine"
        ],
        "icon": "📱",
        "image_url": None,
        "category": "control",
        "featured": False
    },
    {
        "id": "alarm",
        "name": "Alarme",
        "slug": "alarme",
        "description": "Système d'alarme intelligent et connecté pour votre sécurité",
        "detailed_description": "Protection complète de votre domicile avec détecteurs de mouvement, ouverture, et sirène. Alertes instantanées sur smartphone et possibilité de télésurveillance.",
        "advantages": [
            "Détection intrusion",
            "Alertes instantanées",
            "Sirène intérieure/extérieure",
            "Mode absent/nuit",
            "Télésurveillance compatible"
        ],
        "use_cases": [
            "Résidence principale",
            "Résidence secondaire",
            "Commerce",
            "Entrepôt"
        ],
        "icon": "🚨",
        "image_url": None,
        "category": "security",
        "featured": True
    },
    {
        "id": "video-surveillance",
        "name": "Vidéosurveillance",
        "slug": "videosurveillance",
        "description": "Solution complète de vidéosurveillance HD avec vision nocturne",
        "detailed_description": "Système de vidéosurveillance professionnel avec caméras HD, enregistrement cloud, détection de mouvement intelligente et vision à distance. Protection 24/7 de vos biens.",
        "advantages": [
            "Caméras HD/4K",
            "Vision nocturne infrarouge",
            "Détection intelligente (personnes, véhicules)",
            "Enregistrement cloud sécurisé",
            "Visualisation en temps réel",
            "Alertes personnalisées"
        ],
        "use_cases": [
            "Surveillance périmétrique",
            "Intérieur maison",
            "Parking et garage",
            "Commerce et bureaux",
            "Chantier"
        ],
        "icon": "📹",
        "image_url": None,
        "category": "security",
        "featured": True
    },
    {
        "id": "thermostat",
        "name": "Thermostat Connecté",
        "slug": "thermostat-connecte",
        "description": "Optimisez votre confort thermique et réalisez des économies d'énergie",
        "detailed_description": "Notre thermostat intelligent apprend vos habitudes et optimise automatiquement la température de votre logement. Contrôlez votre chauffage à distance et programmez des scénarios personnalisés pour chaque pièce. Compatible avec tous les systèmes de chauffage existants.",
        "advantages": [
            "Économies d'énergie jusqu'à 30%",
            "Contrôle par pièce ou zone",
            "Programmation intelligente auto-apprenante",
            "Contrôle à distance via smartphone",
            "Détection présence/absence",
            "Intégration météo pour anticipation",
            "Compatible assistants vocaux"
        ],
        "use_cases": [
            "Maison individuelle",
            "Appartement",
            "Bureau",
            "Commerce",
            "Résidence secondaire"
        ],
        "icon": "🌡️",
        "image_url": None,
        "category": "automation",
        "featured": True
    }
]

# Products data
PRODUCTS = [
    # Modules
    {
        "id": "module-wifi-1",
        "name": "Module WiFi Multi-zones",
        "description": "Module central pour contrôler jusqu'à 8 zones différentes",
        "technology": "WiFi",
        "category": "Module",
        "image_url": None,
        "compatibility": ["Alexa", "Google Home", "Homekit"],
        "usage": "Installation centrale pour piloter l'ensemble de votre installation",
        "price": 149.99,
        "featured": True
    },
    {
        "id": "module-zigbee-1",
        "name": "Hub Zigbee",
        "description": "Pont de connexion pour tous vos appareils Zigbee",
        "technology": "Zigbee",
        "category": "Module",
        "image_url": None,
        "compatibility": ["Zigbee 3.0", "Matter"],
        "usage": "Connecte jusqu'à 100 appareils Zigbee",
        "price": 89.99,
        "featured": True
    },
    # Écrans
    {
        "id": "screen-touch-1",
        "name": "Écran Tactile 7 pouces",
        "description": "Écran de contrôle tactile mural avec affichage météo",
        "technology": "WiFi",
        "category": "Écran",
        "image_url": None,
        "compatibility": ["Tous protocoles"],
        "usage": "Contrôle centralisé de toute votre domotique",
        "price": 299.99,
        "featured": True
    },
    # Éclairage
    {
        "id": "bulb-color-1",
        "name": "Ampoule LED Couleur E27",
        "description": "Ampoule connectée RGB + blanc variable 10W",
        "technology": "WiFi/Zigbee",
        "category": "Éclairage",
        "image_url": None,
        "compatibility": ["Alexa", "Google Home"],
        "usage": "Éclairage d'ambiance salon, chambre",
        "price": 24.99,
        "featured": False
    },
    {
        "id": "spot-wifi-1",
        "name": "Spot Encastrable WiFi",
        "description": "Spot LED encastrable intelligent blanc variable",
        "technology": "WiFi",
        "category": "Éclairage",
        "image_url": None,
        "compatibility": ["Alexa", "Google Home"],
        "usage": "Éclairage cuisine, couloir",
        "price": 34.99,
        "featured": False
    },
    # Interrupteurs
    {
        "id": "switch-wifi-1",
        "name": "Interrupteur WiFi Tactile",
        "description": "Interrupteur tactile 1 à 4 gangs",
        "technology": "WiFi",
        "category": "Interrupteur",
        "image_url": None,
        "compatibility": ["Alexa", "Google Home"],
        "usage": "Remplacement interrupteur standard",
        "price": 39.99,
        "featured": False
    },
    # Prises
    {
        "id": "outlet-wifi-1",
        "name": "Prise Connectée WiFi",
        "description": "Prise intelligente avec mesure de consommation",
        "technology": "WiFi",
        "category": "Prise",
        "image_url": None,
        "compatibility": ["Alexa", "Google Home"],
        "usage": "Automatisation appareils électriques",
        "price": 19.99,
        "featured": False
    },
    # Vidéosurveillance
    {
        "id": "camera-outdoor-1",
        "name": "Caméra Extérieure 4K",
        "description": "Caméra IP 4K avec vision nocturne 30m et détection IA",
        "technology": "WiFi",
        "category": "Vidéosurveillance",
        "image_url": None,
        "compatibility": ["ONVIF", "RTSP"],
        "usage": "Surveillance périmétrique extérieure",
        "price": 199.99,
        "featured": True
    },
    {
        "id": "camera-indoor-1",
        "name": "Caméra Intérieure 2K",
        "description": "Caméra rotative 360° avec suivi automatique",
        "technology": "WiFi",
        "category": "Vidéosurveillance",
        "image_url": None,
        "compatibility": ["ONVIF", "Cloud"],
        "usage": "Surveillance intérieure",
        "price": 89.99,
        "featured": True
    },
    {
        "id": "nvr-8ch",
        "name": "Enregistreur NVR 8 Canaux",
        "description": "Enregistreur réseau pour 8 caméras avec disque 2TB",
        "technology": "WiFi",
        "category": "Vidéosurveillance",
        "image_url": None,
        "compatibility": ["ONVIF", "H.265"],
        "usage": "Enregistrement centralisé vidéosurveillance",
        "price": 349.99,
        "featured": False
    },
    # Alarme
    {
        "id": "alarm-kit-1",
        "name": "Kit Alarme Complet",
        "description": "Kit alarme: centrale + 3 détecteurs + sirène + télécommandes",
        "technology": "WiFi/Zigbee",
        "category": "Alarme",
        "image_url": None,
        "compatibility": ["GSM", "Application mobile"],
        "usage": "Protection complète maison",
        "price": 299.99,
        "featured": True
    },
    {
        "id": "motion-sensor-1",
        "name": "Détecteur de Mouvement",
        "description": "Détecteur PIR sans fil portée 12m",
        "technology": "Zigbee",
        "category": "Alarme",
        "image_url": None,
        "compatibility": ["Zigbee 3.0"],
        "usage": "Détection présence intérieur",
        "price": 29.99,
        "featured": False
    },
    # Volets
    {
        "id": "shutter-motor-1",
        "name": "Moteur Volet Roulant WiFi",
        "description": "Motorisation connectée pour volet roulant",
        "technology": "WiFi",
        "category": "Volet",
        "image_url": None,
        "compatibility": ["Alexa", "Google Home"],
        "usage": "Automatisation volet roulant existant",
        "price": 129.99,
        "featured": False
    },
    # Thermostat
    {
        "id": "thermostat-smart-1",
        "name": "Thermostat Connecté WiFi",
        "description": "Thermostat intelligent avec apprentissage automatique",
        "technology": "WiFi",
        "category": "Autre",
        "image_url": None,
        "compatibility": ["Alexa", "Google Home", "Homekit"],
        "usage": "Régulation température multi-zones",
        "price": 199.99,
        "featured": True
    },
    {
        "id": "thermostat-valve-1",
        "name": "Têtes Thermostatiques Connectées (Pack 4)",
        "description": "Vannes thermostatiques intelligentes pour radiateurs",
        "technology": "Zigbee",
        "category": "Autre",
        "image_url": None,
        "compatibility": ["Zigbee 3.0"],
        "usage": "Contrôle température par pièce",
        "price": 149.99,
        "featured": False
    }
]

async def seed_database():
    """Seed the database with initial data"""
    print("🌱 Starting database seeding...")
    
    # Clear existing data
    await db.services.delete_many({})
    await db.products.delete_many({})
    print("✅ Cleared existing data")
    
    # Insert services
    await db.services.insert_many(SERVICES)
    print(f"✅ Inserted {len(SERVICES)} services")
    
    # Insert products
    await db.products.insert_many(PRODUCTS)
    print(f"✅ Inserted {len(PRODUCTS)} products")
    
    print("🎉 Database seeding completed!")

if __name__ == "__main__":
    asyncio.run(seed_database())
    client.close()
