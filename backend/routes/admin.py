from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import User, UserRole
from models.service_request import ServiceRequest, ServiceRequestUpdate, RequestStatus
from models.appointment import Appointment, AppointmentStatus
from models.product import Product
from models.service import Service
from models.message import Message, MessageType
from utils.dependencies import get_db, require_role
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from passlib.context import CryptContext
import uuid
import random

router = APIRouter(prefix="/admin", tags=["Admin"])

# Dependency for admin only
admin_required = require_role([UserRole.ADMIN])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==================== SEED DATA ROUTE ====================

@router.post("/seed-database")
async def seed_database(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Seed the database with test data (Admin only)"""
    
    results = {"users": 0, "categories": 0, "products": 0, "services": 0, "annonces": 0}
    
    # Check if already seeded
    existing_products = await db.products.count_documents({})
    if existing_products > 100:
        return {"message": "Database already seeded", "products": existing_products}
    
    # ============ USERS ============
    existing_users = await db.users.count_documents({})
    if existing_users < 3:
        users = [
            {
                "id": str(uuid.uuid4()),
                "email": "admin@mydar.tn",
                "full_name": "Administrateur MyDar",
                "phone": "+216 70 123 456",
                "address": "Centre Urbain Nord, Tunis",
                "role": "ADMIN",
                "is_active": True,
                "is_email_verified": True,
                "hashed_password": pwd_context.hash("admin123"),
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
                "hashed_password": pwd_context.hash("pro123"),
                "loyalty_points": 150,
                "total_spent": 2500.000,
                "company_info": {
                    "company_name": "TechPro Installation SARL",
                    "siret": "12345678901234",
                    "address": "Zone Industrielle, Sousse 4000",
                    "technical_contact": "Ahmed Ben Ali",
                    "website": "https://techpro-installation.tn",
                    "sites": []
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
                "hashed_password": pwd_context.hash("client123"),
                "loyalty_points": 75,
                "total_spent": 850.500,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for user in users:
            existing = await db.users.find_one({"email": user["email"]})
            if not existing:
                await db.users.insert_one(user)
                results["users"] += 1
    
    # ============ CATEGORIES ============
    categories = [
        {"id": str(uuid.uuid4()), "name": "Vidéosurveillance", "description": "Caméras IP, NVR, et accessoires", "icon": "Camera", "product_count": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Alarme", "description": "Systèmes d'alarme et détecteurs", "icon": "Bell", "product_count": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Éclairage", "description": "Ampoules connectées et LED", "icon": "Lightbulb", "product_count": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Module", "description": "Modules et hubs domotique", "icon": "Cpu", "product_count": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Interrupteur", "description": "Interrupteurs intelligents", "icon": "ToggleRight", "product_count": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Prise", "description": "Prises connectées", "icon": "Plug", "product_count": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Volet", "description": "Motorisation volets", "icon": "Blinds", "product_count": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Écran", "description": "Écrans tactiles et contrôle", "icon": "Monitor", "product_count": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
    ]
    
    existing_cats = await db.categories.count_documents({})
    if existing_cats < 5:
        await db.categories.delete_many({})
        await db.categories.insert_many(categories)
        results["categories"] = len(categories)
    
    # ============ SERVICES ============
    services = [
        {"id": "videophone", "name": "Vidéophone", "slug": "videophone", "description": "Contrôle d'accès vidéo", "icon": "Video", "category": "security", "featured": True},
        {"id": "lighting", "name": "Éclairage Intelligent", "slug": "eclairage", "description": "Automatisation éclairage", "icon": "Lightbulb", "category": "automation", "featured": True},
        {"id": "alarm", "name": "Système d'Alarme", "slug": "alarme", "description": "Protection domicile", "icon": "Bell", "category": "security", "featured": True},
        {"id": "video-surveillance", "name": "Vidéosurveillance", "slug": "videosurveillance", "description": "Caméras HD/4K", "icon": "Camera", "category": "security", "featured": True},
        {"id": "shutters", "name": "Volets Connectés", "slug": "volets", "description": "Centralisation volets", "icon": "Blinds", "category": "automation", "featured": False},
        {"id": "network", "name": "Réseau & Câblage", "slug": "reseau", "description": "WiFi et câblage", "icon": "Wifi", "category": "network", "featured": False},
    ]
    
    existing_services = await db.services.count_documents({})
    if existing_services < 5:
        await db.services.delete_many({})
        await db.services.insert_many(services)
        results["services"] = len(services)
    
    # ============ PRODUCTS (Generate many) ============
    marques = ["Tuya", "Sonoff", "Aqara", "Shelly", "Dahua", "Hikvision", "Xiaomi", "TP-Link", "Ezviz", "Innr"]
    technologies = ["WiFi", "Zigbee", "WiFi/Zigbee", "Z-Wave", "Bluetooth"]
    cats_list = ["Vidéosurveillance", "Alarme", "Éclairage", "Module", "Interrupteur", "Prise", "Volet", "Écran"]
    
    product_templates = {
        "Vidéosurveillance": [("Caméra Dôme", 150, 350), ("Caméra Bullet Extérieure", 180, 400), ("NVR Enregistreur", 300, 600), ("Caméra PTZ", 250, 500)],
        "Alarme": [("Kit Alarme Complet", 250, 500), ("Détecteur Mouvement", 25, 60), ("Sirène Intérieure", 35, 80), ("Détecteur Ouverture", 15, 40)],
        "Éclairage": [("Ampoule LED RGBW E27", 15, 35), ("Ruban LED RGB", 35, 90), ("Spot Encastrable", 25, 55), ("Plafonnier LED", 60, 150)],
        "Module": [("Hub Zigbee 3.0", 60, 120), ("Module Relais WiFi", 35, 80), ("Passerelle IR", 25, 50), ("Module Mesure Énergie", 45, 100)],
        "Interrupteur": [("Interrupteur Tactile", 40, 90), ("Variateur Connecté", 55, 110), ("Bouton Scène", 25, 50)],
        "Prise": [("Prise Connectée", 20, 45), ("Multiprise Intelligente", 50, 110), ("Prise Extérieure IP44", 30, 65)],
        "Volet": [("Module Volet Roulant", 40, 85), ("Moteur Tubulaire", 90, 200), ("Télécommande 16CH", 60, 130)],
        "Écran": [("Écran Tactile Mural", 120, 280), ("Interphone Vidéo", 150, 350), ("Thermostat Écran", 130, 280)],
    }
    
    existing_prods = await db.products.count_documents({})
    if existing_prods < 100:
        products = []
        for i in range(1000):
            cat = random.choice(cats_list)
            templates = product_templates.get(cat, [("Produit", 50, 200)])
            name_base, price_min, price_max = random.choice(templates)
            marque = random.choice(marques)
            tech = random.choice(technologies)
            
            products.append({
                "id": str(uuid.uuid4()),
                "name": f"{name_base} {marque} {random.choice(['Pro', 'Plus', 'Max', 'Lite', ''])}".strip(),
                "description": f"Produit {cat.lower()} de qualité professionnelle. Technologie {tech}.",
                "brand": marque,
                "technology": tech,
                "category": cat,
                "image_url": f"https://picsum.photos/seed/{uuid.uuid4().hex[:8]}/500/500",
                "gallery_images": [],
                "compatibility": random.sample(["Alexa", "Google Home", "HomeKit", "SmartThings", "IFTTT"], k=random.randint(2, 4)),
                "usage": "Usage résidentiel et professionnel",
                "price": round(random.uniform(price_min, price_max), 3),
                "featured": random.random() > 0.9,
                "stock_quantity": random.randint(0, 100),
            })
        
        await db.products.delete_many({})
        for i in range(0, len(products), 100):
            await db.products.insert_many(products[i:i+100])
        results["products"] = len(products)
    
    # ============ ANNONCES (Generate many) ============
    villes = ["Tunis", "Sfax", "Sousse", "Ariana", "Ben Arous", "La Marsa", "Hammamet", "Nabeul", "Monastir", "Bizerte", "Gabès", "Kairouan", "Mahdia", "Médenine", "Kasserine", "Gafsa", "Tozeur", "Sidi Bouzid", "Le Kef", "Jendouba"]
    categories_ann = ["Installation Caméra", "Système d'Alarme", "Domotique", "Éclairage Connecté", "Serrure Connectée", "Réseau WiFi/Câblage", "Autre"]
    statuts = ["EN_ATTENTE", "PUBLIEE", "PUBLIEE", "PUBLIEE", "ATTRIBUEE", "CLOTUREE"]
    
    titles = [
        "Installation vidéosurveillance", "Système d'alarme maison", "Domotique appartement",
        "Éclairage connecté salon", "Serrure connectée portail", "Réseau WiFi villa",
        "Caméras extérieures", "Détecteurs mouvement", "Motorisation volets",
        "Interphone vidéo", "Contrôle accès bureau", "Installation domotique complète"
    ]
    
    existing_ann = await db.annonces.count_documents({})
    if existing_ann < 100:
        # Get client user
        client = await db.users.find_one({"role": "PARTICULIER"})
        pro = await db.users.find_one({"role": "PROFESSIONNEL"})
        
        if client and pro:
            annonces = []
            for i in range(1000):
                status = random.choice(statuts)
                created = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90))
                
                annonce = {
                    "id": str(uuid.uuid4()),
                    "client_id": client["id"],
                    "client_name": client["full_name"],
                    "client_email": client["email"],
                    "client_phone": f"+216 {random.randint(20, 99)} {random.randint(100, 999)} {random.randint(100, 999)}",
                    "title": f"{random.choice(titles)} {random.choice(villes)}",
                    "description": f"Recherche professionnel pour {random.choice(titles).lower()}. Surface environ {random.randint(50, 300)}m².",
                    "category": random.choice(categories_ann),
                    "city": random.choice(villes),
                    "address": f"Quartier {random.choice(['Centre', 'Nord', 'Sud', 'Est', 'Ouest'])}, {random.choice(villes)}",
                    "status": status,
                    "responses": [],
                    "created_at": created.isoformat(),
                    "updated_at": created.isoformat(),
                }
                
                if status in ["PUBLIEE", "ATTRIBUEE", "CLOTUREE"]:
                    annonce["published_at"] = created.isoformat()
                    if random.random() > 0.5:
                        annonce["responses"] = [{
                            "id": str(uuid.uuid4()),
                            "professional_id": pro["id"],
                            "professional_name": pro["full_name"],
                            "professional_email": pro["email"],
                            "professional_phone": pro.get("phone", ""),
                            "message": "Je suis disponible pour ce projet.",
                            "price_estimate": random.randint(200, 3000),
                            "availability": "Disponible cette semaine",
                            "created_at": created.isoformat()
                        }]
                
                annonces.append(annonce)
            
            await db.annonces.delete_many({})
            for i in range(0, len(annonces), 100):
                await db.annonces.insert_many(annonces[i:i+100])
            results["annonces"] = len(annonces)
    
    # Update category counts
    for cat in cats_list:
        count = await db.products.count_documents({"category": cat})
        await db.categories.update_one({"name": cat}, {"$set": {"product_count": count}})
    
    return {
        "message": "Database seeded successfully",
        "results": results,
        "credentials": {
            "admin": "admin@mydar.tn / admin123",
            "pro": "pro@mydar.tn / pro123",
            "client": "client@mydar.tn / client123"
        }
    }


# ==================== DASHBOARD ====================

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get dashboard statistics"""
    # Count users by role
    total_users = await db.users.count_documents({})
    particuliers = await db.users.count_documents({"role": "PARTICULIER"})
    professionnels = await db.users.count_documents({"role": "PROFESSIONNEL"})
    
    # Count requests by status
    pending_requests = await db.service_requests.count_documents({"status": RequestStatus.PENDING.value})
    in_progress_requests = await db.service_requests.count_documents({"status": RequestStatus.IN_PROGRESS.value})
    total_requests = await db.service_requests.count_documents({})
    
    # Count appointments by status
    pending_appointments = await db.appointments.count_documents({"status": AppointmentStatus.PENDING.value})
    confirmed_appointments = await db.appointments.count_documents({"status": AppointmentStatus.CONFIRMED.value})
    total_appointments = await db.appointments.count_documents({})
    
    # Count unread messages
    unread_messages = await db.messages.count_documents({
        "message_type": MessageType.USER_TO_ADMIN.value,
        "is_read": False
    })
    
    # Products count
    total_products = await db.products.count_documents({})
    
    return {
        "users": {
            "total": total_users,
            "particuliers": particuliers,
            "professionnels": professionnels
        },
        "requests": {
            "total": total_requests,
            "pending": pending_requests,
            "in_progress": in_progress_requests
        },
        "appointments": {
            "total": total_appointments,
            "pending": pending_appointments,
            "confirmed": confirmed_appointments
        },
        "messages": {
            "unread": unread_messages
        },
        "products": {
            "total": total_products
        }
    }


# ==================== USERS ====================

@router.get("/users")
async def get_all_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all users with optional filters"""
    query = {}
    if role:
        query["role"] = role.value
    if is_active is not None:
        query["is_active"] = is_active
    
    users = await db.users.find(query, {"_id": 0, "hashed_password": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Convert datetime strings to ISO format
    result = []
    for user in users:
        user_dict = dict(user)
        if isinstance(user_dict.get('created_at'), str):
            pass  # Already a string, keep as is
        elif user_dict.get('created_at'):
            user_dict['created_at'] = user_dict['created_at'].isoformat()
        if isinstance(user_dict.get('updated_at'), str):
            pass
        elif user_dict.get('updated_at'):
            user_dict['updated_at'] = user_dict['updated_at'].isoformat()
        result.append(user_dict)
    
    return result


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific user"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user_dict = dict(user)
    if user_dict.get('created_at') and not isinstance(user_dict.get('created_at'), str):
        user_dict['created_at'] = user_dict['created_at'].isoformat()
    if user_dict.get('updated_at') and not isinstance(user_dict.get('updated_at'), str):
        user_dict['updated_at'] = user_dict['updated_at'].isoformat()
    
    return user_dict


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update user's role"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": new_role.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"message": f"Rôle mis à jour: {new_role.value}"}


@router.patch("/users/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    is_active: bool,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Activate or deactivate a user"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    status_text = "activé" if is_active else "désactivé"
    return {"message": f"Utilisateur {status_text}"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")
    
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"message": "Utilisateur supprimé"}


# ==================== SERVICE REQUESTS ====================

@router.get("/requests", response_model=List[ServiceRequest])
async def get_all_requests(
    status_filter: Optional[RequestStatus] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all service requests"""
    query = {}
    if status_filter:
        query["status"] = status_filter.value
    
    requests = await db.service_requests.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for req in requests:
        if isinstance(req.get('created_at'), str):
            req['created_at'] = datetime.fromisoformat(req['created_at'])
        if isinstance(req.get('updated_at'), str):
            req['updated_at'] = datetime.fromisoformat(req['updated_at'])
    
    return requests


@router.get("/requests/{request_id}", response_model=ServiceRequest)
async def get_request_admin(
    request_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific service request"""
    request = await db.service_requests.find_one({"id": request_id}, {"_id": 0})
    if not request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    if isinstance(request.get('created_at'), str):
        request['created_at'] = datetime.fromisoformat(request['created_at'])
    if isinstance(request.get('updated_at'), str):
        request['updated_at'] = datetime.fromisoformat(request['updated_at'])
    
    return ServiceRequest(**request)


@router.patch("/requests/{request_id}")
async def update_request(
    request_id: str,
    update_data: ServiceRequestUpdate,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a service request"""
    update_dict = {k: v.value if hasattr(v, 'value') else v for k, v in update_data.model_dump().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
    
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.service_requests.update_one(
        {"id": request_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    return {"message": "Demande mise à jour"}


# ==================== APPOINTMENTS ====================

@router.get("/appointments", response_model=List[Appointment])
async def get_all_appointments(
    status_filter: Optional[AppointmentStatus] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all appointments"""
    query = {}
    if status_filter:
        query["status"] = status_filter.value
    
    appointments = await db.appointments.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for apt in appointments:
        if isinstance(apt.get('created_at'), str):
            apt['created_at'] = datetime.fromisoformat(apt['created_at'])
    
    return appointments


@router.patch("/appointments/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: str,
    new_status: AppointmentStatus,
    meet_link: Optional[str] = None,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update appointment status"""
    update_data = {"status": new_status.value}
    if meet_link:
        update_data["meet_link"] = meet_link
    
    result = await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    
    return {"message": f"Statut mis à jour: {new_status.value}"}


@router.delete("/appointments/{appointment_id}")
async def delete_appointment(
    appointment_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete an appointment"""
    result = await db.appointments.delete_one({"id": appointment_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    
    return {"message": "Rendez-vous supprimé"}


# ==================== PRODUCTS ====================

@router.get("/products", response_model=List[Product])
async def get_all_products_admin(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all products"""
    products = await db.products.find({}, {"_id": 0}).to_list(200)
    return products


@router.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: dict,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new product"""
    product_data['id'] = str(uuid.uuid4())
    await db.products.insert_one(product_data)
    
    # Remove _id before returning
    product_data.pop('_id', None)
    return Product(**product_data)


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    product_data: dict,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a product"""
    product_data.pop('id', None)  # Don't update ID
    product_data.pop('_id', None)
    
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": product_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    return {"message": "Produit mis à jour"}


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a product"""
    result = await db.products.delete_one({"id": product_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    return {"message": "Produit supprimé"}


# ==================== SERVICES ====================

@router.get("/services", response_model=List[Service])
async def get_all_services_admin(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all services"""
    services = await db.services.find({}, {"_id": 0}).to_list(50)
    return services


@router.post("/services", response_model=Service, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: dict,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new service"""
    service_data['id'] = str(uuid.uuid4())
    await db.services.insert_one(service_data)
    
    service_data.pop('_id', None)
    return Service(**service_data)


@router.put("/services/{service_id}")
async def update_service(
    service_id: str,
    service_data: dict,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a service"""
    service_data.pop('id', None)
    service_data.pop('_id', None)
    
    result = await db.services.update_one(
        {"id": service_id},
        {"$set": service_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Service non trouvé")
    
    return {"message": "Service mis à jour"}


@router.delete("/services/{service_id}")
async def delete_service(
    service_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a service"""
    result = await db.services.delete_one({"id": service_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Service non trouvé")
    
    return {"message": "Service supprimé"}


# ==================== MESSAGES ====================

@router.get("/messages/conversations")
async def get_all_conversations(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all message conversations"""
    pipeline = [
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": "$conversation_id",
            "subject": {"$first": "$subject"},
            "user_id": {"$first": "$sender_id"},
            "user_name": {"$first": "$sender_name"},
            "last_message_at": {"$first": "$created_at"},
            "messages": {"$push": "$$ROOT"}
        }},
        {"$project": {
            "id": "$_id",
            "subject": 1,
            "user_id": 1,
            "user_name": 1,
            "last_message_at": 1,
            "unread_count": {
                "$size": {
                    "$filter": {
                        "input": "$messages",
                        "cond": {"$and": [
                            {"$eq": ["$$this.is_read", False]},
                            {"$eq": ["$$this.message_type", MessageType.USER_TO_ADMIN.value]}
                        ]}
                    }
                }
            }
        }},
        {"$sort": {"last_message_at": -1}}
    ]
    
    conversations = await db.messages.aggregate(pipeline).to_list(100)
    return conversations


@router.post("/messages/reply/{conversation_id}")
async def admin_reply(
    conversation_id: str,
    content: str = Query(...),
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Admin reply to a conversation"""
    # Get original conversation
    original = await db.messages.find_one({"conversation_id": conversation_id}, {"_id": 0})
    
    if not original:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        sender_name=current_user.full_name,
        sender_role="ADMIN",
        recipient_id=original['sender_id'],
        subject=f"Re: {original['subject']}",
        content=content,
        message_type=MessageType.ADMIN_TO_USER,
        related_request_id=original.get('related_request_id')
    )
    
    doc = message.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.messages.insert_one(doc)
    
    return {"message": "Réponse envoyée"}


# ==================== CATEGORIES ====================

@router.get("/categories")
async def get_all_categories(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all categories with product count (new structure with label/slug)"""
    # Get only root categories (level 1)
    root_cats = await db.categories.find({"level": 1}, {"_id": 0}).to_list(100)
    
    result = []
    for cat in root_cats:
        # Get MongoDB ID for parent reference (subcategories use this as parent_id)
        cat_mongo_id = cat.get("id")  # This is the MongoDB ObjectId stored as string
        cat_slug = cat.get("slug", "")
        
        # Get subcategories - search by MongoDB ID or slug for compatibility
        subcats = await db.categories.find(
            {"$or": [{"parent_id": cat_mongo_id}, {"parent_id": cat_slug}]}, 
            {"_id": 0}
        ).to_list(50)
        
        # Calculate total product count
        total_count = cat.get("product_count", 0)
        for sub in subcats:
            total_count += sub.get("product_count", 0)
        
        result.append({
            "id": cat.get("slug"),  # Use slug as id for compatibility
            "name": cat.get("label"),  # Alias for frontend compatibility
            "label": cat.get("label"),
            "slug": cat.get("slug"),
            "description": cat.get("description", ""),
            "icon": cat.get("icon", "shield"),  # Default icon
            "image_url": cat.get("image_url", ""),
            "product_count": total_count,
            "subcategories": [
                {
                    "id": s.get("slug"),
                    "name": s.get("label"),
                    "label": s.get("label"),
                    "slug": s.get("slug"),
                    "icon": s.get("icon", "shield"),  # Default icon for subcategory
                    "product_count": s.get("product_count", 0)
                }
                for s in subcats
            ],
            "created_at": cat.get("created_at"),
            "updated_at": cat.get("updated_at")
        })
    
    return result


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: dict,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new category (root level)"""
    label = category_data.get('name') or category_data.get('label')
    if not label:
        raise HTTPException(status_code=400, detail="Le nom est requis")
    
    # Generate slug
    slug = label.lower().replace(' ', '-').replace("'", '-').replace('é', 'e').replace('à', 'a')
    
    # Check if category already exists
    existing = await db.categories.find_one({"slug": slug})
    if existing:
        raise HTTPException(status_code=400, detail="Cette catégorie existe déjà")
    
    new_cat = {
        "label": label,
        "slug": slug,
        "parent_id": None,
        "level": 1,
        "path_ids": [slug],
        "is_active": True,
        "description": category_data.get("description", ""),
        "icon": category_data.get("icon", ""),
        "image_url": category_data.get("image_url", ""),
        "product_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.categories.insert_one(new_cat)
    new_cat.pop('_id', None)
    new_cat['id'] = slug
    new_cat['name'] = label
    
    return new_cat


@router.put("/categories/{category_id}")
async def update_category(
    category_id: str,
    category_data: dict,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a category and its subcategories"""
    # Find by slug (used as id)
    old_category = await db.categories.find_one({"slug": category_id}, {"_id": 0})
    if not old_category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    
    update_fields = {"updated_at": datetime.now(timezone.utc)}
    
    # Update label if provided
    new_label = category_data.get('name') or category_data.get('label')
    if new_label and new_label != old_category.get('label'):
        update_fields['label'] = new_label
        # Update category_label on products
        await db.products.update_many(
            {"category_label": old_category.get('label')},
            {"$set": {"category_label": new_label}}
        )
    
    if 'description' in category_data:
        update_fields['description'] = category_data['description']
    if 'icon' in category_data:
        update_fields['icon'] = category_data['icon'] or 'shield'  # Default icon
    if 'image_url' in category_data:
        update_fields['image_url'] = category_data['image_url']
    
    await db.categories.update_one(
        {"slug": category_id},
        {"$set": update_fields}
    )
    
    # Handle subcategories if provided
    if 'subcategories' in category_data:
        subcategories = category_data['subcategories']
        
        # Get existing subcategories
        existing_subcats = await db.categories.find(
            {"parent_id": category_id},
            {"_id": 0}
        ).to_list(100)
        existing_slugs = {s['slug'] for s in existing_subcats}
        
        # Track which subcategories to keep
        new_slugs = set()
        
        for subcat in subcategories:
            subcat_label = subcat.get('name') or subcat.get('label')
            if not subcat_label:
                continue
                
            subcat_slug = subcat_label.lower().replace(' ', '-').replace("'", '-').replace('é', 'e').replace('à', 'a').replace('è', 'e')
            subcat_full_slug = f"{category_id}__{subcat_slug}"
            new_slugs.add(subcat_full_slug)
            
            subcat_icon = subcat.get('icon') or 'shield'  # Default icon
            
            if subcat_full_slug in existing_slugs or subcat.get('id') in existing_slugs:
                # Update existing subcategory
                actual_slug = subcat.get('id') if subcat.get('id') in existing_slugs else subcat_full_slug
                new_slugs.add(actual_slug)
                await db.categories.update_one(
                    {"slug": actual_slug},
                    {"$set": {
                        "label": subcat_label,
                        "icon": subcat_icon,
                        "updated_at": datetime.now(timezone.utc)
                    }}
                )
                # Update products with new subcategory label
                await db.products.update_many(
                    {"category_id": actual_slug},
                    {"$set": {"subcategory_label": subcat_label}}
                )
            else:
                # Create new subcategory
                new_subcat = {
                    "label": subcat_label,
                    "slug": subcat_full_slug,
                    "parent_id": category_id,
                    "level": 2,
                    "path_ids": [category_id, subcat_full_slug],
                    "is_active": True,
                    "icon": subcat_icon,
                    "product_count": 0,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                await db.categories.insert_one(new_subcat)
        
        # Don't delete subcategories that have products - just skip them
        for existing in existing_subcats:
            if existing['slug'] not in new_slugs:
                # Check if it has products
                product_count = existing.get('product_count', 0)
                if product_count == 0:
                    await db.categories.delete_one({"slug": existing['slug']})
    
    return {"message": "Catégorie mise à jour"}


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a category"""
    category = await db.categories.find_one({"slug": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    
    # Check if category has products
    product_count = await db.products.count_documents({
        "$or": [
            {"category_label": category.get('label')},
            {"category_path_ids": category_id}
        ]
    })
    if product_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de supprimer: {product_count} produits utilisent cette catégorie"
        )
    
    # Delete subcategories first
    await db.categories.delete_many({"parent_id": category_id})
    # Delete the category itself
    await db.categories.delete_one({"slug": category_id})
    
    return {"message": "Catégorie supprimée"}


# ==================== PURCHASE REQUESTS ====================

@router.get("/purchase-requests")
async def get_all_purchase_requests(
    status: Optional[str] = None,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all purchase requests with optional status filter"""
    query = {}
    if status:
        query["status"] = status
    
    requests = await db.purchase_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return requests


@router.get("/purchase-requests/{request_id}")
async def get_purchase_request(
    request_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific purchase request"""
    request = await db.purchase_requests.find_one({"id": request_id}, {"_id": 0})
    if not request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    return request


@router.patch("/purchase-requests/{request_id}")
async def update_purchase_request_status(
    request_id: str,
    update_data: dict,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update purchase request status and/or admin notes"""
    request = await db.purchase_requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    old_status = request.get("status")
    new_status = update_data.get("status")
    
    update_fields = {"updated_at": datetime.now(timezone.utc)}
    
    if "status" in update_data:
        valid_statuses = ["EN_ATTENTE", "EN_COURS", "VALIDEE", "REFUSEE"]
        if update_data["status"] not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs acceptées: {valid_statuses}")
        update_fields["status"] = update_data["status"]
    
    if "admin_notes" in update_data:
        update_fields["admin_notes"] = update_data["admin_notes"]
    
    await db.purchase_requests.update_one(
        {"id": request_id},
        {"$set": update_fields}
    )
    
    # Credit loyalty points when status changes to VALIDEE
    if new_status == "VALIDEE" and old_status != "VALIDEE":
        user_id = request.get("user_id")
        final_total = request.get("final_total") or request.get("total_estimated", 0)
        
        if user_id and final_total > 0:
            # 1 point per dinar spent
            points_earned = int(final_total)
            
            await db.users.update_one(
                {"id": user_id},
                {
                    "$inc": {
                        "loyalty_points": points_earned,
                        "total_spent": final_total
                    }
                }
            )
            
            # Store points earned in the request
            await db.purchase_requests.update_one(
                {"id": request_id},
                {"$set": {"points_earned": points_earned}}
            )
    
    return {"message": "Demande mise à jour"}


@router.delete("/purchase-requests/{request_id}")
async def delete_purchase_request(
    request_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a purchase request"""
    result = await db.purchase_requests.delete_one({"id": request_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    return {"message": "Demande supprimée"}


@router.get("/purchase-requests/stats/summary")
async def get_purchase_requests_stats(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get purchase requests statistics"""
    total = await db.purchase_requests.count_documents({})
    pending = await db.purchase_requests.count_documents({"status": "EN_ATTENTE"})
    in_progress = await db.purchase_requests.count_documents({"status": "EN_COURS"})
    validated = await db.purchase_requests.count_documents({"status": "VALIDEE"})
    refused = await db.purchase_requests.count_documents({"status": "REFUSEE"})
    
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "validated": validated,
        "refused": refused
    }


# ==================== SALES STATISTICS ====================

def make_aware(dt):
    """Make datetime timezone-aware if it's naive"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

@router.get("/statistics/sales")
async def get_sales_statistics(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get comprehensive sales statistics"""
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Only count validated purchase requests for revenue
    validated_requests = await db.purchase_requests.find({"status": "VALIDEE"}).to_list(1000)
    
    # Total revenue
    total_revenue = sum(r.get("total_estimated", 0) or 0 for r in validated_requests)
    
    # Today's revenue
    today_revenue = 0
    month_revenue = 0
    today_orders = 0
    month_orders = 0
    
    for r in validated_requests:
        created_at = make_aware(r.get("created_at"))
        amount = r.get("total_estimated", 0) or 0
        if created_at:
            if created_at >= today_start:
                today_revenue += amount
                today_orders += 1
            if created_at >= month_start:
                month_revenue += amount
                month_orders += 1
    
    # Revenue by day (last 30 days)
    daily_revenue = {}
    for i in range(30):
        day = (today_start - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_revenue[day] = 0
    
    for r in validated_requests:
        created_at = r.get("created_at")
        if created_at:
            day = created_at.strftime("%Y-%m-%d")
            if day in daily_revenue:
                daily_revenue[day] += r.get("total_estimated", 0) or 0
    
    # Revenue by month (last 12 months)
    monthly_revenue = {}
    for i in range(12):
        month = (now - timedelta(days=i*30)).strftime("%Y-%m")
        monthly_revenue[month] = 0
    
    for r in validated_requests:
        created_at = r.get("created_at")
        if created_at:
            month = created_at.strftime("%Y-%m")
            if month in monthly_revenue:
                monthly_revenue[month] += r.get("total_estimated", 0) or 0
    
    # Total orders count
    total_orders = len(validated_requests)
    
    return {
        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "month_revenue": month_revenue,
        "total_orders": total_orders,
        "today_orders": today_orders,
        "month_orders": month_orders,
        "daily_revenue": [{"date": k, "revenue": v} for k, v in sorted(daily_revenue.items())],
        "monthly_revenue": [{"month": k, "revenue": v} for k, v in sorted(monthly_revenue.items())]
    }


@router.get("/statistics/best-sellers")
async def get_best_sellers(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db),
    limit: int = Query(default=10, le=50)
):
    """Get best selling products"""
    # Get all validated purchase requests
    validated_requests = await db.purchase_requests.find({"status": "VALIDEE"}).to_list(1000)
    
    # Count product sales
    product_sales = {}
    product_revenue = {}
    
    for request in validated_requests:
        for item in request.get("items", []):
            pid = item.get("product_id")
            qty = item.get("quantity", 0)
            price = item.get("product_price", 0) or 0
            
            if pid:
                product_sales[pid] = product_sales.get(pid, 0) + qty
                product_revenue[pid] = product_revenue.get(pid, 0) + (qty * price)
    
    # Get product details and sort by sales
    best_sellers = []
    for pid, qty_sold in sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:limit]:
        product = await db.products.find_one({"id": pid})
        if product:
            best_sellers.append({
                "product_id": pid,
                "name": product.get("name"),
                "category": product.get("category"),
                "image_url": product.get("image_url"),
                "price": product.get("price"),
                "quantity_sold": qty_sold,
                "revenue": product_revenue.get(pid, 0),
                "stock_quantity": product.get("stock_quantity", 0)
            })
    
    return best_sellers


@router.get("/statistics/inventory")
async def get_inventory_statistics(
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get inventory/stock statistics"""
    products = await db.products.find({}, {"_id": 0}).to_list(1000)
    
    total_products = len(products)
    out_of_stock = len([p for p in products if p.get("stock_quantity", 0) == 0])
    low_stock = len([p for p in products if 0 < p.get("stock_quantity", 0) <= 5])
    in_stock = len([p for p in products if p.get("stock_quantity", 0) > 5])
    
    total_stock_value = sum(
        (p.get("price") or 0) * p.get("stock_quantity", 0) 
        for p in products
    )
    
    total_items_in_stock = sum(p.get("stock_quantity", 0) for p in products)
    
    # Products by stock status
    products_by_stock = {
        "out_of_stock": [
            {"id": p["id"], "name": p["name"], "category": p.get("category"), "stock": 0}
            for p in products if p.get("stock_quantity", 0) == 0
        ][:10],
        "low_stock": [
            {"id": p["id"], "name": p["name"], "category": p.get("category"), "stock": p.get("stock_quantity", 0)}
            for p in products if 0 < p.get("stock_quantity", 0) <= 5
        ][:10]
    }
    
    # Stock by category
    stock_by_category = {}
    for p in products:
        cat = p.get("category", "Autre")
        if cat not in stock_by_category:
            stock_by_category[cat] = {"count": 0, "total_stock": 0, "value": 0}
        stock_by_category[cat]["count"] += 1
        stock_by_category[cat]["total_stock"] += p.get("stock_quantity", 0)
        stock_by_category[cat]["value"] += (p.get("price") or 0) * p.get("stock_quantity", 0)
    
    return {
        "total_products": total_products,
        "out_of_stock": out_of_stock,
        "low_stock": low_stock,
        "in_stock": in_stock,
        "total_stock_value": total_stock_value,
        "total_items_in_stock": total_items_in_stock,
        "products_by_stock": products_by_stock,
        "stock_by_category": [
            {"category": k, **v} for k, v in stock_by_category.items()
        ]
    }


# ==================== INVOICE GENERATION ====================

from fastapi.responses import Response

@router.post("/purchase-requests/{request_id}/generate-invoice")
async def generate_invoice(
    request_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Generate invoice for a purchase request and store it in database"""
    from services.invoice_service import generate_invoice_pdf, invoice_to_base64
    
    # Get purchase request
    request = await db.purchase_requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    # Get user details
    user = await db.users.find_one({"id": request.get("user_id")})
    
    # Generate invoice number
    invoice_count = await db.invoices.count_documents({})
    invoice_number = f"SL{str(invoice_count + 1).zfill(5)}"
    
    # Prepare invoice data
    discount = request.get("discount", 0)
    invoice_data = {
        "invoice_number": invoice_number,
        "date": datetime.now(timezone.utc),
        "client_name": user.get("full_name") if user else request.get("user_name", "N/A"),
        "client_email": user.get("email") if user else request.get("user_email", ""),
        "client_phone": user.get("phone") if user else request.get("user_phone", ""),
        "client_address": user.get("address_details") if user else {},
        "items": [
            {
                "product_name": item.get("product_name"),
                "quantity": item.get("quantity", 1),
                "unit_price": item.get("product_price", 0),
                "total": (item.get("product_price", 0) or 0) * item.get("quantity", 1)
            }
            for item in request.get("items", [])
        ],
        "total": request.get("total_estimated", 0),
        "discount": discount,
        "status": request.get("status", "EN_ATTENTE")
    }
    
    # Generate PDF
    pdf_bytes = generate_invoice_pdf(invoice_data)
    pdf_base64 = invoice_to_base64(pdf_bytes)
    
    # Store invoice in database
    invoice_record = {
        "id": str(uuid.uuid4()),
        "invoice_number": invoice_number,
        "purchase_request_id": request_id,
        "user_id": request.get("user_id"),
        "pdf_data": pdf_base64,
        "total_ht": request.get("total_estimated", 0),
        "total_ttc": request.get("total_estimated", 0) * 1.2,
        "created_at": datetime.now(timezone.utc),
        "created_by": current_user.id
    }
    
    # Check if invoice already exists for this request
    existing = await db.invoices.find_one({"purchase_request_id": request_id})
    if existing:
        # Update existing invoice
        await db.invoices.update_one(
            {"purchase_request_id": request_id},
            {"$set": {
                "pdf_data": pdf_base64,
                "invoice_number": existing.get("invoice_number"),  # Keep original number
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        invoice_record["invoice_number"] = existing.get("invoice_number")
    else:
        await db.invoices.insert_one(invoice_record)
    
    # Update purchase request with invoice reference
    await db.purchase_requests.update_one(
        {"id": request_id},
        {"$set": {
            "invoice_id": invoice_record["id"],
            "invoice_number": invoice_record["invoice_number"],
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {
        "message": "Facture générée avec succès",
        "invoice_number": invoice_record["invoice_number"],
        "invoice_id": invoice_record["id"]
    }


@router.get("/purchase-requests/{request_id}/invoice")
async def download_invoice_admin(
    request_id: str,
    current_user: User = Depends(admin_required),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Download invoice PDF for a purchase request (admin)"""
    from services.invoice_service import base64_to_invoice
    
    invoice = await db.invoices.find_one({"purchase_request_id": request_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    pdf_bytes = base64_to_invoice(invoice["pdf_data"])
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="facture_{invoice["invoice_number"]}.pdf"'
        }
    )
