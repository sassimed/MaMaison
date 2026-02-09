"""
Multi-tenant Support for Marketplace
- Tenant isolation
- Access control
- Data scoping
"""

from typing import Optional, Dict, Any, List
from functools import wraps
from fastapi import HTTPException, Request, Depends
from enum import Enum


class TenantRole(str, Enum):
    """Tenant roles for access control"""
    OWNER = "owner"           # Full access to tenant data
    ADMIN = "admin"           # Admin access within tenant
    MANAGER = "manager"       # Can manage products, orders
    SELLER = "seller"         # Can list products, view own orders
    VIEWER = "viewer"         # Read-only access


class Permission(str, Enum):
    """Granular permissions"""
    # Products
    PRODUCTS_READ = "products:read"
    PRODUCTS_WRITE = "products:write"
    PRODUCTS_DELETE = "products:delete"
    
    # Orders
    ORDERS_READ = "orders:read"
    ORDERS_WRITE = "orders:write"
    ORDERS_MANAGE = "orders:manage"
    
    # Users
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_INVITE = "users:invite"
    
    # Analytics
    ANALYTICS_READ = "analytics:read"
    
    # Settings
    SETTINGS_READ = "settings:read"
    SETTINGS_WRITE = "settings:write"
    
    # Billing
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"


# Role-to-permissions mapping
ROLE_PERMISSIONS: Dict[TenantRole, List[Permission]] = {
    TenantRole.OWNER: list(Permission),  # All permissions
    
    TenantRole.ADMIN: [
        Permission.PRODUCTS_READ, Permission.PRODUCTS_WRITE, Permission.PRODUCTS_DELETE,
        Permission.ORDERS_READ, Permission.ORDERS_WRITE, Permission.ORDERS_MANAGE,
        Permission.USERS_READ, Permission.USERS_WRITE, Permission.USERS_INVITE,
        Permission.ANALYTICS_READ,
        Permission.SETTINGS_READ, Permission.SETTINGS_WRITE,
    ],
    
    TenantRole.MANAGER: [
        Permission.PRODUCTS_READ, Permission.PRODUCTS_WRITE,
        Permission.ORDERS_READ, Permission.ORDERS_WRITE, Permission.ORDERS_MANAGE,
        Permission.USERS_READ,
        Permission.ANALYTICS_READ,
        Permission.SETTINGS_READ,
    ],
    
    TenantRole.SELLER: [
        Permission.PRODUCTS_READ, Permission.PRODUCTS_WRITE,
        Permission.ORDERS_READ,
        Permission.SETTINGS_READ,
    ],
    
    TenantRole.VIEWER: [
        Permission.PRODUCTS_READ,
        Permission.ORDERS_READ,
        Permission.SETTINGS_READ,
    ],
}


