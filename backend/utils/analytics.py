"""
Analytics Utilities
Helpers for tracking events and managing analytics data
"""

import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import httpx
import asyncio

# IP Geolocation cache (to avoid too many API calls)
_geo_cache: Dict[str, Dict] = {}
_geo_cache_ttl = 3600  # 1 hour


async def get_ip_geolocation(ip: str) -> Dict[str, Any]:
    """Get geolocation data from IP address using ip-api.com"""
    if not ip or ip in ('127.0.0.1', 'localhost', '::1'):
        return {"country": "Local", "city": "Local", "region": ""}
    
    # Check cache
    if ip in _geo_cache:
        cached = _geo_cache[ip]
        if cached.get("_cached_at", 0) > datetime.now(timezone.utc).timestamp() - _geo_cache_ttl:
            return cached
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    result = {
                        "country": data.get("country", "Unknown"),
                        "city": data.get("city", "Unknown"),
                        "region": data.get("regionName", ""),
                        "isp": data.get("isp", ""),
                        "_cached_at": datetime.now(timezone.utc).timestamp()
                    }
                    _geo_cache[ip] = result
                    return result
    except Exception as e:
        print(f"[Analytics] Geolocation error for {ip}: {e}")
    
    return {"country": "Unknown", "city": "Unknown", "region": ""}


def generate_visitor_id(ip: str, user_agent: str, user_id: Optional[str] = None) -> str:
    """Generate a unique visitor ID based on device fingerprint"""
    if user_id:
        # If user is logged in, use their ID as base
        return f"user_{user_id}"
    
    # Create fingerprint from IP + User-Agent
    fingerprint = f"{ip}:{user_agent}"
    return f"anon_{hashlib.sha256(fingerprint.encode()).hexdigest()[:16]}"


def generate_session_id() -> str:
    """Generate a unique session ID"""
    return f"sess_{uuid.uuid4().hex[:16]}"


def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """Parse user agent string to extract device info"""
    ua = user_agent.lower() if user_agent else ""
    
    # Detect device type
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device_type = "mobile"
    elif "tablet" in ua or "ipad" in ua:
        device_type = "tablet"
    else:
        device_type = "desktop"
    
    # Detect browser
    if "chrome" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "edg" in ua:
        browser = "Edge"
    elif "opera" in ua or "opr" in ua:
        browser = "Opera"
    else:
        browser = "Other"
    
    # Detect OS
    if "windows" in ua:
        os = "Windows"
    elif "mac" in ua or "darwin" in ua:
        os = "macOS"
    elif "linux" in ua:
        os = "Linux"
    elif "android" in ua:
        os = "Android"
    elif "iphone" in ua or "ipad" in ua:
        os = "iOS"
    else:
        os = "Other"
    
    return {
        "device_type": device_type,
        "browser": browser,
        "os": os,
        "raw": user_agent[:200] if user_agent else ""
    }


def parse_referrer(referrer: str) -> Dict[str, str]:
    """Parse referrer URL to extract source info"""
    if not referrer:
        return {"source": "direct", "medium": "none", "referrer": ""}
    
    referrer_lower = referrer.lower()
    
    # Social media
    if "facebook" in referrer_lower or "fb.com" in referrer_lower:
        return {"source": "facebook", "medium": "social", "referrer": referrer}
    elif "instagram" in referrer_lower:
        return {"source": "instagram", "medium": "social", "referrer": referrer}
    elif "twitter" in referrer_lower or "t.co" in referrer_lower:
        return {"source": "twitter", "medium": "social", "referrer": referrer}
    elif "linkedin" in referrer_lower:
        return {"source": "linkedin", "medium": "social", "referrer": referrer}
    elif "tiktok" in referrer_lower:
        return {"source": "tiktok", "medium": "social", "referrer": referrer}
    
    # Search engines
    elif "google" in referrer_lower:
        return {"source": "google", "medium": "organic", "referrer": referrer}
    elif "bing" in referrer_lower:
        return {"source": "bing", "medium": "organic", "referrer": referrer}
    elif "yahoo" in referrer_lower:
        return {"source": "yahoo", "medium": "organic", "referrer": referrer}
    elif "duckduckgo" in referrer_lower:
        return {"source": "duckduckgo", "medium": "organic", "referrer": referrer}
    
    # Other
    else:
        # Extract domain
        try:
            from urllib.parse import urlparse
            domain = urlparse(referrer).netloc
            return {"source": domain, "medium": "referral", "referrer": referrer}
        except:
            return {"source": "other", "medium": "referral", "referrer": referrer}


def parse_utm_params(url: str) -> Dict[str, str]:
    """Extract UTM parameters from URL"""
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        return {
            "utm_source": params.get("utm_source", [""])[0],
            "utm_medium": params.get("utm_medium", [""])[0],
            "utm_campaign": params.get("utm_campaign", [""])[0],
            "utm_term": params.get("utm_term", [""])[0],
            "utm_content": params.get("utm_content", [""])[0]
        }
    except:
        return {}


# Event types
class EventType:
    PAGE_VIEW = "page_view"
    PRODUCT_VIEW = "product_view"
    SEARCH = "search"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    CHECKOUT_START = "checkout_start"
    CHECKOUT_COMPLETE = "checkout_complete"
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    CLICK = "click"
    ERROR = "error"
    CHAT_START = "chat_start"
    CHAT_MESSAGE = "chat_message"
