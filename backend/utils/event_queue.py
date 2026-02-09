"""
Async Event Queue for Analytics
Separates high-volume analytics events from transactional operations
Uses fire-and-forget pattern to never block the main request
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from collections import deque
import traceback

from utils.observability import logger, metrics


class AsyncEventQueue:
    """
    High-performance async event queue
    - Fire-and-forget: Never blocks the caller
    - Batched writes: Collects events and writes in batches
    - Back-pressure handling: Drops events if queue is full
    - Auto-retry on failure
    """
    
    def __init__(
        self,
        max_queue_size: int = 10000,
        batch_size: int = 100,
        flush_interval_seconds: float = 2.0,
        max_retries: int = 3
    ):
        self._queue: deque = deque(maxlen=max_queue_size)
        self._batch_size = batch_size
        self._flush_interval = flush_interval_seconds
        self._max_retries = max_retries
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._handlers: Dict[str, Callable] = {}
        self._dropped_count = 0
        self._processed_count = 0
        self._error_count = 0
        self._lock = asyncio.Lock()
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for an event type"""
        self._handlers[event_type] = handler
    
    async def enqueue(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Add event to queue (non-blocking)
        Returns True if queued, False if dropped due to back-pressure
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc),
            "retries": 0
        }
        
        try:
            self._queue.append(event)
            return True
        except Exception:
            self._dropped_count += 1
            return False
    
    def fire_and_forget(self, event_type: str, data: Dict[str, Any]):
        """
        Fire-and-forget event submission
        Creates a task that won't block the caller
        """
        asyncio.create_task(self.enqueue(event_type, data))
    
    async def _process_batch(self, events: List[Dict[str, Any]]):
        """Process a batch of events"""
        # Group events by type
        by_type: Dict[str, List[Dict]] = {}
        for event in events:
            event_type = event["type"]
            if event_type not in by_type:
                by_type[event_type] = []
            by_type[event_type].append(event)
        
        # Process each type
        for event_type, type_events in by_type.items():
            handler = self._handlers.get(event_type)
            if not handler:
                logger.warning(f"No handler for event type: {event_type}")
                continue
            
            try:
                # Call handler with batch of events
                await handler([e["data"] for e in type_events])
                self._processed_count += len(type_events)
                
                await metrics.record("event_queue.batch_processed", len(type_events), 
                                     {"type": event_type})
                
            except Exception as e:
                self._error_count += len(type_events)
                logger.error(f"Error processing events: {str(e)}",
                            event_type=event_type,
                            batch_size=len(type_events),
                            error=str(e))
                
                # Re-queue events that can be retried
                for event in type_events:
                    if event["retries"] < self._max_retries:
                        event["retries"] += 1
                        try:
                            self._queue.appendleft(event)
                        except:
                            pass
    
    async def _worker(self):
        """Background worker that processes the queue"""
        logger.info("Event queue worker started")
        
        while self._running:
            try:
                # Wait for flush interval
                await asyncio.sleep(self._flush_interval)
                
                # Collect batch
                batch = []
                async with self._lock:
                    while len(batch) < self._batch_size and self._queue:
                        batch.append(self._queue.popleft())
                
                if batch:
                    await self._process_batch(batch)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event queue worker error: {str(e)}")
                await asyncio.sleep(1)
        
        # Process remaining events on shutdown
        remaining = list(self._queue)
        if remaining:
            logger.info(f"Processing {len(remaining)} remaining events on shutdown")
            await self._process_batch(remaining)
        
        logger.info("Event queue worker stopped")
    
    async def start(self):
        """Start the background worker"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._worker())
    
    async def stop(self):
        """Stop the background worker gracefully"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    def stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "queue_size": len(self._queue),
            "processed_count": self._processed_count,
            "dropped_count": self._dropped_count,
            "error_count": self._error_count,
            "handlers_registered": list(self._handlers.keys()),
            "is_running": self._running
        }
    
    async def flush(self):
        """Force flush all pending events"""
        batch = []
        async with self._lock:
            while self._queue:
                batch.append(self._queue.popleft())
        
        if batch:
            await self._process_batch(batch)


# Global event queue instance
event_queue = AsyncEventQueue(
    max_queue_size=10000,
    batch_size=100,
    flush_interval_seconds=2.0
)


# ============ ANALYTICS EVENT HANDLERS ============

async def handle_analytics_events(events: List[Dict[str, Any]]):
    """
    Batch handler for analytics events
    Writes directly to MongoDB in bulk
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    
    # Get database connection
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        logger.error("MongoDB connection not configured for analytics")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Prepare documents
        docs = []
        for event in events:
            doc = {
                **event,
                "processed_at": datetime.now(timezone.utc)
            }
            docs.append(doc)
        
        # Bulk insert
        if docs:
            result = await db.analytics_events.insert_many(docs, ordered=False)
            logger.info(f"Inserted {len(result.inserted_ids)} analytics events",
                       type="analytics_batch",
                       count=len(result.inserted_ids))
    
    except Exception as e:
        logger.error(f"Failed to insert analytics events: {str(e)}")
        raise
    finally:
        client.close()


async def handle_session_updates(events: List[Dict[str, Any]]):
    """Batch handler for session updates"""
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import UpdateOne
    import os
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Group updates by session_id
        operations = []
        for event in events:
            session_id = event.get("session_id")
            if not session_id:
                continue
            
            operations.append(UpdateOne(
                {"session_id": session_id},
                {
                    "$set": {
                        "last_seen": event.get("timestamp", datetime.now(timezone.utc)),
                        "last_page": event.get("page_url")
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now(timezone.utc)
                    },
                    "$inc": {"page_views": 1}
                },
                upsert=True
            ))
        
        if operations:
            result = await db.analytics_sessions.bulk_write(operations, ordered=False)
            logger.debug(f"Updated {result.modified_count} sessions",
                        type="session_batch",
                        modified=result.modified_count,
                        upserted=result.upserted_count)
    
    except Exception as e:
        logger.error(f"Failed to update sessions: {str(e)}")
        raise
    finally:
        client.close()


# Register handlers
event_queue.register_handler("analytics", handle_analytics_events)
event_queue.register_handler("session_update", handle_session_updates)
