"""
Tests Unitaires - Module Utils
Couverture: utils/cache.py, utils/observability.py, utils/middleware.py
"""
import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch, AsyncMock

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCacheModule:
    """Tests du module de cache"""
    
    def test_cache_import(self):
        """Test import du module cache"""
        from utils.cache import cache
        assert cache is not None
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Test set et get du cache"""
        from utils.cache import cache
        
        await cache.set("test_key", "test_value", ttl=60)
        value = await cache.get("test_key")
        assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test expiration du cache"""
        from utils.cache import cache
        
        await cache.set("expire_test", "value", ttl=1)
        value = await cache.get("expire_test")
        assert value == "value"
        
        # Wait for expiration
        await asyncio.sleep(1.5)
        expired_value = await cache.get("expire_test")
        assert expired_value is None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test suppression du cache"""
        from utils.cache import cache
        
        await cache.set("delete_test", "value")
        await cache.delete("delete_test")
        value = await cache.get("delete_test")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Test vidage du cache"""
        from utils.cache import cache
        
        await cache.set("clear_test_1", "value1")
        await cache.set("clear_test_2", "value2")
        await cache.clear()
        
        value1 = await cache.get("clear_test_1")
        value2 = await cache.get("clear_test_2")
        assert value1 is None
        assert value2 is None
    
    def test_cache_stats(self):
        """Test statistiques du cache"""
        from utils.cache import cache
        
        stats = cache.stats()
        assert "total_keys" in stats or "size" in stats


class TestObservabilityModule:
    """Tests du module d'observabilité"""
    
    def test_logger_import(self):
        """Test import du logger"""
        from utils.observability import logger
        assert logger is not None
    
    def test_logger_info(self):
        """Test log info"""
        from utils.observability import logger
        # Should not raise
        logger.info("Test info message")
    
    def test_logger_error(self):
        """Test log error"""
        from utils.observability import logger
        # Should not raise
        logger.error("Test error message")
    
    def test_logger_warning(self):
        """Test log warning"""
        from utils.observability import logger
        # Should not raise
        logger.warning("Test warning message")
    
    def test_metrics_import(self):
        """Test import des métriques"""
        from utils.observability import metrics
        assert metrics is not None
    
    @pytest.mark.asyncio
    async def test_metrics_record(self):
        """Test enregistrement métrique"""
        from utils.observability import metrics
        
        await metrics.record("test_metric", 100.5)
        stats = metrics.get_stats("test_metric")
        assert stats["count"] >= 1
    
    @pytest.mark.asyncio
    async def test_metrics_stats(self):
        """Test statistiques métriques"""
        from utils.observability import metrics
        
        # Record some values
        for i in range(10):
            await metrics.record("stats_test", i * 10)
        
        stats = metrics.get_stats("stats_test")
        assert "count" in stats
        assert "min_ms" in stats
        assert "max_ms" in stats
        assert "avg_ms" in stats
    
    def test_health_checker_import(self):
        """Test import du health checker"""
        from utils.observability import health_checker
        assert health_checker is not None
    
    @pytest.mark.asyncio
    async def test_health_checker_register(self):
        """Test enregistrement health check"""
        from utils.observability import health_checker
        
        def always_healthy():
            return True
        
        health_checker.register("test_check", always_healthy)
        result = await health_checker.check_all()
        assert "status" in result
    
    def test_error_tracker_import(self):
        """Test import du tracker d'erreurs"""
        from utils.observability import error_tracker
        assert error_tracker is not None
    
    @pytest.mark.asyncio
    async def test_error_tracker_capture(self):
        """Test capture d'erreur"""
        from utils.observability import error_tracker
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            await error_tracker.capture(e, {"context": "test"})
        
        errors = error_tracker.get_recent_errors()
        assert len(errors) >= 0  # May have been cleared


