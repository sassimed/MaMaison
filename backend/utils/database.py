"""
Optimized MongoDB Connection Manager
- Connection pooling
- Read/Write separation ready
- Health monitoring
- Query optimization helpers
"""

import os
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ReadPreference, WriteConcern
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import asyncio

from utils.observability import logger, health_checker


class MongoDBManager:
    """
    Optimized MongoDB connection manager
    - Configurable connection pool
    - Read preference support
    - Write concern configuration
    - Health monitoring
    """
    
    def __init__(
        self,
        mongo_url: str,
        db_name: str,
        min_pool_size: int = 10,
        max_pool_size: int = 100,
        max_idle_time_ms: int = 30000,
        server_selection_timeout_ms: int = 5000,
        connect_timeout_ms: int = 10000,
        socket_timeout_ms: int = 30000
    ):
        self.mongo_url = mongo_url
        self.db_name = db_name
        
        # Connection options optimized for high traffic
        self.options = {
            "minPoolSize": min_pool_size,
            "maxPoolSize": max_pool_size,
            "maxIdleTimeMS": max_idle_time_ms,
            "serverSelectionTimeoutMS": server_selection_timeout_ms,
            "connectTimeoutMS": connect_timeout_ms,
            "socketTimeoutMS": socket_timeout_ms,
            "retryWrites": True,
            "retryReads": True,
            "w": "majority",  # Write concern for durability
            "journal": True,
            "compressors": ["zstd", "snappy", "zlib"],  # Network compression
        }
        
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._analytics_db: Optional[AsyncIOMotorDatabase] = None
        
    async def connect(self):
        """Initialize connection"""
        if self._client is not None:
            return
        
        try:
            self._client = AsyncIOMotorClient(self.mongo_url, **self.options)
            self._db = self._client[self.db_name]
            
            # Test connection
            await self._client.admin.command('ping')
            
            logger.info("MongoDB connected successfully",
                       type="db_connect",
                       db_name=self.db_name,
                       pool_size=self.options["maxPoolSize"])
            
            # Register health check
            health_checker.register("mongodb", self.health_check)
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            raise
    
    async def disconnect(self):
        """Close connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB disconnected")
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get main database"""
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db
    
    @property
    def client(self) -> AsyncIOMotorClient:
        """Get client for advanced operations"""
        if self._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._client
    
    def get_collection(self, name: str, read_preference: str = "primary"):
        """
        Get collection with specific read preference
        
        read_preference options:
        - "primary": Read from primary (default, for consistency)
        - "secondary": Read from secondary (for read scaling)
        - "nearest": Read from nearest (for low latency)
        """
        rp_map = {
            "primary": ReadPreference.PRIMARY,
            "secondary": ReadPreference.SECONDARY_PREFERRED,
            "nearest": ReadPreference.NEAREST
        }
        
        rp = rp_map.get(read_preference, ReadPreference.PRIMARY)
        return self.db.get_collection(name, read_preference=rp)
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            await self._client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self._client:
            return {"status": "disconnected"}
        
        # Get server info
        try:
            topology = self._client.topology_description
            servers = []
            for server in topology.server_descriptions().values():
                servers.append({
                    "address": f"{server.address[0]}:{server.address[1]}",
                    "server_type": server.server_type.name,
                    "round_trip_time": server.round_trip_time
                })
            
            return {
                "status": "connected",
                "topology_type": topology.topology_type.name,
                "servers": servers,
                "min_pool_size": self.options["minPoolSize"],
                "max_pool_size": self.options["maxPoolSize"]
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ============ QUERY OPTIMIZATION HELPERS ============

def projection_fields(*fields: str) -> Dict[str, int]:
    """
    Create a projection dict for specific fields
    Always excludes _id unless explicitly included
    
    Usage:
        projection = projection_fields("id", "name", "price")
        # Returns: {"id": 1, "name": 1, "price": 1, "_id": 0}
    """
    proj = {field: 1 for field in fields}
    if "_id" not in fields:
        proj["_id"] = 0
    return proj


def light_product_projection() -> Dict[str, int]:
    """Standard light projection for product listings"""
    return {
        "_id": 0,
        "id": 1,
        "name": 1,
        "price": 1,
        "primary_image_url": 1,
        "brand": 1,
        "category_label": 1,
        "subcategory_label": 1,
        "model_code": 1,
        "in_stock": 1
    }


def full_product_projection() -> Dict[str, int]:
    """Full projection for product detail page"""
    return {"_id": 0}  # Exclude only _id


# ============ INDEX RECOMMENDATIONS ============

RECOMMENDED_INDEXES = {
    "products": [
        # Primary lookups
        {"keys": [("id", 1)], "options": {"unique": True}},
        {"keys": [("slug", 1)], "options": {"unique": True, "sparse": True}},
        {"keys": [("model_code", 1)], "options": {"sparse": True}},
        
        # Category filtering (compound for common queries)
        {"keys": [("active", 1), ("category_path_ids", 1), ("ranking.quality_score", -1)]},
        {"keys": [("active", 1), ("category_id", 1), ("ranking.quality_score", -1)]},
        
        # Faceted search
        {"keys": [("active", 1), ("brand", 1)]},
        {"keys": [("active", 1), ("attributes_norm.connectivity", 1)]},
        {"keys": [("active", 1), ("price", 1)]},
        
        # Text search
        {"keys": [("name", "text"), ("description", "text"), ("search.keywords", "text")],
         "options": {"default_language": "french", "name": "products_text_idx"}}
    ],
    
    "orders": [
        {"keys": [("id", 1)], "options": {"unique": True}},
        {"keys": [("user_id", 1), ("created_at", -1)]},
        {"keys": [("status", 1), ("created_at", -1)]},
        {"keys": [("tenant_id", 1), ("created_at", -1)]},  # Multi-tenant ready
    ],
    
    "users": [
        {"keys": [("id", 1)], "options": {"unique": True}},
        {"keys": [("email", 1)], "options": {"unique": True}},
        {"keys": [("tenant_id", 1)]},  # Multi-tenant ready
        {"keys": [("role", 1)]},
    ],
    
    "analytics_events": [
        {"keys": [("timestamp", -1)]},
        {"keys": [("event_type", 1), ("timestamp", -1)]},
        {"keys": [("session_id", 1)]},
        {"keys": [("user_id", 1), ("timestamp", -1)]},
        {"keys": [("product_id", 1), ("timestamp", -1)]},
        # TTL index for auto-cleanup (90 days)
        {"keys": [("timestamp", 1)], "options": {"expireAfterSeconds": 7776000}}
    ],
    
    "analytics_sessions": [
        {"keys": [("session_id", 1)], "options": {"unique": True}},
        {"keys": [("last_seen", -1)]},
        {"keys": [("visitor_id", 1)]},
    ]
}


async def ensure_indexes(db: AsyncIOMotorDatabase, collections: List[str] = None):
    """
    Create recommended indexes for specified collections
    
    Usage:
        await ensure_indexes(db)  # All collections
        await ensure_indexes(db, ["products", "orders"])  # Specific collections
    """
    target_collections = collections or list(RECOMMENDED_INDEXES.keys())
    
    for collection_name in target_collections:
        if collection_name not in RECOMMENDED_INDEXES:
            continue
        
        collection = db[collection_name]
        indexes = RECOMMENDED_INDEXES[collection_name]
        
        for idx in indexes:
            try:
                keys = idx["keys"]
                options = idx.get("options", {})
                
                # Convert to list of tuples if dict
                if isinstance(keys, dict):
                    keys = list(keys.items())
                
                await collection.create_index(keys, **options)
                logger.debug(f"Index created: {collection_name}.{keys}")
                
            except Exception as e:
                # Index might already exist
                if "already exists" not in str(e).lower():
                    logger.warning(f"Failed to create index on {collection_name}: {str(e)}")
    
    logger.info(f"Indexes ensured for collections: {target_collections}")


# ============ GLOBAL INSTANCE ============

# Will be initialized in server.py
db_manager: Optional[MongoDBManager] = None


def get_db() -> AsyncIOMotorDatabase:
    """Get database instance (for dependency injection)"""
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return db_manager.db


def get_db_manager() -> MongoDBManager:
    """Get database manager instance"""
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return db_manager
