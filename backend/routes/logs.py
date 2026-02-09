"""
Logs & Errors Management API
Endpoints pour gérer les logs, erreurs et alertes
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/logs", tags=["Logs & Errors"])

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class LogErrorRequest(BaseModel):
    """Request model for logging errors from frontend"""
    error_type: str = Field(..., description="Type of error (js_error, api_error, etc.)")
    message: str = Field(..., description="Error message")
    stack_trace: Optional[str] = None
    url: str = Field(..., description="URL where error occurred")
    user_agent: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateErrorStatusRequest(BaseModel):
    """Request to update error status"""
    status: ErrorStatus
    notes: Optional[str] = None


# ============ ERROR LOGGING ENDPOINTS ============

@router.post("/error")
async def log_error(error: LogErrorRequest):
    """
    Log an error from frontend or API
    Automatically determines severity based on error type
    """
    # Determine severity
    severity = ErrorSeverity.MEDIUM
    if "500" in error.message or "Internal Server Error" in error.message:
        severity = ErrorSeverity.CRITICAL
    elif "TypeError" in error.error_type or "ReferenceError" in error.error_type:
        severity = ErrorSeverity.HIGH
    elif "NetworkError" in error.error_type or "timeout" in error.message.lower():
        severity = ErrorSeverity.MEDIUM
    elif "Warning" in error.error_type:
        severity = ErrorSeverity.LOW
    
    # Create error document
    error_doc = {
        "error_type": error.error_type,
        "message": error.message,
        "stack_trace": error.stack_trace,
        "url": error.url,
        "user_agent": error.user_agent,
        "user_id": error.user_id,
        "session_id": error.session_id,
        "metadata": error.metadata or {},
        "severity": severity.value,
        "status": ErrorStatus.NEW.value,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "occurrence_count": 1,
        "last_occurrence": datetime.now(timezone.utc)
    }
    
    # Check if similar error exists (group by message + url)
    existing = await db.error_logs.find_one({
        "message": error.message,
        "url": error.url,
        "status": {"$ne": ErrorStatus.RESOLVED.value}
    })
    
    if existing:
        # Update existing error
        await db.error_logs.update_one(
            {"_id": existing["_id"]},
            {
                "$inc": {"occurrence_count": 1},
                "$set": {
                    "last_occurrence": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                "$push": {
                    "occurrences": {
                        "timestamp": datetime.now(timezone.utc),
                        "user_id": error.user_id,
                        "session_id": error.session_id,
                        "user_agent": error.user_agent
                    }
                }
            }
        )
        return {"success": True, "error_id": str(existing["_id"]), "grouped": True}
    else:
        # Insert new error
        error_doc["occurrences"] = [{
            "timestamp": datetime.now(timezone.utc),
            "user_id": error.user_id,
            "session_id": error.session_id,
            "user_agent": error.user_agent
        }]
        result = await db.error_logs.insert_one(error_doc)
        return {"success": True, "error_id": str(result.inserted_id), "grouped": False}


@router.post("/api-error")
async def log_api_error(
    status_code: int,
    endpoint: str,
    method: str,
    error_message: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_body: Optional[Dict] = None,
    response_time_ms: Optional[float] = None
):
    """
    Log API errors (called from middleware)
    """
    severity = ErrorSeverity.MEDIUM
    if status_code >= 500:
        severity = ErrorSeverity.CRITICAL
    elif status_code == 404:
        severity = ErrorSeverity.LOW
    elif status_code in [401, 403]:
        severity = ErrorSeverity.MEDIUM
    elif status_code >= 400:
        severity = ErrorSeverity.MEDIUM
    
    error_doc = {
        "error_type": "api_error",
        "status_code": status_code,
        "endpoint": endpoint,
        "method": method,
        "message": error_message,
        "request_id": request_id,
        "user_id": user_id,
        "request_body": request_body,
        "response_time_ms": response_time_ms,
        "severity": severity.value,
        "status": ErrorStatus.NEW.value,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "occurrence_count": 1
    }
    
    await db.error_logs.insert_one(error_doc)
    return {"success": True}


# ============ ADMIN ENDPOINTS ============

@router.get("/admin/errors")
async def get_errors(
    status: Optional[ErrorStatus] = None,
    severity: Optional[ErrorSeverity] = None,
    error_type: Optional[str] = None,
    range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None
):
    """
    Get error logs with filters
    """
    # Build time filter
    now = datetime.now(timezone.utc)
    range_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90)
    }
    time_delta = range_map.get(range, timedelta(hours=24))
    start_time = now - time_delta
    
    # Build query
    query = {"created_at": {"$gte": start_time}}
    
    if status:
        query["status"] = status.value
    if severity:
        query["severity"] = severity.value
    if error_type:
        query["error_type"] = error_type
    if search:
        query["$or"] = [
            {"message": {"$regex": search, "$options": "i"}},
            {"url": {"$regex": search, "$options": "i"}},
            {"endpoint": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count
    total = await db.error_logs.count_documents(query)
    
    # Get errors
    skip = (page - 1) * limit
    errors = await db.error_logs.find(
        query,
        {"_id": 0, "occurrences": {"$slice": -5}}  # Only last 5 occurrences
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Convert ObjectId to string if present
    for error in errors:
        if "_id" in error:
            error["id"] = str(error["_id"])
            del error["_id"]
    
    return {
        "errors": errors,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.get("/admin/errors/summary")
async def get_errors_summary(
    range: str = Query("24h", description="Time range")
):
    """
    Get error summary statistics
    """
    now = datetime.now(timezone.utc)
    range_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    time_delta = range_map.get(range, timedelta(hours=24))
    start_time = now - time_delta
    
    # Aggregation pipeline
    pipeline = [
        {"$match": {"created_at": {"$gte": start_time}}},
        {"$group": {
            "_id": None,
            "total_errors": {"$sum": 1},
            "total_occurrences": {"$sum": "$occurrence_count"},
            "critical_count": {"$sum": {"$cond": [{"$eq": ["$severity", "critical"]}, 1, 0]}},
            "high_count": {"$sum": {"$cond": [{"$eq": ["$severity", "high"]}, 1, 0]}},
            "medium_count": {"$sum": {"$cond": [{"$eq": ["$severity", "medium"]}, 1, 0]}},
            "low_count": {"$sum": {"$cond": [{"$eq": ["$severity", "low"]}, 1, 0]}},
            "new_count": {"$sum": {"$cond": [{"$eq": ["$status", "new"]}, 1, 0]}},
            "resolved_count": {"$sum": {"$cond": [{"$eq": ["$status", "resolved"]}, 1, 0]}},
            "api_errors": {"$sum": {"$cond": [{"$eq": ["$error_type", "api_error"]}, 1, 0]}},
            "js_errors": {"$sum": {"$cond": [{"$in": ["$error_type", ["js_error", "TypeError", "ReferenceError"]]}, 1, 0]}}
        }}
    ]
    
    result = await db.error_logs.aggregate(pipeline).to_list(1)
    
    if result:
        summary = result[0]
        del summary["_id"]
    else:
        summary = {
            "total_errors": 0,
            "total_occurrences": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "new_count": 0,
            "resolved_count": 0,
            "api_errors": 0,
            "js_errors": 0
        }
    
    # Get errors by hour (for chart)
    hourly_pipeline = [
        {"$match": {"created_at": {"$gte": start_time}}},
        {"$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d %H:00",
                    "date": "$created_at"
                }
            },
            "count": {"$sum": 1},
            "critical": {"$sum": {"$cond": [{"$eq": ["$severity", "critical"]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 168}  # Max 7 days of hourly data
    ]
    
    hourly = await db.error_logs.aggregate(hourly_pipeline).to_list(168)
    
    # Get top errors
    top_errors_pipeline = [
        {"$match": {"created_at": {"$gte": start_time}}},
        {"$group": {
            "_id": "$message",
            "count": {"$sum": "$occurrence_count"},
            "severity": {"$first": "$severity"},
            "error_type": {"$first": "$error_type"},
            "url": {"$first": "$url"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    top_errors = await db.error_logs.aggregate(top_errors_pipeline).to_list(10)
    
    # Get 500 errors count (for alerts)
    errors_500 = await db.error_logs.count_documents({
        "created_at": {"$gte": start_time},
        "$or": [
            {"status_code": {"$gte": 500}},
            {"message": {"$regex": "500|Internal Server Error", "$options": "i"}}
        ]
    })
    
    return {
        "summary": summary,
        "hourly": hourly,
        "top_errors": top_errors,
        "errors_500_count": errors_500,
        "range": range,
        "timestamp": now.isoformat()
    }


@router.put("/admin/errors/{error_id}/status")
async def update_error_status(error_id: str, request: UpdateErrorStatusRequest):
    """
    Update error status
    """
    from bson import ObjectId
    
    try:
        obj_id = ObjectId(error_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid error ID")
    
    update_data = {
        "status": request.status.value,
        "updated_at": datetime.now(timezone.utc)
    }
    
    if request.notes:
        update_data["resolution_notes"] = request.notes
    
    if request.status == ErrorStatus.RESOLVED:
        update_data["resolved_at"] = datetime.now(timezone.utc)
    
    result = await db.error_logs.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Error not found")
    
    return {"success": True, "status": request.status.value}


@router.delete("/admin/errors/{error_id}")
async def delete_error(error_id: str):
    """
    Delete an error log
    """
    from bson import ObjectId
    
    try:
        obj_id = ObjectId(error_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid error ID")
    
    result = await db.error_logs.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Error not found")
    
    return {"success": True}


@router.post("/admin/errors/resolve-all")
async def resolve_all_errors(
    severity: Optional[ErrorSeverity] = None,
    error_type: Optional[str] = None
):
    """
    Bulk resolve errors
    """
    query = {"status": {"$ne": ErrorStatus.RESOLVED.value}}
    
    if severity:
        query["severity"] = severity.value
    if error_type:
        query["error_type"] = error_type
    
    result = await db.error_logs.update_many(
        query,
        {"$set": {
            "status": ErrorStatus.RESOLVED.value,
            "updated_at": datetime.now(timezone.utc),
            "resolved_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"success": True, "resolved_count": result.modified_count}


# ============ ALERTS ENDPOINTS ============

@router.get("/admin/alerts")
async def get_active_alerts():
    """
    Get active alerts based on error thresholds
    """
    now = datetime.now(timezone.utc)
    last_hour = now - timedelta(hours=1)
    last_5min = now - timedelta(minutes=5)
    
    alerts = []
    
    # Check for 500 errors in last 5 minutes
    errors_500_5min = await db.error_logs.count_documents({
        "created_at": {"$gte": last_5min},
        "$or": [
            {"status_code": {"$gte": 500}},
            {"severity": "critical"}
        ]
    })
    
    if errors_500_5min > 0:
        alerts.append({
            "type": "critical",
            "title": "Erreurs 500 détectées",
            "message": f"{errors_500_5min} erreur(s) critique(s) dans les 5 dernières minutes",
            "count": errors_500_5min,
            "action": "investigate"
        })
    
    # Check for high error rate in last hour
    errors_last_hour = await db.error_logs.count_documents({
        "created_at": {"$gte": last_hour}
    })
    
    if errors_last_hour > 50:
        alerts.append({
            "type": "warning",
            "title": "Taux d'erreur élevé",
            "message": f"{errors_last_hour} erreurs dans la dernière heure",
            "count": errors_last_hour,
            "action": "review"
        })
    
    # Check for unresolved critical errors
    unresolved_critical = await db.error_logs.count_documents({
        "severity": "critical",
        "status": "new"
    })
    
    if unresolved_critical > 0:
        alerts.append({
            "type": "danger",
            "title": "Erreurs critiques non résolues",
            "message": f"{unresolved_critical} erreur(s) critique(s) en attente",
            "count": unresolved_critical,
            "action": "resolve"
        })
    
    return {
        "alerts": alerts,
        "has_critical": any(a["type"] in ["critical", "danger"] for a in alerts),
        "timestamp": now.isoformat()
    }


# ============ INDEX CREATION ============

async def create_logs_indexes():
    """Create indexes for error_logs collection"""
    try:
        await db.error_logs.create_index([("created_at", -1)])
        await db.error_logs.create_index([("status", 1), ("created_at", -1)])
        await db.error_logs.create_index([("severity", 1), ("created_at", -1)])
        await db.error_logs.create_index([("error_type", 1), ("created_at", -1)])
        await db.error_logs.create_index([("message", 1), ("url", 1)])
        # TTL index - auto-delete after 90 days
        await db.error_logs.create_index(
            [("created_at", 1)],
            expireAfterSeconds=7776000  # 90 days
        )
    except Exception as e:
        print(f"Error creating logs indexes: {e}")