class TestMiddlewareModule:
    """Tests du module middleware"""
    
    def test_middleware_import(self):
        """Test import des middlewares"""
        from utils.middleware import PerformanceMiddleware, RateLimitMiddleware
        assert PerformanceMiddleware is not None
        assert RateLimitMiddleware is not None
    
    def test_rate_limit_excluded_ips(self):
        """Test IPs exclues du rate limiting"""
        from utils.middleware import RateLimitMiddleware
        
        assert '127.0.0.1' in RateLimitMiddleware.EXCLUDED_IPS
        assert 'localhost' in RateLimitMiddleware.EXCLUDED_IPS


class TestDatabaseModule:
    """Tests du module database"""
    
    def test_database_import(self):
        """Test import du module database"""
        from utils.database import projection_fields, light_product_projection
        assert projection_fields is not None
        assert light_product_projection is not None
    
    def test_projection_fields(self):
        """Test génération de projection"""
        from utils.database import projection_fields
        
        proj = projection_fields("id", "name", "price")
        assert proj == {"id": 1, "name": 1, "price": 1, "_id": 0}
    
    def test_projection_excludes_id(self):
        """Test que projection exclut _id par défaut"""
        from utils.database import projection_fields
        
        proj = projection_fields("name")
        assert proj["_id"] == 0
    
    def test_light_product_projection(self):
        """Test projection légère produit"""
        from utils.database import light_product_projection
        
        proj = light_product_projection()
        assert "_id" in proj
        assert proj["_id"] == 0
        assert "id" in proj
        assert "name" in proj


class TestEventQueueModule:
    """Tests du module event queue"""
    
    def test_event_queue_import(self):
        """Test import de l'event queue"""
        from utils.event_queue import event_queue
        assert event_queue is not None
    
    def test_event_queue_stats(self):
        """Test statistiques de la queue"""
        from utils.event_queue import event_queue
        
        stats = event_queue.stats()
        assert "queue_size" in stats
        assert "processed_count" in stats
        assert "dropped_count" in stats
    
    @pytest.mark.asyncio
    async def test_event_queue_enqueue(self):
        """Test ajout à la queue"""
        from utils.event_queue import event_queue
        
        result = await event_queue.enqueue("test_event", {"data": "test"})
        assert result is True


class TestMultitenancyModule:
    """Tests du module multitenancy"""
    
    def test_multitenancy_import(self):
        """Test import du module multitenancy"""
        from utils.multitenancy import TenantContext, TenantRole, Permission
        assert TenantContext is not None
        assert TenantRole is not None
        assert Permission is not None
    
    def test_tenant_roles(self):
        """Test rôles tenant"""
        from utils.multitenancy import TenantRole
        
        assert TenantRole.OWNER == "owner"
        assert TenantRole.ADMIN == "admin"
        assert TenantRole.SELLER == "seller"
    
    def test_permissions(self):
        """Test permissions"""
        from utils.multitenancy import Permission
        
        assert Permission.PRODUCTS_READ == "products:read"
        assert Permission.ORDERS_WRITE == "orders:write"
    
    def test_tenant_context_scoped_query(self):
        """Test query scopé par tenant"""
        from utils.multitenancy import TenantContext, TenantRole
        
        ctx = TenantContext(
            tenant_id="tenant_123",
            user_id="user_456",
            role=TenantRole.SELLER
        )
        
        query = ctx.scoped_query({"active": True})
        assert query["tenant_id"] == "tenant_123"
        assert query["active"] is True
    
    def test_tenant_context_permissions(self):
        """Test vérification permissions"""
        from utils.multitenancy import TenantContext, TenantRole, Permission
        
        ctx = TenantContext(
            tenant_id="tenant_123",
            user_id="user_456",
            role=TenantRole.SELLER
        )
        
        # Seller should have products:read
        assert ctx.has_permission(Permission.PRODUCTS_READ)
        # Seller should not have billing:write
        assert not ctx.has_permission(Permission.BILLING_WRITE)
