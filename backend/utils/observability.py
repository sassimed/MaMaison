"""
Performance Monitoring & Observability Module
Structured logging, latency metrics, and request tracing
"""

import time
import logging
import json
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
from functools import wraps
from contextlib import asynccontextmanager
import traceback
import os

# ============ STRUCTURED LOGGER ============

class StructuredLogger:
    """JSON structured logger for observability"""
    
    def __init__(self, name: str = "mydar"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add JSON handler
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
        
        self.name = name
    
    def _log(self, level: str, message: str, **extra):
        """Internal log method with structured data"""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self.name,
            "level": level,
            "message": message,
            **extra
        }
        
        if level == "error":
            self.logger.error(json.dumps(log_data))
        elif level == "warning":
            self.logger.warning(json.dumps(log_data))
        elif level == "debug":
            self.logger.debug(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))
    
    def info(self, message: str, **extra):
        self._log("info", message, **extra)
    
    def error(self, message: str, **extra):
        self._log("error", message, **extra)
    
    def warning(self, message: str, **extra):
        self._log("warning", message, **extra)
    
    def debug(self, message: str, **extra):
        self._log("debug", message, **extra)
    
    def request(self, method: str, path: str, status: int, duration_ms: float, **extra):
        """Log HTTP request with latency"""
        self._log("info", f"{method} {path} {status}", 
                  type="http_request",
                  method=method,
                  path=path,
                  status_code=status,
                  duration_ms=round(duration_ms, 2),
                  **extra)
    
    def db_query(self, collection: str, operation: str, duration_ms: float, **extra):
        """Log database query with latency"""
        self._log("info", f"DB {operation} on {collection}",
                  type="db_query",
                  collection=collection,
                  operation=operation,
                  duration_ms=round(duration_ms, 2),
                  **extra)
    
    def cache_hit(self, key: str):
        """Log cache hit"""
        self._log("debug", f"Cache HIT: {key[:50]}...", type="cache", hit=True, key=key[:100])
    
    def cache_miss(self, key: str):
        """Log cache miss"""
        self._log("debug", f"Cache MISS: {key[:50]}...", type="cache", hit=False, key=key[:100])


class JsonFormatter(logging.Formatter):
    """JSON log formatter"""
    def format(self, record):
        return record.getMessage()


# Global logger instance
logger = StructuredLogger("mydar")


# ============ LATENCY METRICS ============

