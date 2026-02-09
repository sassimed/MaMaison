"""
Analytics API Routes
Endpoints for tracking events and retrieving analytics data

PERFORMANCE OPTIMIZATIONS:
- Fire-and-forget tracking (never blocks the caller)
- Batched writes via async queue
- Lightweight response for /track endpoint
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from dotenv import load_dotenv

from utils.analytics import (
    generate_visitor_id, generate_session_id, parse_user_agent,
    parse_referrer, parse_utm_params, get_ip_geolocation, EventType
)
from utils.event_queue import event_queue
from utils.observability import logger, metrics

load_dotenv()

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Online users TTL (5 minutes by default)
ONLINE_USER_TTL_MINUTES = 5


# ============ PYDANTIC MODELS ============

class TrackEventRequest(BaseModel):
    event_type: str = Field(..., description="Type of event (page_view, click, etc.)")
    page_url: str = Field(..., description="Current page URL")
    page_title: Optional[str] = None
    referrer: Optional[str] = None
    session_id: Optional[str] = None
    visitor_id: Optional[str] = None
    user_id: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    search_query: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class HeartbeatRequest(BaseModel):
    session_id: str
    visitor_id: Optional[str] = None
    user_id: Optional[str] = None
    current_page: Optional[str] = None


# ============ ASYNC EVENT PROCESSING ============

async def process_track_event_async(event_doc: Dict[str, Any]):
    """
    Process tracking event asynchronously
    This runs in background, never blocks the HTTP response
    """
    try:
        # Insert event
        await db.analytics_events.insert_one(event_doc)
        
        # Update session
        session_id = event_doc.get("session_id")
        if session_id:
            await db.analytics_sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "visitor_id": event_doc.get("visitor_id"),
                        "user_id": event_doc.get("user_id"),
                        "last_seen": event_doc.get("timestamp"),
                        "last_page": event_doc.get("page_url"),
                        "device": event_doc.get("device"),
                        "geo": event_doc.get("geo")
                    },
                    "$setOnInsert": {
                        "created_at": event_doc.get("timestamp"),
                        "referrer": event_doc.get("referrer"),
                        "utm": event_doc.get("utm"),
                        "ip": event_doc.get("ip")
                    },
                    "$inc": {"page_views": 1 if event_doc.get("event_type") == EventType.PAGE_VIEW else 0}
                },
                upsert=True
            )
        
        # Update online users if logged in
        user_id = event_doc.get("user_id")
        if user_id:
            await db.online_users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "last_seen": event_doc.get("timestamp"),
                        "current_page": event_doc.get("page_url"),
                        "session_id": session_id,
                        "visitor_id": event_doc.get("visitor_id")
                    }
                },
                upsert=True
            )
        
        await metrics.record("analytics.event_processed", 1, {"type": event_doc.get("event_type")})
        
    except Exception as e:
        logger.error(f"Error processing analytics event: {str(e)}")


# ============ TRACKING ENDPOINTS ============

@router.post("/track")
async def track_event(event: TrackEventRequest, request: Request, background_tasks: BackgroundTasks):
    """
    Track an analytics event
    
    PERFORMANCE: This endpoint is optimized for speed:
    - Returns immediately after basic validation
    - Event processing happens in background
    - Never blocks the caller
    """
    # Get client info (fast operations only)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    
    user_agent = request.headers.get("User-Agent", "")
    
    # Generate IDs if not provided
    visitor_id = event.visitor_id or generate_visitor_id(client_ip, user_agent, event.user_id)
    session_id = event.session_id or generate_session_id()
    
    # Parse user agent (fast, no I/O)
    device_info = parse_user_agent(user_agent)
    
    # Parse referrer (fast, no I/O)
    referrer_info = parse_referrer(event.referrer)
    
    # Build event document
    event_doc = {
        "event_type": event.event_type,
        "timestamp": datetime.now(timezone.utc),
        "session_id": session_id,
        "visitor_id": visitor_id,
        "user_id": event.user_id,
        "page_url": event.page_url,
        "page_title": event.page_title,
        "referrer": referrer_info,
        "utm": {
            "source": event.utm_source,
            "medium": event.utm_medium,
            "campaign": event.utm_campaign
        },
        "device": device_info,
        "ip": client_ip,
        "product_id": event.product_id,
        "product_name": event.product_name,
        "search_query": event.search_query,
        "metadata": event.metadata or {}
    }
    
    # Fire-and-forget: Add to background tasks (non-blocking)
    # This returns immediately while processing continues in background
    background_tasks.add_task(process_track_event_with_geo, event_doc, client_ip)
    
    # Return immediately with minimal response
    return {
        "success": True,
        "session_id": session_id,
        "visitor_id": visitor_id
    }


async def process_track_event_with_geo(event_doc: Dict[str, Any], client_ip: str):
    """Process event with geolocation lookup (slow operation done in background)"""
    try:
        # Get geolocation (this is slow, ~100-500ms)
        geo_info = await get_ip_geolocation(client_ip)
        event_doc["geo"] = geo_info
        
        # Now process the full event
        await process_track_event_async(event_doc)
    except Exception as e:
        logger.error(f"Error in background event processing: {str(e)}")


@router.post("/track/batch")
async def track_events_batch(events: List[TrackEventRequest], request: Request, background_tasks: BackgroundTasks):
    """
    Track multiple events in a single request (for offline sync)
    """
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    
    user_agent = request.headers.get("User-Agent", "")
    device_info = parse_user_agent(user_agent)
    
    event_docs = []
    for event in events[:100]:  # Limit batch size
        visitor_id = event.visitor_id or generate_visitor_id(client_ip, user_agent, event.user_id)
        session_id = event.session_id or generate_session_id()
        
        event_docs.append({
            "event_type": event.event_type,
            "timestamp": datetime.now(timezone.utc),
            "session_id": session_id,
            "visitor_id": visitor_id,
            "user_id": event.user_id,
            "page_url": event.page_url,
            "page_title": event.page_title,
            "referrer": parse_referrer(event.referrer),
            "utm": {
                "source": event.utm_source,
                "medium": event.utm_medium,
                "campaign": event.utm_campaign
            },
            "device": device_info,
            "ip": client_ip,
            "product_id": event.product_id,
            "product_name": event.product_name,
            "search_query": event.search_query,
            "metadata": event.metadata or {}
        })
    
    # Process batch in background
    background_tasks.add_task(process_batch_events, event_docs)
    
    return {"success": True, "queued": len(event_docs)}


async def process_batch_events(events: List[Dict[str, Any]]):
    """Process batch of events"""
    try:
        if events:
            await db.analytics_events.insert_many(events, ordered=False)
            logger.info(f"Batch inserted {len(events)} analytics events")
    except Exception as e:
        logger.error(f"Error in batch event processing: {str(e)}")


@router.post("/heartbeat")
async def heartbeat(data: HeartbeatRequest, request: Request):
    """Keep session alive and update online status"""
    now = datetime.now(timezone.utc)
    
    # Update session
    await db.analytics_sessions.update_one(
        {"session_id": data.session_id},
        {
            "$set": {
                "last_seen": now,
                "last_page": data.current_page
            }
        }
    )
    
    # Update online users if logged in
    if data.user_id:
        await db.online_users.update_one(
            {"user_id": data.user_id},
            {
                "$set": {
                    "last_seen": now,
                    "current_page": data.current_page,
                    "session_id": data.session_id
                }
            },
            upsert=True
        )
    
    return {"success": True}


@router.post("/end-session")
async def end_session(session_id: str):
    """Mark a session as ended"""
    await db.analytics_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"ended_at": datetime.now(timezone.utc)}}
    )
    return {"success": True}


# ============ ADMIN STATS ENDPOINTS ============

@router.get("/admin/stats")
async def get_analytics_stats(
    range: str = Query("7d", description="Date range: 24h, 7d, 30d, 90d"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get overall analytics statistics"""
    # Calculate date range
    now = datetime.now(timezone.utc)
    
    if start_date and end_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except:
            start = now - timedelta(days=7)
            end = now
    else:
        days_map = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(range, 7)
        start = now - timedelta(days=days)
        end = now
    
    date_filter = {"timestamp": {"$gte": start, "$lte": end}}
    
    # Get basic stats
    total_events = await db.analytics_events.count_documents(date_filter)
    page_views = await db.analytics_events.count_documents({**date_filter, "event_type": "page_view"})
    
    # Unique visitors
    unique_visitors = len(await db.analytics_events.distinct("visitor_id", date_filter))
    
    # Unique sessions
    unique_sessions = len(await db.analytics_events.distinct("session_id", date_filter))
    
    # Daily stats
    daily_pipeline = [
        {"$match": date_filter},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "events": {"$sum": 1},
            "page_views": {"$sum": {"$cond": [{"$eq": ["$event_type", "page_view"]}, 1, 0]}},
            "visitors": {"$addToSet": "$visitor_id"},
            "sessions": {"$addToSet": "$session_id"}
        }},
        {"$project": {
            "_id": 1,
            "events": 1,
            "page_views": 1,
            "visitors": {"$size": "$visitors"},
            "sessions": {"$size": "$sessions"}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily_stats = await db.analytics_events.aggregate(daily_pipeline).to_list(None)
    
    # Top pages
    top_pages_pipeline = [
        {"$match": {**date_filter, "event_type": "page_view"}},
        {"$group": {"_id": "$page_url", "views": {"$sum": 1}}},
        {"$sort": {"views": -1}},
        {"$limit": 10}
    ]
    top_pages = await db.analytics_events.aggregate(top_pages_pipeline).to_list(None)
    
    # Traffic sources
    sources_pipeline = [
        {"$match": date_filter},
        {"$group": {"_id": "$referrer.source", "visits": {"$sum": 1}}},
        {"$sort": {"visits": -1}},
        {"$limit": 10}
    ]
    traffic_sources = await db.analytics_events.aggregate(sources_pipeline).to_list(None)
    
    # Device breakdown
    devices_pipeline = [
        {"$match": date_filter},
        {"$group": {"_id": "$device.device_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    devices = await db.analytics_events.aggregate(devices_pipeline).to_list(None)
    
    # Browser breakdown
    browsers_pipeline = [
        {"$match": date_filter},
        {"$group": {"_id": "$device.browser", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    browsers = await db.analytics_events.aggregate(browsers_pipeline).to_list(None)
    
    # Country breakdown
    countries_pipeline = [
        {"$match": date_filter},
        {"$group": {"_id": "$geo.country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    countries = await db.analytics_events.aggregate(countries_pipeline).to_list(None)
    
    return {
        "summary": {
            "total_events": total_events,
            "page_views": page_views,
            "unique_visitors": unique_visitors,
            "unique_sessions": unique_sessions,
            "avg_pages_per_session": round(page_views / unique_sessions, 2) if unique_sessions > 0 else 0
        },
        "daily_stats": daily_stats,
        "top_pages": top_pages,
        "traffic_sources": traffic_sources,
        "devices": {d["_id"]: d["count"] for d in devices if d["_id"]},
        "browsers": {b["_id"]: b["count"] for b in browsers if b["_id"]},
        "countries": countries,
        "date_range": {"start": start.isoformat(), "end": end.isoformat()}
    }


@router.get("/admin/online-users")
async def get_online_users():
    """Get currently online users (active in last X minutes)"""
    threshold = datetime.now(timezone.utc) - timedelta(minutes=ONLINE_USER_TTL_MINUTES)
    
    # Get online authenticated users
    online_users = await db.online_users.find({
        "last_seen": {"$gte": threshold}
    }).to_list(None)
    
    # Enrich with user info
    enriched = []
    for ou in online_users:
        user_info = None
        if ou.get("user_id"):
            user = await db.users.find_one(
                {"id": ou["user_id"]},
                {"_id": 0, "email": 1, "name": 1, "first_name": 1, "last_name": 1, "role": 1}
            )
            user_info = user
        
        enriched.append({
            "user_id": ou.get("user_id"),
            "user_info": user_info,
            "session_id": ou.get("session_id"),
            "current_page": ou.get("current_page"),
            "last_seen": ou.get("last_seen").isoformat() if ou.get("last_seen") else None
        })
    
    # Count total online sessions (including anonymous)
    total_active_sessions = await db.analytics_sessions.count_documents({
        "last_seen": {"$gte": threshold}
    })
    
    return {
        "online_users": enriched,
        "online_users_count": len(enriched),
        "total_active_sessions": total_active_sessions,
        "threshold_minutes": ONLINE_USER_TTL_MINUTES
    }


@router.get("/admin/events")
async def get_events(
    range: str = Query("24h"),
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """Get filtered events list (audit trail)"""
    now = datetime.now(timezone.utc)
    days_map = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 1)
    start = now - timedelta(days=days)
    
    # Build filter
    filter_query = {"timestamp": {"$gte": start}}
    
    if event_type:
        filter_query["event_type"] = event_type
    if user_id:
        filter_query["user_id"] = user_id
    if session_id:
        filter_query["session_id"] = session_id
    
    # Get total
    total = await db.analytics_events.count_documents(filter_query)
    
    # Get events
    skip = (page - 1) * limit
    events = await db.analytics_events.find(
        filter_query,
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    # Convert datetime to string
    for event in events:
        if event.get("timestamp"):
            event["timestamp"] = event["timestamp"].isoformat()
    
    return {
        "events": events,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/admin/user-timeline/{user_id}")
async def get_user_timeline(
    user_id: str,
    range: str = Query("7d"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get timeline of events for a specific user"""
    now = datetime.now(timezone.utc)
    days_map = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 7)
    start = now - timedelta(days=days)
    
    # Get user info
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    
    # Get events
    events = await db.analytics_events.find(
        {"user_id": user_id, "timestamp": {"$gte": start}},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Group by session
    sessions = {}
    for event in events:
        sid = event.get("session_id", "unknown")
        if sid not in sessions:
            sessions[sid] = []
        if event.get("timestamp"):
            event["timestamp"] = event["timestamp"].isoformat()
        sessions[sid].append(event)
    
    return {
        "user": user,
        "total_events": len(events),
        "sessions": sessions,
        "session_count": len(sessions)
    }


@router.get("/admin/top-products")
async def get_top_products(
    range: str = Query("7d"),
    limit: int = Query(20, ge=1, le=100)
):
    """Get most viewed products"""
    now = datetime.now(timezone.utc)
    days_map = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 7)
    start = now - timedelta(days=days)
    
    pipeline = [
        {"$match": {
            "timestamp": {"$gte": start},
            "event_type": "product_view",
            "product_id": {"$exists": True, "$ne": None}
        }},
        {"$group": {
            "_id": "$product_id",
            "product_name": {"$first": "$product_name"},
            "total_views": {"$sum": 1},
            "unique_visitors": {"$addToSet": "$visitor_id"}
        }},
        {"$project": {
            "_id": 1,
            "product_name": 1,
            "total_views": 1,
            "unique_views": {"$size": "$unique_visitors"}
        }},
        {"$sort": {"total_views": -1}},
        {"$limit": limit}
    ]
    
    top_products = await db.analytics_events.aggregate(pipeline).to_list(None)
    
    # Enrich with product details
    enriched = []
    for p in top_products:
        product = await db.products.find_one(
            {"id": p["_id"]},
            {"_id": 0, "name": 1, "primary_image_url": 1, "price": 1, "category_label": 1}
        )
        enriched.append({
            "product_id": p["_id"],
            "product_name": p.get("product_name") or (product.get("name") if product else "Unknown"),
            "total_views": p["total_views"],
            "unique_views": p["unique_views"],
            "product_info": product
        })
    
    return {
        "top_products": enriched,
        "date_range": range
    }


@router.get("/admin/search-terms")
async def get_top_search_terms(
    range: str = Query("7d"),
    limit: int = Query(20, ge=1, le=100)
):
    """Get most searched terms"""
    now = datetime.now(timezone.utc)
    days_map = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 7)
    start = now - timedelta(days=days)
    
    pipeline = [
        {"$match": {
            "timestamp": {"$gte": start},
            "event_type": "search",
            "search_query": {"$exists": True, "$ne": None, "$ne": ""}
        }},
        {"$group": {
            "_id": {"$toLower": "$search_query"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    
    search_terms = await db.analytics_events.aggregate(pipeline).to_list(None)
    
    return {
        "search_terms": [{"term": s["_id"], "count": s["count"]} for s in search_terms],
        "date_range": range
    }


# ============ DATA MANAGEMENT ============

@router.delete("/admin/purge-old-data")
async def purge_old_data(days: int = Query(90, ge=7)):
    """Purge analytics data older than X days"""
    threshold = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Delete old events
    events_result = await db.analytics_events.delete_many({
        "timestamp": {"$lt": threshold}
    })
    
    # Delete old sessions
    sessions_result = await db.analytics_sessions.delete_many({
        "last_seen": {"$lt": threshold}
    })
    
    return {
        "success": True,
        "deleted_events": events_result.deleted_count,
        "deleted_sessions": sessions_result.deleted_count,
        "threshold_date": threshold.isoformat()
    }


# ============ DATABASE INDEXES ============

async def create_analytics_indexes():
    """Create indexes for analytics collections"""
    # Events indexes
    await db.analytics_events.create_index([("timestamp", -1)])
    await db.analytics_events.create_index([("event_type", 1)])
    await db.analytics_events.create_index([("session_id", 1)])
    await db.analytics_events.create_index([("visitor_id", 1)])
    await db.analytics_events.create_index([("user_id", 1)])
    await db.analytics_events.create_index([("product_id", 1)])
    await db.analytics_events.create_index([
        ("timestamp", -1),
        ("event_type", 1)
    ])
    
    # Sessions indexes
    await db.analytics_sessions.create_index([("session_id", 1)], unique=True)
    await db.analytics_sessions.create_index([("last_seen", -1)])
    await db.analytics_sessions.create_index([("visitor_id", 1)])
    
    # Online users index with TTL (auto-delete after 10 minutes of inactivity)
    await db.online_users.create_index([("user_id", 1)], unique=True)
    await db.online_users.create_index(
        [("last_seen", 1)],
        expireAfterSeconds=600  # 10 minutes TTL
    )
    
    print("[Analytics] Indexes created successfully")
