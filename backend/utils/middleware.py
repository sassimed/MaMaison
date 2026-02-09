"""
Performance Middleware for FastAPI
- Request timing and logging
- Compression
- Rate limiting
- Request ID tracking
"""

import time
import gzip
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import asyncio

from utils.observability import logger, metrics, request_context, error_tracker


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for performance monitoring
    - Adds request ID
    - Times requests
    - Logs slow requests
    - Records latency metrics
    """
    
    # Paths to skip logging (health checks, static files)
    SKIP_PATHS = {"/api/", "/api/health", "/api/metrics", "/favicon.ico"}
    
    # Slow request threshold (ms)
    SLOW_THRESHOLD_MS = 1000
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request_context.set("request_id", request_id)
        
        # Extract user ID from auth header if present
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In production, decode JWT to get user ID
            request_context.set("user_id", "authenticated")
        
        # Start timing
        start_time = time.perf_counter()
        
        # Get client info
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            # Record metrics
            path = request.url.path
            method = request.method
            status = response.status_code
            
            # Group paths for metrics (avoid high cardinality)
            metric_path = self._normalize_path(path)
            await metrics.record(f"http.{method}.{metric_path}", duration_ms, 
                               {"status": str(status)})
            
            # Log request (skip health checks)
            if path not in self.SKIP_PATHS:
                log_level = "warning" if duration_ms > self.SLOW_THRESHOLD_MS else "info"
                
                if log_level == "warning":
                    logger.warning(f"Slow request: {method} {path}",
                                  type="http_slow",
                                  method=method,
                                  path=path,
                                  status_code=status,
                                  duration_ms=round(duration_ms, 2),
                                  client_ip=client_ip,
                                  request_id=request_id)
                else:
                    logger.request(method, path, status, duration_ms,
                                  client_ip=client_ip,
                                  request_id=request_id)
            
            return response
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log error
            logger.error(f"Request error: {request.method} {request.url.path}",
                        type="http_error",
                        method=request.method,
                        path=request.url.path,
                        error=str(e),
                        duration_ms=round(duration_ms, 2),
                        request_id=request_id)
            
            # Track error
            await error_tracker.capture(e, {
                "path": request.url.path,
                "method": request.method,
                "client_ip": client_ip
            })
            
            raise
        finally:
            # Clean up request context
            request_context.clear()
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics (replace IDs with placeholders)"""
        parts = path.split("/")
        normalized = []
        for part in parts:
            # Replace UUIDs and long IDs
            if len(part) > 20 or (len(part) > 8 and "-" in part):
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Gzip compression for large responses
    Only compresses JSON responses > 1KB
    """
    
    MIN_SIZE = 1024  # 1KB
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if client accepts gzip
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding:
            return await call_next(request)
        
        response = await call_next(request)
        
        # Only compress JSON responses
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return response
        
        # Skip if already compressed
        if response.headers.get("Content-Encoding"):
            return response
        
        # Get response body
        if isinstance(response, StreamingResponse):
            return response
        
        # Read body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Only compress if large enough
        if len(body) < self.MIN_SIZE:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        # Compress
        compressed = gzip.compress(body, compresslevel=6)
        
        # Only use compressed if smaller
        if len(compressed) < len(body):
            headers = dict(response.headers)
            headers["Content-Encoding"] = "gzip"
            headers["Content-Length"] = str(len(compressed))
            
            return Response(
                content=compressed,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type
            )
        
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware
    Uses in-memory storage (use Redis in production for distributed)
    """
    
    # IPs to exclude from rate limiting (localhost, internal networks)
    EXCLUDED_IPS = {'127.0.0.1', 'localhost', '::1', '10.208.138.40'}
    
    def __init__(self, app, requests_per_minute: int = 100, burst: int = 20):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.burst = burst
        self._buckets: dict = {}
        self._lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for certain paths
        if request.url.path in ["/api/", "/api/health", "/api/metrics"]:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        
        # Skip rate limiting for localhost/internal IPs (for tests)
        if client_ip in self.EXCLUDED_IPS or client_ip.startswith('10.') or client_ip.startswith('127.'):
            return await call_next(request)
        
        # Check rate limit
        async with self._lock:
            now = time.time()
            bucket_key = f"{client_ip}"
            
            if bucket_key not in self._buckets:
                self._buckets[bucket_key] = {
                    "tokens": self.burst,
                    "last_update": now
                }
            
            bucket = self._buckets[bucket_key]
            
            # Refill tokens
            time_passed = now - bucket["last_update"]
            tokens_to_add = time_passed * (self.rpm / 60)
            bucket["tokens"] = min(self.burst, bucket["tokens"] + tokens_to_add)
            bucket["last_update"] = now
            
            # Check if request can proceed
            if bucket["tokens"] < 1:
                logger.warning(f"Rate limit exceeded for {client_ip}",
                              type="rate_limit",
                              client_ip=client_ip)
                
                return Response(
                    content='{"error": "Rate limit exceeded"}',
                    status_code=429,
                    headers={
                        "Content-Type": "application/json",
                        "Retry-After": "60"
                    }
                )
            
            # Consume token
            bucket["tokens"] -= 1
        
        return await call_next(request)
    
    async def cleanup(self):
        """Remove old buckets"""
        async with self._lock:
            now = time.time()
            expired = [k for k, v in self._buckets.items() 
                      if now - v["last_update"] > 300]
            for k in expired:
                del self._buckets[k]
