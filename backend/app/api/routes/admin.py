"""SmartRail AI+ — Admin Routes"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_admin
from app.core.database import get_db

logger = logging.getLogger("smartrail.admin")
router = APIRouter(prefix="/admin")


@router.get("/metrics")
async def get_admin_metrics(admin: dict = Depends(get_current_admin)):
    """Admin metrics dashboard."""
    async with get_db() as db:
        await db.execute(
            """
            SELECT
                COUNT(*) AS total_bookings,
                SUM(CASE WHEN booking_status='CONFIRMED' THEN 1 ELSE 0 END) AS confirmed,
                SUM(CASE WHEN booking_status='WAITING'   THEN 1 ELSE 0 END) AS waitlisted,
                SUM(CASE WHEN booking_status='CANCELLED' THEN 1 ELSE 0 END) AS cancelled,
                SUM(total_fare) AS total_revenue,
                COUNT(DISTINCT user_id) AS unique_users
            FROM bookings
            """
        )
        booking_stats = await db.fetchone()

    async with get_db() as db:
        await db.execute("SELECT COUNT(*) AS count FROM users WHERE role='PASSENGER'")
        user_count = await db.fetchone()

    async with get_db() as db:
        await db.execute(
            """
            SELECT t.train_number, t.train_name, COUNT(b.id) AS booking_count
            FROM bookings b JOIN trains t ON b.train_id = t.id
            GROUP BY t.id ORDER BY booking_count DESC LIMIT 5
            """
        )
        top_trains = await db.fetchall()

    async with get_db() as db:
        await db.execute(
            """
            SELECT pnr, booking_status, total_fare, booking_time, source_station, dest_station
            FROM bookings ORDER BY booking_time DESC LIMIT 10
            """
        )
        recent_bookings = await db.fetchall()

    for b in recent_bookings:
        if b.get("booking_time") and hasattr(b["booking_time"], "isoformat"):
            b["booking_time"] = b["booking_time"].isoformat()

    async with get_db() as db:
        await db.execute(
            """
            SELECT transaction_id, operation_type, status, duration_ms, created_at
            FROM db_transactions_log ORDER BY created_at DESC LIMIT 10
            """
        )
        recent_txns = await db.fetchall()

    for t in recent_txns:
        if t.get("created_at") and hasattr(t["created_at"], "isoformat"):
            t["created_at"] = t["created_at"].isoformat()

    def safe(v, default=0):
        return v if v is not None else default

    return {
        "booking_summary": {
            "total": safe(booking_stats["total_bookings"]),
            "confirmed": safe(booking_stats["confirmed"]),
            "waitlisted": safe(booking_stats["waitlisted"]),
            "cancelled": safe(booking_stats["cancelled"]),
            "total_revenue": float(safe(booking_stats["total_revenue"], 0.0)),
            "unique_users": safe(booking_stats["unique_users"]),
        },
        "total_registered_users": safe(user_count["count"]),
        "top_trains": [dict(t) for t in top_trains],
        "recent_bookings": [dict(b) for b in recent_bookings],
        "recent_transactions": [dict(t) for t in recent_txns],
    }


@router.get("/users")
async def list_users(admin: dict = Depends(get_current_admin)):
    """List all users (admin only)."""
    async with get_db() as db:
        await db.execute(
            "SELECT id, email, username, full_name, role, is_active, created_at, last_login FROM users ORDER BY created_at DESC"
        )
        users = await db.fetchall()

    for u in users:
        for k in ["created_at", "last_login"]:
            if u.get(k) and hasattr(u[k], "isoformat"):
                u[k] = u[k].isoformat()

    return {"total": len(users), "users": [dict(u) for u in users]}