class TenantContext:
    """
    Holds current tenant context for request
    """
    
    def __init__(
        self,
        tenant_id: str,
        user_id: str,
        role: TenantRole,
        permissions: List[Permission] = None
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.role = role
        self.permissions = permissions or ROLE_PERMISSIONS.get(role, [])
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if context has specific permission"""
        return permission in self.permissions
    
    def require_permission(self, permission: Permission):
        """Raise exception if permission is missing"""
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission.value}"
            )
    
    def scoped_query(self, query: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add tenant scope to a MongoDB query
        
        Usage:
            query = tenant.scoped_query({"status": "active"})
            # Returns: {"tenant_id": "xxx", "status": "active"}
        """
        base = {"tenant_id": self.tenant_id}
        if query:
            base.update(query)
        return base
    
    def scope_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add tenant_id to a document before insert
        
        Usage:
            doc = tenant.scope_document({"name": "Product"})
            # Returns: {"tenant_id": "xxx", "name": "Product"}
        """
        return {"tenant_id": self.tenant_id, **doc}


def require_tenant(permission: Permission = None):
    """
    Decorator to require tenant context and optionally a specific permission
    
    Usage:
        @router.get("/products")
        @require_tenant(Permission.PRODUCTS_READ)
        async def list_products(tenant: TenantContext = Depends(get_tenant_context)):
            query = tenant.scoped_query({"active": True})
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get tenant context from kwargs (injected by Depends)
            tenant = kwargs.get("tenant")
            if not tenant:
                raise HTTPException(status_code=401, detail="Tenant context required")
            
            # Check permission if specified
            if permission:
                tenant.require_permission(permission)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def get_tenant_context(request: Request) -> Optional[TenantContext]:
    """
    Dependency to extract tenant context from request
    In production, this would decode JWT and lookup tenant membership
    
    Usage:
        @router.get("/products")
        async def list_products(tenant: TenantContext = Depends(get_tenant_context)):
            ...
    """
    # Get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if not user:
        return None
    
    # Get tenant_id from header or user's default tenant
    tenant_id = request.headers.get("X-Tenant-ID") or user.get("default_tenant_id")
    if not tenant_id:
        return None
    
    # In production: lookup user's role in this tenant from database
    # For now, use user's global role
    role_str = user.get("role", "viewer").lower()
    role_map = {
        "admin": TenantRole.OWNER,
        "professionnel": TenantRole.SELLER,
        "particulier": TenantRole.VIEWER
    }
    role = role_map.get(role_str, TenantRole.VIEWER)
    
    return TenantContext(
        tenant_id=tenant_id,
        user_id=user.get("id"),
        role=role
    )


# ============ MULTI-TENANT INDEXES ============

TENANT_INDEXES = {
    "products": [
        {"keys": [("tenant_id", 1), ("id", 1)], "options": {"unique": True}},
        {"keys": [("tenant_id", 1), ("active", 1), ("category_id", 1)]},
        {"keys": [("tenant_id", 1), ("slug", 1)], "options": {"unique": True, "sparse": True}},
    ],
    "orders": [
        {"keys": [("tenant_id", 1), ("id", 1)], "options": {"unique": True}},
        {"keys": [("tenant_id", 1), ("user_id", 1), ("created_at", -1)]},
        {"keys": [("tenant_id", 1), ("status", 1), ("created_at", -1)]},
    ],
    "users": [
        {"keys": [("tenant_id", 1), ("id", 1)], "options": {"unique": True}},
        {"keys": [("tenant_id", 1), ("email", 1)], "options": {"unique": True}},
    ],
    "categories": [
        {"keys": [("tenant_id", 1), ("id", 1)], "options": {"unique": True}},
        {"keys": [("tenant_id", 1), ("slug", 1)], "options": {"unique": True}},
    ],
    "analytics_events": [
        {"keys": [("tenant_id", 1), ("timestamp", -1)]},
        {"keys": [("tenant_id", 1), ("event_type", 1), ("timestamp", -1)]},
    ],
}


async def ensure_tenant_indexes(db):
    """Create multi-tenant indexes"""
    from utils.observability import logger
    
    for collection_name, indexes in TENANT_INDEXES.items():
        collection = db[collection_name]
        
        for idx in indexes:
            try:
                await collection.create_index(idx["keys"], **idx.get("options", {}))
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Failed to create tenant index on {collection_name}: {str(e)}")
    
    logger.info("Multi-tenant indexes created")


# ============ TENANT UTILITIES ============

def tenant_scoped_collection(db, collection_name: str, tenant_id: str):
    """
    Get a collection wrapper that automatically scopes queries to tenant
    
    Usage:
        products = tenant_scoped_collection(db, "products", tenant_id)
        await products.find({"active": True}).to_list(100)
        # Automatically adds tenant_id to query
    """
    # This is a simplified version - in production, use a proper wrapper class
    collection = db[collection_name]
    
    # Store original methods
    original_find = collection.find
    original_find_one = collection.find_one
    original_count_documents = collection.count_documents
    
    # Create scoped versions
    def scoped_find(query=None, *args, **kwargs):
        scoped_query = {"tenant_id": tenant_id}
        if query:
            scoped_query.update(query)
        return original_find(scoped_query, *args, **kwargs)
    
    async def scoped_find_one(query=None, *args, **kwargs):
        scoped_query = {"tenant_id": tenant_id}
        if query:
            scoped_query.update(query)
        return await original_find_one(scoped_query, *args, **kwargs)
    
    async def scoped_count_documents(query=None, *args, **kwargs):
        scoped_query = {"tenant_id": tenant_id}
        if query:
            scoped_query.update(query)
        return await original_count_documents(scoped_query, *args, **kwargs)
    
    # Monkey-patch (not ideal, but simple for demo)
    collection.find = scoped_find
    collection.find_one = scoped_find_one
    collection.count_documents = scoped_count_documents
    
    return collection
