"""SmartRail AI+ — Waitlist Routes"""

import logging
from fastapi import APIRouter, Query, HTTPException
from app.core.database import get_db

logger = logging.getLogger("smartrail.waitlist")
router = APIRouter(prefix="/waitlist")


@router.get("")
async def get_waitlist(
    train_id: int = Query(...),
    coach_id: int = Query(...),
    journey_date: str = Query(...),
):
    """Get the current waitlist for a train/coach/date."""
    async with get_db() as db:
        await db.execute(
            """
            SELECT b.pnr, b.booking_status, b.booking_time,
                   bp.waitlist_number, bp.passenger_fare,
                   p.full_name, p.age, p.gender,
                   b.quota, b.priority_level
            FROM bookings b
            JOIN booking_passengers bp ON b.id = bp.booking_id
            JOIN passengers p ON bp.passenger_id = p.id
            WHERE b.train_id = %s
              AND b.coach_id = %s
              AND b.journey_date = %s
              AND b.booking_status = 'WAITING'
              AND bp.status = 'WAITING'
            ORDER BY bp.waitlist_number ASC
            """,
            (train_id, coach_id, journey_date),
        )
        waitlist = await db.fetchall()

    for w in waitlist:
        for key in ["booking_time"]:
            if w.get(key) and hasattr(w[key], "isoformat"):
                w[key] = w[key].isoformat()

    return {
        "train_id": train_id,
        "coach_id": coach_id,
        "journey_date": journey_date,
        "total_waitlisted": len(waitlist),
        "waitlist": [dict(w) for w in waitlist],
    }
