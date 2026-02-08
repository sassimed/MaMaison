import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone
import uuid
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# ============ USERS ============
USERS = [
    {
        "id": str(uuid.uuid4()),
        "email": "admin@mydar.tn",
        "full_name": "Administrateur MyDar",
        "phone": "+216 70 123 456",
        "address": "Centre Urbain Nord, Tunis",
        "role": "ADMIN",
        "is_active": True,
        "is_email_verified": True,
        "hashed_password": hash_password("admin123"),
        "loyalty_points": 0,
        "total_spent": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "email": "pro@mydar.tn",
        "full_name": "TechPro Installation",
        "phone": "+216 98 765 432",
        "address": "Rue de la Liberté, Sousse",
        "role": "PROFESSIONNEL",
        "is_active": True,
        "is_email_verified": True,
        "hashed_password": hash_password("pro123"),
        "loyalty_points": 150,
        "total_spent": 2500.000,
        "company_info": {
            "company_name": "TechPro Installation SARL",
            "siret": "12345678901234",
            "address": "Zone Industrielle, Sousse 4000",
            "technical_contact": "Ahmed Ben Ali",
            "website": "https://techpro-installation.tn",
            "sites": [
                {"name": "Siège Sousse", "address": "Zone Industrielle, Sousse"},
                {"name": "Agence Tunis", "address": "La Marsa, Tunis"}
            ]
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "email": "client@mydar.tn",
        "full_name": "Mohamed Ben Salah",
        "phone": "+216 55 111 222",
        "address": "Cité Ennasr, Ariana",
        "role": "PARTICULIER",
        "is_active": True,
        "is_email_verified": True,
        "hashed_password": hash_password("client123"),
        "loyalty_points": 75,
        "total_spent": 850.500,
        "address_details": {
            "street": "15, Rue des Oliviers",
            "street2": "Apt 3B",
            "postal_code": "2037",
            "city": "Ariana",
            "country": "Tunisie"
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
]

# ============ CATEGORIES ============
CATEGORIES = [
    {
        "id": str(uuid.uuid4()),
        "name": "Vidéosurveillance",
        "description": "Caméras IP, NVR, et accessoires de vidéosurveillance",
        "icon": "Camera",
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
        "product_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Alarme",
        "description": "Systèmes d'alarme, détecteurs et sirènes",
        "icon": "Bell",
        "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400",
        "product_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Éclairage",
        "description": "Ampoules connectées, spots et rubans LED",
        "icon": "Lightbulb",
        "image_url": "https://images.unsplash.com/photo-1565814329452-e1efa11c5b89?w=400",
        "product_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Module",
        "description": "Modules et hubs de contrôle domotique",
        "icon": "Cpu",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400",
        "product_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Interrupteur",
        "description": "Interrupteurs tactiles et intelligents",
        "icon": "ToggleRight",
        "image_url": "https://images.unsplash.com/photo-1558618047-f4b511d1e6e4?w=400",
        "product_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Prise",
        "description": "Prises connectées avec mesure de consommation",
        "icon": "Plug",
        "image_url": "https://images.unsplash.com/photo-1544724569-5f546fd6f2b5?w=400",
        "product_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Volet",
        "description": "Motorisation et contrôle de volets roulants",
        "icon": "Blinds",
        "image_url": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=400",
        "product_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Écran",
        "description": "Écrans tactiles et tableaux de contrôle",
        "icon": "Monitor",
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400",
        "product_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
]

# ============ PRODUCTS ============
PRODUCTS = [
    # Vidéosurveillance
    {
        "id": str(uuid.uuid4()),
        "name": "Caméra Dôme 4K Tuya",
        "description": "Caméra dôme intérieure 4K avec vision nocturne IR 30m, détection de mouvement IA, audio bidirectionnel et stockage cloud.",
        "brand": "Tuya",
        "technology": "WiFi",
        "category": "Vidéosurveillance",
        "image_url": "https://images.unsplash.com/photo-1557324232-b8917d3c3dcb?w=500",
        "gallery_images": [],
        "compatibility": ["Alexa", "Google Home", "SmartThings"],
        "usage": "Surveillance intérieure maison et bureau",
        "price": 189.900,
        "featured": True,
        "stock_quantity": 25
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Caméra Bullet Extérieure Leelen",
        "description": "Caméra bullet 2K étanche IP67, vision nocturne couleur, détection véhicules et personnes, sirène intégrée.",
        "brand": "Leelen",
        "technology": "WiFi",
        "category": "Vidéosurveillance",
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500",
        "gallery_images": [],
        "compatibility": ["ONVIF", "NVR Compatible"],
        "usage": "Surveillance périmétrique extérieure",
        "price": 249.500,
        "featured": True,
        "stock_quantity": 18
    },
    {
        "id": str(uuid.uuid4()),
        "name": "NVR 8 Canaux 4K",
        "description": "Enregistreur vidéo réseau 8 canaux, disque dur 2TB inclus, compression H.265+, accès distant application mobile.",
        "brand": "Dahua",
        "technology": "WiFi",
        "category": "Vidéosurveillance",
        "image_url": "https://images.unsplash.com/photo-1597424216809-3ba9864aeb18?w=500",
        "gallery_images": [],
        "compatibility": ["ONVIF", "RTSP", "P2P Cloud"],
        "usage": "Enregistrement centralisé système vidéosurveillance",
        "price": 459.000,
        "featured": False,
        "stock_quantity": 12
    },
    # Alarme
    {
        "id": str(uuid.uuid4()),
        "name": "Kit Alarme Premium Sonoff",
        "description": "Kit complet: centrale WiFi/GSM, 4 détecteurs mouvement, 2 détecteurs ouverture, sirène 110dB, 2 télécommandes.",
        "brand": "Sonoff",
        "technology": "WiFi/Zigbee",
        "category": "Alarme",
        "image_url": "https://images.unsplash.com/photo-1558002038-1055907df827?w=500",
        "gallery_images": [],
        "compatibility": ["eWeLink", "Alexa", "Google Home"],
        "usage": "Protection complète maison ou appartement",
        "price": 389.000,
        "featured": True,
        "stock_quantity": 15
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Détecteur de Mouvement PIR Zigbee",
        "description": "Détecteur infrarouge passif sans fil, angle 110°, portée 12m, pile CR2450 longue durée 2 ans.",
        "brand": "Aqara",
        "technology": "Zigbee",
        "category": "Alarme",
        "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=500",
        "gallery_images": [],
        "compatibility": ["Zigbee 3.0", "HomeKit", "Alexa"],
        "usage": "Automatisation éclairage et sécurité",
        "price": 35.900,
        "featured": False,
        "stock_quantity": 50
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Sirène Intérieure 110dB",
        "description": "Sirène puissante avec flash LED, alimentation secteur + batterie secours, déclenchement via app.",
        "brand": "Tuya",
        "technology": "WiFi",
        "category": "Alarme",
        "image_url": "https://images.unsplash.com/photo-1592435284330-ee9551b09822?w=500",
        "gallery_images": [],
        "compatibility": ["Tuya Smart", "Smart Life"],
        "usage": "Dissuasion intrusion",
        "price": 49.900,
        "featured": False,
        "stock_quantity": 30
    },
    # Éclairage
    {
        "id": str(uuid.uuid4()),
        "name": "Ampoule LED RGBW E27 Tuya",
        "description": "Ampoule connectée 10W, 16 millions de couleurs + blanc chaud/froid variable 2700K-6500K, 800 lumens.",
        "brand": "Tuya",
        "technology": "WiFi",
        "category": "Éclairage",
        "image_url": "https://images.unsplash.com/photo-1565814329452-e1efa11c5b89?w=500",
        "gallery_images": [],
        "compatibility": ["Alexa", "Google Home", "SmartThings"],
        "usage": "Éclairage d'ambiance salon, chambre",
        "price": 19.900,
        "featured": True,
        "stock_quantity": 100
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Ruban LED RGB 5m Sonoff",
        "description": "Ruban LED flexible 5 mètres, 300 LEDs, contrôle par application, modes musique et scènes prédéfinies.",
        "brand": "Sonoff",
        "technology": "WiFi",
        "category": "Éclairage",
        "image_url": "https://images.unsplash.com/photo-1550985616-10810253b84d?w=500",
        "gallery_images": [],
        "compatibility": ["eWeLink", "Alexa", "Google Home"],
        "usage": "Décoration TV, bureau, cuisine",
        "price": 45.500,
        "featured": False,
        "stock_quantity": 35
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Spot Encastrable GU10 Zigbee",
        "description": "Spot LED encastrable 5W, blanc variable 2700K-6500K, dimming progressif, compatible hub Zigbee.",
        "brand": "Innr",
        "technology": "Zigbee",
        "category": "Éclairage",
        "image_url": "https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=500",
        "gallery_images": [],
        "compatibility": ["Philips Hue", "Zigbee 3.0"],
        "usage": "Éclairage encastré cuisine, couloir",
        "price": 29.900,
        "featured": False,
        "stock_quantity": 60
    },
    # Modules
    {
        "id": str(uuid.uuid4()),
        "name": "Hub Zigbee 3.0 Universal",
        "description": "Passerelle Zigbee 3.0 compatible 128 appareils, Ethernet + WiFi, Matter ready pour future compatibilité.",
        "brand": "Sonoff",
        "technology": "Zigbee",
        "category": "Module",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=500",
        "gallery_images": [],
        "compatibility": ["Zigbee 3.0", "Matter", "HomeAssistant"],
        "usage": "Centre de contrôle domotique",
        "price": 79.900,
        "featured": True,
        "stock_quantity": 20
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Module Relais WiFi 4 Canaux",
        "description": "Module relais 4 sorties indépendantes, montage rail DIN, programmation horaire, mesure consommation.",
        "brand": "Shelly",
        "technology": "WiFi",
        "category": "Module",
        "image_url": "https://images.unsplash.com/photo-1597424216809-3ba9864aeb18?w=500",
        "gallery_images": [],
        "compatibility": ["MQTT", "REST API", "Alexa"],
        "usage": "Automatisation tableau électrique",
        "price": 65.000,
        "featured": False,
        "stock_quantity": 25
    },
    # Interrupteurs
    {
        "id": str(uuid.uuid4()),
        "name": "Interrupteur Tactile 3 Touches",
        "description": "Interrupteur mural verre trempé, 3 touches capacitives, rétroéclairage LED, neutre non requis.",
        "brand": "Tuya",
        "technology": "WiFi",
        "category": "Interrupteur",
        "image_url": "https://images.unsplash.com/photo-1558618047-f4b511d1e6e4?w=500",
        "gallery_images": [],
        "compatibility": ["Tuya Smart", "Alexa", "Google Home"],
        "usage": "Remplacement interrupteur salon, chambre",
        "price": 55.000,
        "featured": True,
        "stock_quantity": 40
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Interrupteur Variateur Zigbee",
        "description": "Variateur rotatif intelligent, compatible ampoules dimmables LED/halogène, réglage min-max.",
        "brand": "Aqara",
        "technology": "Zigbee",
        "category": "Interrupteur",
        "image_url": "https://images.unsplash.com/photo-1545259742-b4fd8fea67e4?w=500",
        "gallery_images": [],
        "compatibility": ["Zigbee 3.0", "HomeKit", "Alexa"],
        "usage": "Variation éclairage salon, salle à manger",
        "price": 69.900,
        "featured": False,
        "stock_quantity": 22
    },
    # Prises
    {
        "id": str(uuid.uuid4()),
        "name": "Prise Connectée Mesure Énergie",
        "description": "Prise WiFi 16A avec mesure temps réel consommation, historique, programmation, protection surtension.",
        "brand": "Sonoff",
        "technology": "WiFi",
        "category": "Prise",
        "image_url": "https://images.unsplash.com/photo-1544724569-5f546fd6f2b5?w=500",
        "gallery_images": [],
        "compatibility": ["eWeLink", "Alexa", "Google Home"],
        "usage": "Contrôle appareils électroménagers",
        "price": 25.900,
        "featured": True,
        "stock_quantity": 80
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Multiprise Connectée 4 Prises + USB",
        "description": "Multiprise intelligente 4 prises contrôlables individuellement + 4 ports USB, protection parafoudre.",
        "brand": "Tuya",
        "technology": "WiFi",
        "category": "Prise",
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500",
        "gallery_images": [],
        "compatibility": ["Tuya Smart", "Alexa", "Google Home"],
        "usage": "Bureau, salon multimédia",
        "price": 59.900,
        "featured": False,
        "stock_quantity": 28
    },
    # Volets
    {
        "id": str(uuid.uuid4()),
        "name": "Module Volet Roulant WiFi",
        "description": "Module pour motorisation volet existante, calibrage automatique, position pourcentage, programmation soleil.",
        "brand": "Shelly",
        "technology": "WiFi",
        "category": "Volet",
        "image_url": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=500",
        "gallery_images": [],
        "compatibility": ["Alexa", "Google Home", "HomeAssistant"],
        "usage": "Automatisation volets existants",
        "price": 45.000,
        "featured": True,
        "stock_quantity": 35
    },
    # Écrans
    {
        "id": str(uuid.uuid4()),
        "name": "Écran Tactile Mural 4 pouces",
        "description": "Écran de contrôle tactile, affichage météo/heure, contrôle scènes, intercom vidéo, montage encastré.",
        "brand": "Tuya",
        "technology": "WiFi/Zigbee",
        "category": "Écran",
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500",
        "gallery_images": [],
        "compatibility": ["Tuya Smart", "Zigbee 3.0"],
        "usage": "Point de contrôle entrée, salon",
        "price": 159.000,
        "featured": True,
        "stock_quantity": 10
    }
]

# ============ SERVICES ============
SERVICES = [
    {
        "id": "videophone",
        "name": "Vidéophone",
        "slug": "videophone",
        "description": "Contrôlez vos accès avec un système de vidéophonie intelligent",
        "detailed_description": "Notre solution de vidéophonie connectée vous permet de voir et communiquer avec vos visiteurs depuis n'importe où. Compatible avec smartphones et tablettes.",
        "advantages": ["Vision HD jour et nuit", "Communication bidirectionnelle", "Ouverture à distance", "Notifications instantanées"],
        "use_cases": ["Maison individuelle", "Immeuble collectif", "Entreprise"],
        "icon": "Video",
        "category": "security",
        "featured": True
    },
    {
        "id": "lighting",
        "name": "Éclairage Intelligent",
        "slug": "eclairage-intelligent",
        "description": "Automatisez votre éclairage pour plus de confort et d'économies",
        "detailed_description": "Transformez votre éclairage en système intelligent. Programmez des scénarios, ajustez l'intensité et contrôlez tout depuis votre smartphone.",
        "advantages": ["Économies jusqu'à 40%", "Ambiances personnalisables", "Contrôle vocal", "Détection de présence"],
        "use_cases": ["Salon et chambres", "Éclairage extérieur", "Bureaux"],
        "icon": "Lightbulb",
        "category": "automation",
        "featured": True
    },
    {
        "id": "alarm",
        "name": "Système d'Alarme",
        "slug": "alarme",
        "description": "Protection complète de votre domicile avec alertes instantanées",
        "detailed_description": "Système d'alarme connecté avec détecteurs de mouvement, capteurs d'ouverture et sirène. Alertes en temps réel sur votre smartphone.",
        "advantages": ["Détection intrusion", "Alertes instantanées", "Télésurveillance compatible", "Mode absent/nuit"],
        "use_cases": ["Résidence principale", "Commerce", "Entrepôt"],
        "icon": "Bell",
        "category": "security",
        "featured": True
    },
    {
        "id": "video-surveillance",
        "name": "Vidéosurveillance",
        "slug": "videosurveillance",
        "description": "Surveillez votre propriété 24h/24 avec nos caméras HD",
        "detailed_description": "Installation professionnelle de systèmes de vidéosurveillance avec caméras HD/4K, enregistrement et accès à distance.",
        "advantages": ["Vision nocturne", "Détection IA", "Enregistrement cloud", "Accès mobile"],
        "use_cases": ["Périmètre maison", "Parking", "Commerce"],
        "icon": "Camera",
        "category": "security",
        "featured": True
    },
    {
        "id": "shutters",
        "name": "Volets Connectés",
        "slug": "volets-connectes",
        "description": "Centralisez le contrôle de tous vos volets roulants",
        "detailed_description": "Pilotez vos volets depuis une interface unique. Programmation automatique selon horaires et ensoleillement.",
        "advantages": ["Ouverture automatique", "Simulation présence", "Contrôle groupe", "Intégration météo"],
        "use_cases": ["Maison", "Appartement", "Villa"],
        "icon": "Blinds",
        "category": "automation",
        "featured": False
    },
    {
        "id": "network",
        "name": "Réseau & Câblage",
        "slug": "reseau-cablage",
        "description": "Installation réseau WiFi performant et câblage structuré",
        "detailed_description": "Déploiement de réseaux WiFi mesh, câblage Ethernet catégorie 6, et optimisation de la couverture réseau.",
        "advantages": ["WiFi mesh", "Câblage Cat6", "Couverture optimale", "Sécurité réseau"],
        "use_cases": ["Grande maison", "Bureau", "Commerce"],
        "icon": "Wifi",
        "category": "network",
        "featured": False
    }
]

# ============ ANNONCES ============
def create_annonces():
    client_id = USERS[2]["id"]  # Le particulier
    pro_id = USERS[1]["id"]  # Le professionnel
    
    return [
        {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "client_name": "Mohamed Ben Salah",
            "client_email": "client@mydar.tn",
            "client_phone": "+216 55 111 222",
            "title": "Installation système vidéosurveillance villa",
            "description": "Je recherche un professionnel pour installer un système de vidéosurveillance complet dans ma villa. J'ai besoin de 4 caméras extérieures et 2 intérieures avec un NVR. La villa fait environ 300m² sur un terrain de 500m².",
            "category": "Installation Caméra",
            "city": "La Marsa",
            "address": "Résidence Les Jardins, La Marsa",
            "status": "PUBLIEE",
            "responses": [
                {
                    "id": str(uuid.uuid4()),
                    "professional_id": pro_id,
                    "professional_name": "TechPro Installation",
                    "professional_email": "pro@mydar.tn",
                    "professional_phone": "+216 98 765 432",
                    "message": "Bonjour, je suis disponible pour réaliser cette installation. J'ai une grande expérience dans les systèmes de vidéosurveillance pour villas. Je propose des caméras 4K Dahua avec NVR 8 canaux.",
                    "price_estimate": 2500.000,
                    "availability": "Disponible la semaine prochaine",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "published_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "client_name": "Mohamed Ben Salah",
            "client_email": "client@mydar.tn",
            "client_phone": "+216 55 111 222",
            "title": "Domotique éclairage appartement",
            "description": "Souhait de rendre connecté l'éclairage de mon appartement 4 pièces. Je voudrais pouvoir contrôler les lumières via smartphone et commande vocale Alexa. Environ 15 points lumineux à équiper.",
            "category": "Éclairage Connecté",
            "city": "Tunis",
            "address": "Les Berges du Lac 2",
            "status": "PUBLIEE",
            "responses": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "published_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "client_name": "Mohamed Ben Salah",
            "client_email": "client@mydar.tn",
            "client_phone": "+216 55 111 222",
            "title": "Installation alarme maison neuve",
            "description": "Construction d'une maison neuve et je souhaite installer un système d'alarme complet avant la fin des travaux. Besoin de détecteurs de mouvement, capteurs portes/fenêtres et sirène extérieure.",
            "category": "Système d'Alarme",
            "city": "Sousse",
            "address": "Cité Riadh, Sousse",
            "status": "EN_ATTENTE",
            "responses": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "client_name": "Mohamed Ben Salah",
            "client_email": "client@mydar.tn",
            "client_phone": "+216 55 111 222",
            "title": "Motorisation volets roulants",
            "description": "Je dispose de 6 volets roulants manuels que je souhaite motoriser et connecter. Je voudrais pouvoir les programmer automatiquement et les contrôler à distance.",
            "category": "Domotique",
            "city": "Sfax",
            "address": "Route de Tunis, Sfax",
            "status": "PUBLIEE",
            "responses": [
                {
                    "id": str(uuid.uuid4()),
                    "professional_id": pro_id,
                    "professional_name": "TechPro Installation",
                    "professional_email": "pro@mydar.tn",
                    "professional_phone": "+216 98 765 432",
                    "message": "Bonjour, je peux motoriser vos 6 volets avec des moteurs Somfy ou Tuya selon votre budget. Installation propre garantie avec programmation complète.",
                    "price_estimate": 1800.000,
                    "availability": "Disponible ce week-end",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "published_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "client_name": "Mohamed Ben Salah",
            "client_email": "client@mydar.tn",
            "client_phone": "+216 55 111 222",
            "title": "Installation serrure connectée portail",
            "description": "Je cherche à installer une serrure connectée sur mon portail principal avec possibilité d'ouverture via smartphone et vidéophone intégré.",
            "category": "Serrure Connectée",
            "city": "Hammamet",
            "address": "Zone Touristique, Hammamet",
            "status": "PUBLIEE",
            "responses": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "published_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "client_name": "Mohamed Ben Salah",
            "client_email": "client@mydar.tn",
            "client_phone": "+216 55 111 222",
            "title": "Réseau WiFi professionnel café",
            "description": "Nouveau café de 150m² avec terrasse, besoin d'un réseau WiFi performant pour clients et système de caisse. Couverture intérieure et extérieure requise.",
            "category": "Réseau WiFi/Câblage",
            "city": "Monastir",
            "address": "Avenue Habib Bourguiba, Monastir",
            "status": "ATTRIBUEE",
            "selected_response_id": None,
            "responses": [
                {
                    "id": str(uuid.uuid4()),
                    "professional_id": pro_id,
                    "professional_name": "TechPro Installation",
                    "professional_email": "pro@mydar.tn",
                    "professional_phone": "+216 98 765 432",
                    "message": "Je propose une solution mesh WiFi 6 avec 3 points d'accès pour une couverture optimale. Inclus: câblage, configuration réseau invité séparé.",
                    "price_estimate": 950.000,
                    "availability": "Installation sous 3 jours",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "published_at": datetime.now(timezone.utc).isoformat(),
            "closed_at": datetime.now(timezone.utc).isoformat()
        }
    ]

async def seed_database():
    """Seed the database with full test data"""
    print("🌱 Démarrage du remplissage de la base de données...")
    
    # Clear existing data
    collections = ["users", "categories", "products", "services", "annonces"]
    for coll in collections:
        await db[coll].delete_many({})
    print("✅ Données existantes supprimées")
    
    # Insert users
    await db.users.insert_many(USERS)
    print(f"✅ {len(USERS)} utilisateurs créés")
    
    # Insert categories
    await db.categories.insert_many(CATEGORIES)
    print(f"✅ {len(CATEGORIES)} catégories créées")
    
    # Insert products
    await db.products.insert_many(PRODUCTS)
    print(f"✅ {len(PRODUCTS)} produits créés")
    
    # Insert services
    await db.services.insert_many(SERVICES)
    print(f"✅ {len(SERVICES)} services créés")
    
    # Insert annonces
    annonces = create_annonces()
    await db.annonces.insert_many(annonces)
    print(f"✅ {len(annonces)} annonces créées")
    
    # Update category product counts
    for cat in CATEGORIES:
        count = await db.products.count_documents({"category": cat["name"]})
        await db.categories.update_one({"id": cat["id"]}, {"$set": {"product_count": count}})
    print("✅ Compteurs de catégories mis à jour")
    
    print("\n" + "="*50)
    print("🎉 Base de données remplie avec succès!")
    print("="*50)
    print("\n📧 COMPTES DE TEST:")
    print("-"*50)
    print("👑 ADMIN:        admin@mydar.tn / admin123")
    print("🔧 PROFESSIONNEL: pro@mydar.tn / pro123")  
    print("👤 PARTICULIER:   client@mydar.tn / client123")
    print("-"*50)

if __name__ == "__main__":
    asyncio.run(seed_database())
    client.close()
