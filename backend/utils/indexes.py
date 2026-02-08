"""
MongoDB Index Creation Script
Run this on startup to ensure optimal query performance
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


async def create_indexes(db: AsyncIOMotorDatabase):
    """Create all necessary indexes for optimal performance"""
    
    try:
        # Products indexes
        await db.products.create_index("id", unique=True)
        await db.products.create_index("category")
        await db.products.create_index("technology")
        await db.products.create_index("brand")
        await db.products.create_index("price")
        await db.products.create_index("is_featured")
        await db.products.create_index("name")
        # Compound index for common filter combinations
        await db.products.create_index([
            ("category", 1),
            ("technology", 1),
            ("brand", 1),
            ("price", 1)
        ])
        # Text index for search
        await db.products.create_index([
            ("name", "text"),
            ("description", "text")
        ], default_language="french")
        logger.info("Products indexes created")
        
        # Annonces indexes
        await db.annonces.create_index("id", unique=True)
        await db.annonces.create_index("status")
        await db.annonces.create_index("city")
        await db.annonces.create_index("category")
        await db.annonces.create_index("client_id")
        await db.annonces.create_index("created_at")
        await db.annonces.create_index("published_at")
        # Compound index for public annonces query
        await db.annonces.create_index([
            ("status", 1),
            ("city", 1),
            ("category", 1),
            ("published_at", -1)
        ])
        logger.info("Annonces indexes created")
        
        # Users indexes
        await db.users.create_index("id", unique=True)
        await db.users.create_index("email", unique=True)
        await db.users.create_index("role")
        logger.info("Users indexes created")
        
        # Purchase requests indexes
        await db.purchase_requests.create_index("id", unique=True)
        await db.purchase_requests.create_index("user_id")
        await db.purchase_requests.create_index("status")
        await db.purchase_requests.create_index("created_at")
        await db.purchase_requests.create_index([
            ("user_id", 1),
            ("status", 1),
            ("created_at", -1)
        ])
        logger.info("Purchase requests indexes created")
        
        # Categories indexes
        await db.categories.create_index("id", unique=True)
        # Make slug index sparse to allow null values
        await db.categories.create_index("slug", unique=True, sparse=True)
        logger.info("Categories indexes created")
        
        # Services indexes
        await db.services.create_index("id", unique=True)
        logger.info("Services indexes created")
        
        # Messages indexes
        await db.messages.create_index("id", unique=True)
        await db.messages.create_index("user_id")
        await db.messages.create_index("created_at")
        logger.info("Messages indexes created")
        
        # Appointments indexes
        await db.appointments.create_index("id", unique=True)
        await db.appointments.create_index("user_id")
        await db.appointments.create_index("date")
        await db.appointments.create_index("status")
        logger.info("Appointments indexes created")
        
        # Cart indexes
        await db.carts.create_index("user_id", unique=True)
        logger.info("Cart indexes created")
        
        # Favorites indexes
        await db.favorites.create_index("user_id", unique=True)
        logger.info("Favorites indexes created")
        
        # Reviews indexes
        await db.reviews.create_index("id", unique=True)
        await db.reviews.create_index("user_id")
        await db.reviews.create_index("target_type")
        await db.reviews.create_index("target_id")
        await db.reviews.create_index("created_at")
        await db.reviews.create_index([
            ("target_type", 1),
            ("target_id", 1),
            ("created_at", -1)
        ])
        # Unique constraint: one review per user per target
        await db.reviews.create_index(
            [("target_type", 1), ("target_id", 1), ("user_id", 1)],
            unique=True
        )
        logger.info("Reviews indexes created")
        
        logger.info("All MongoDB indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        # Don't raise - indexes are optimization, not critical
