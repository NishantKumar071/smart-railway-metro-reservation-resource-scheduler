"""
SmartRail AI+ — API Routes: Bookings
Booking requests are submitted to the OS priority scheduler and processed by worker threads.
"""

import logging
import threading
import time
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.scheduler import booking_scheduler, QUOTA_PRIORITY_MAP
from app.core.database import get_db
from app.services.booking_service import _do_book_ticket, _do_cancel_ticket

logger = logging.getLogger("smartrail.bookings")
router = APIRouter(prefix="/bookings")


class PassengerInfo(BaseModel):
    full_name: str
    age: int
    gender: str = "MALE"
    id_type: str = "AADHAAR"
    phone: Optional[str] = None


class BookingRequest(BaseModel):
    train_id: int
    coach_id: int
    journey_date: str
    source_station: str
    dest_station: str
    travel_class: str
    quota: str = "GENERAL"
    preferred_berth: str = "NO_PREFERENCE"
    passengers: List[PassengerInfo]
    total_fare: float


class CancellationRequest(BaseModel):
    reason: Optional[str] = "User requested cancellation"


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_booking(
    req: BookingRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new ticket booking.

    This endpoint:
    1. Validates inputs
    2. Fetches coach number from DB
    3. Submits the booking to the OS priority scheduler
    4. The scheduler's worker thread executes the booking inside a DB transaction
    5. Returns the booking result (PNR, status, seat allocation)
    """
    # Validate passengers
    if not req.passengers:
        raise HTTPException(status_code=400, detail="At least one passenger is required")
    if len(req.passengers) > 6:
        raise HTTPException(status_code=400, detail="Maximum 6 passengers per booking")

    # Validate travel class
    valid_classes = ["1AC", "2AC", "3AC", "SL", "CC", "2S", "EC"]
    if req.travel_class.upper() not in valid_classes:
        raise HTTPException(status_code=400, detail=f"Invalid travel class. Use one of: {valid_classes}")

    # Fetch coach number
    async with get_db() as db:
        await db.execute(
            "SELECT coach_number, train_id FROM train_coaches WHERE id = %s",
            (req.coach_id,),
        )
        coach = await db.fetchone()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    if coach["train_id"] != req.train_id:
        raise HTTPException(status_code=400, detail="Coach does not belong to specified train")

    booking_data = {
        "user_id":        current_user["id"],
        "train_id":       req.train_id,
        "coach_id":       req.coach_id,
        "coach_number":   coach["coach_number"],
        "journey_date":   req.journey_date,
        "source_station": req.source_station.upper(),
        "dest_station":   req.dest_station.upper(),
        "travel_class":   req.travel_class.upper(),
        "quota":          req.quota.upper(),
        "preferred_berth": req.preferred_berth.upper(),
        "passengers":     [p.model_dump() for p in req.passengers],
        "total_fare":     req.total_fare,
        "worker_thread_id": threading.get_ident(),
    }

    logger.info(
        f"Booking submitted | user={current_user['id']} | train={req.train_id} | "
        f"quota={req.quota} | passengers={len(req.passengers)}"
    )

    try:
        result = booking_scheduler.submit_request(
            task_fn=_do_book_ticket,
            task_args=(booking_data,),
            quota=req.quota,
            wait=True,
            timeout=30.0,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Booking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")

    return {
        "success": True,
        "message": f"Booking {'confirmed' if result['booking_status'] == 'CONFIRMED' else 'waitlisted'}",
        **result,
        "disclaimer": "This is a demonstration booking. Not connected to real railway services.",
    }


@router.get("/{pnr}")
async def get_booking(pnr: str, current_user: dict = Depends(get_current_user)):
    """Get booking details by PNR."""
    async with get_db() as db:
        await db.execute(
            """
            SELECT b.*, t.train_number, t.train_name, t.departure_time, t.arrival_time,
                   s_src.station_name AS source_name, s_dst.station_name AS dest_name,
                   u.full_name AS booked_by, u.email
            FROM bookings b
            JOIN trains t ON b.train_id = t.id
            JOIN stations s_src ON b.source_station = s_src.station_code
            JOIN stations s_dst ON b.dest_station = s_dst.station_code
            JOIN users u ON b.user_id = u.id
            WHERE b.pnr = %s
            """,
            (pnr,),
        )
        booking = await db.fetchone()

    if not booking:
        raise HTTPException(status_code=404, detail=f"PNR {pnr} not found")

    # Auth check: passengers can only see their own bookings
    if current_user["role"] != "ADMIN" and booking["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    async with get_db() as db:
        await db.execute(
            """
            SELECT bp.*, p.full_name, p.age, p.gender, p.id_type
            FROM booking_passengers bp
            JOIN passengers p ON bp.passenger_id = p.id
            WHERE bp.booking_id = %s
            """,
            (booking["id"],),
        )
        passengers = await db.fetchall()

    # Serialize datetimes
    for key in ["booking_time", "cancellation_time", "created_at", "updated_at"]:
        if booking.get(key) and hasattr(booking[key], "isoformat"):
            booking[key] = booking[key].isoformat()
    for key in ["departure_time", "arrival_time"]:
        if booking.get(key):
            booking[key] = str(booking[key])
    for key in ["journey_date"]:
        if booking.get(key) and hasattr(booking[key], "isoformat"):
            booking[key] = booking[key].isoformat()
    for p in passengers:
        for key in ["created_at", "updated_at"]:
            if p.get(key) and hasattr(p[key], "isoformat"):
                p[key] = p[key].isoformat()

    return {
        **dict(booking),
        "passengers": [dict(p) for p in passengers],
    }


@router.post("/{pnr}/cancel")
async def cancel_booking(
    pnr: str,
    req: CancellationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Cancel a booking by PNR."""
    try:
        result = booking_scheduler.submit_request(
            task_fn=_do_cancel_ticket,
            task_args=(pnr, current_user["id"], req.reason),
            quota="GENERAL",
            wait=True,
            timeout=30.0,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "message": "Booking cancelled successfully",
        **result,
        "note": "If you were CONFIRMED, the first waitlisted passenger has been auto-promoted.",
    }


@router.get("/{pnr}/history")
async def get_booking_history(pnr: str, current_user: dict = Depends(get_current_user)):
    """Get status history for a PNR."""
    async with get_db() as db:
        await db.execute("SELECT id, user_id FROM bookings WHERE pnr = %s", (pnr,))
        booking = await db.fetchone()

    if not booking:
        raise HTTPException(status_code=404, detail=f"PNR {pnr} not found")
    if current_user["role"] != "ADMIN" and booking["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    async with get_db() as db:
        await db.execute(
            """
            SELECT old_status, new_status, reason, changed_at
            FROM booking_status_history
            WHERE booking_id = %s
            ORDER BY changed_at ASC
            """,
            (booking["id"],),
        )
        history = await db.fetchall()

    for h in history:
        if h.get("changed_at") and hasattr(h["changed_at"], "isoformat"):
            h["changed_at"] = h["changed_at"].isoformat()

    return {"pnr": pnr, "history": [dict(h) for h in history]}


@router.get("")
async def get_my_bookings(current_user: dict = Depends(get_current_user)):
    """Get all bookings for the current user."""
    async with get_db() as db:
        await db.execute(
            """
            SELECT b.pnr, b.booking_status, b.journey_date, b.travel_class,
                   b.total_fare, b.booking_time,
                   t.train_number, t.train_name,
                   s_src.station_name AS source_name, s_dst.station_name AS dest_name
            FROM bookings b
            JOIN trains t ON b.train_id = t.id
            JOIN stations s_src ON b.source_station = s_src.station_code
            JOIN stations s_dst ON b.dest_station = s_dst.station_code
            WHERE b.user_id = %s
            ORDER BY b.booking_time DESC
            LIMIT 50
            """,
            (current_user["id"],),
        )
        bookings = await db.fetchall()

    for b in bookings:
        for key in ["booking_time"]:
            if b.get(key) and hasattr(b[key], "isoformat"):
                b[key] = b[key].isoformat()
        if b.get("journey_date") and hasattr(b["journey_date"], "isoformat"):
            b["journey_date"] = b["journey_date"].isoformat()

    return {"total": len(bookings), "bookings": [dict(b) for b in bookings]}