class LatencyMetrics:
    """Collect and expose latency metrics"""
    
    def __init__(self, max_samples: int = 1000):
        self._metrics: Dict[str, list] = {}
        self._max_samples = max_samples
        self._lock = asyncio.Lock()
    
    async def record(self, metric_name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a latency measurement"""
        async with self._lock:
            if metric_name not in self._metrics:
                self._metrics[metric_name] = []
            
            self._metrics[metric_name].append({
                "value": duration_ms,
                "timestamp": time.time(),
                "tags": tags or {}
            })
            
            # Keep only recent samples
            if len(self._metrics[metric_name]) > self._max_samples:
                self._metrics[metric_name] = self._metrics[metric_name][-self._max_samples:]
    
    def get_stats(self, metric_name: str, window_seconds: int = 300) -> Dict[str, Any]:
        """Get statistics for a metric"""
        if metric_name not in self._metrics:
            return {"count": 0}
        
        now = time.time()
        recent = [m["value"] for m in self._metrics[metric_name] 
                  if now - m["timestamp"] <= window_seconds]
        
        if not recent:
            return {"count": 0}
        
        sorted_values = sorted(recent)
        count = len(recent)
        
        return {
            "count": count,
            "min_ms": round(sorted_values[0], 2),
            "max_ms": round(sorted_values[-1], 2),
            "avg_ms": round(sum(recent) / count, 2),
            "p50_ms": round(sorted_values[count // 2], 2),
            "p95_ms": round(sorted_values[int(count * 0.95)] if count > 1 else sorted_values[0], 2),
            "p99_ms": round(sorted_values[int(count * 0.99)] if count > 1 else sorted_values[0], 2),
        }
    
    def get_all_stats(self, window_seconds: int = 300) -> Dict[str, Any]:
        """Get statistics for all metrics"""
        return {name: self.get_stats(name, window_seconds) for name in self._metrics.keys()}


# Global metrics instance
metrics = LatencyMetrics()


# ============ PERFORMANCE DECORATORS ============

def timed_async(metric_name: str = None, log: bool = True):
    """
    Decorator to time async functions and record metrics
    
    Usage:
        @timed_async("db.products.find")
        async def find_products():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            start = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                
                # Record metric
                await metrics.record(name, duration_ms)
                
                # Log if slow (> 500ms)
                if log and duration_ms > 500:
                    logger.warning(f"Slow function: {name}", 
                                   duration_ms=round(duration_ms, 2),
                                   type="slow_function")
                
                return result
            
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.error(f"Error in {name}: {str(e)}",
                            duration_ms=round(duration_ms, 2),
                            error=str(e),
                            traceback=traceback.format_exc()[:500])
                raise
        
        return wrapper
    return decorator


@asynccontextmanager
async def timed_block(name: str):
    """
    Context manager for timing code blocks
    
    Usage:
        async with timed_block("heavy_computation"):
            await do_something()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        await metrics.record(name, duration_ms)


# ============ REQUEST CONTEXT ============

class RequestContext:
    """Store request-scoped data for tracing"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any):
        self._data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
    
    def clear(self):
        self._data.clear()
    
    @property
    def request_id(self) -> Optional[str]:
        return self._data.get("request_id")
    
    @property
    def user_id(self) -> Optional[str]:
        return self._data.get("user_id")


# Global request context (use contextvars in production for thread-safety)
request_context = RequestContext()


# ============ ERROR TRACKING (Sentry-like) ============

class ErrorTracker:
    """Simple error tracking and aggregation"""
    
    def __init__(self, max_errors: int = 100):
        self._errors: list = []
        self._max_errors = max_errors
        self._lock = asyncio.Lock()
        self._error_counts: Dict[str, int] = {}
    
    async def capture(self, error: Exception, context: Dict[str, Any] = None):
        """Capture an error"""
        async with self._lock:
            error_type = type(error).__name__
            error_msg = str(error)
            
            # Increment error count
            key = f"{error_type}:{error_msg[:50]}"
            self._error_counts[key] = self._error_counts.get(key, 0) + 1
            
            # Store error details
            error_data = {
                "type": error_type,
                "message": error_msg,
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": context or {},
                "request_id": request_context.request_id,
                "user_id": request_context.user_id,
                "count": self._error_counts[key]
            }
            
            self._errors.append(error_data)
            
            # Keep only recent errors
            if len(self._errors) > self._max_errors:
                self._errors = self._errors[-self._max_errors:]
            
            # Log error
            logger.error(f"Exception: {error_type}: {error_msg[:100]}",
                        type="exception",
                        error_type=error_type,
                        error_message=error_msg[:200],
                        count=self._error_counts[key])
    
    def get_recent_errors(self, limit: int = 20) -> list:
        """Get recent errors"""
        return self._errors[-limit:]
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get error counts by type"""
        return dict(sorted(self._error_counts.items(), key=lambda x: -x[1])[:20])
    
    def clear(self):
        """Clear error history"""
        self._errors.clear()
        self._error_counts.clear()


# Global error tracker
error_tracker = ErrorTracker()


# ============ HEALTH CHECK ============

class HealthChecker:
    """System health checker"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
    
    def register(self, name: str, check_func: Callable):
        """Register a health check"""
        self.checks[name] = check_func
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                start = time.perf_counter()
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                duration_ms = (time.perf_counter() - start) * 1000
                
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "duration_ms": round(duration_ms, 2)
                }
                if not result:
                    overall_healthy = False
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e)
                }
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global health checker
health_checker = HealthChecker()
