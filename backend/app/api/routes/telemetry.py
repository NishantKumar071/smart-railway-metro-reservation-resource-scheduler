"""SmartRail AI+ — OS Telemetry Route"""

import logging
from fastapi import APIRouter
from app.core.scheduler import booking_scheduler
from app.core.database import get_db

logger = logging.getLogger("smartrail.telemetry")
router = APIRouter(prefix="/telemetry")


@router.get("")
async def get_telemetry():
    """
    Real-time OS telemetry dashboard data.
    Shows live scheduler metrics and DB-persisted scheduling history.
    """
    scheduler_status = booking_scheduler.get_status()
    telemetry = booking_scheduler.telemetry.snapshot()

    # Fetch recent DB metrics
    async with get_db() as db:
        await db.execute(
            """
            SELECT
                COUNT(*) AS total_logged,
                SUM(CASE WHEN result_status='COMPLETED' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN result_status='FAILED' THEN 1 ELSE 0 END) AS failed,
                AVG(processing_time_ms) AS avg_proc_ms,
                AVG(queue_wait_time_ms) AS avg_wait_ms,
                MAX(queue_position_at_entry) AS max_queue_depth,
                SUM(CASE WHEN priority_level=1 THEN 1 ELSE 0 END) AS emergency_count,
                SUM(CASE WHEN priority_level=2 THEN 1 ELSE 0 END) AS senior_count,
                SUM(CASE WHEN priority_level=3 THEN 1 ELSE 0 END) AS tatkal_count,
                SUM(CASE WHEN priority_level=4 THEN 1 ELSE 0 END) AS normal_count
            FROM os_scheduling_metrics
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
        )
        db_stats = await db.fetchone()

    async with get_db() as db:
        await db.execute(
            """
            SELECT request_id, priority_name, processing_time_ms, queue_wait_time_ms,
                   worker_thread_id, result_status, created_at
            FROM os_scheduling_metrics
            ORDER BY created_at DESC
            LIMIT 20
            """
        )
        recent = await db.fetchall()

    for r in recent:
        if r.get("created_at") and hasattr(r["created_at"], "isoformat"):
            r["created_at"] = r["created_at"].isoformat()

    def safe_float(v):
        try:
            return round(float(v), 2) if v is not None else 0.0
        except Exception:
            return 0.0

    return {
        "live_scheduler": {
            "worker_threads_configured": scheduler_status["worker_threads"],
            "queue_length": scheduler_status["queue_length"],
            "thread_states": scheduler_status["thread_states"],
        },
        "live_counters": telemetry,
        "db_stats_24h": {
            "total_logged": db_stats["total_logged"] or 0,
            "completed": db_stats["completed"] or 0,
            "failed": db_stats["failed"] or 0,
            "avg_processing_ms": safe_float(db_stats["avg_proc_ms"]),
            "avg_queue_wait_ms": safe_float(db_stats["avg_wait_ms"]),
            "max_queue_depth": db_stats["max_queue_depth"] or 0,
            "by_priority": {
                "EMERGENCY": db_stats["emergency_count"] or 0,
                "SENIOR_CITIZEN": db_stats["senior_count"] or 0,
                "TATKAL": db_stats["tatkal_count"] or 0,
                "NORMAL": db_stats["normal_count"] or 0,
            },
        },
        "recent_requests": [dict(r) for r in recent],
        "os_concepts": {
            "multithreading": "Worker thread pool with configurable size",
            "synchronization": "threading.Condition, threading.Lock, threading.Event",
            "scheduling_policy": "Priority queue (min-heap) with 4 levels: EMERGENCY > SENIOR > TATKAL > NORMAL",
            "deadlock_prevention": "Single-lock protocol — only queue_condition lock acquired in scheduler",
            "producer_consumer": "HTTP handlers produce; worker threads consume from bounded priority queue",
            "note": "This is an ACADEMIC demonstration of OS concepts. Priority levels are project-defined, not official Indian Railways policy.",
        },
    }
