"""SmartRail AI+ — PNR Enquiry Route"""

import logging
from fastapi import APIRouter, HTTPException
from app.core.database import get_db

logger = logging.getLogger("smartrail.pnr")
router = APIRouter(prefix="/pnr")


@router.get("/{pnr}")
async def pnr_enquiry(pnr: str):
    """
    Public PNR status enquiry — no authentication required.
    Returns booking status, train info, passenger details (name masked).
    """
    if len(pnr) != 10 or not pnr.isdigit():
        raise HTTPException(status_code=400, detail="PNR must be a 10-digit number")

    async with get_db() as db:
        await db.execute(
            """
            SELECT b.pnr, b.booking_status, b.journey_date, b.travel_class,
                   b.source_station, b.dest_station, b.total_fare, b.booking_time,
                   t.train_number, t.train_name, t.departure_time, t.arrival_time,
                   t.journey_duration_mins,
                   s_src.station_name AS source_name, s_dst.station_name AS dest_name
            FROM bookings b
            JOIN trains t ON b.train_id = t.id
            JOIN stations s_src ON b.source_station = s_src.station_code
            JOIN stations s_dst ON b.dest_station = s_dst.station_code
            WHERE b.pnr = %s
            """,
            (pnr,),
        )
        booking = await db.fetchone()

    if not booking:
        raise HTTPException(status_code=404, detail=f"PNR {pnr} not found in the system")

    async with get_db() as db:
        await db.execute(
            """
            SELECT bp.status, bp.coach_number, bp.seat_number, bp.berth_allotted,
                   bp.waitlist_number, bp.passenger_fare,
                   p.full_name, p.age, p.gender
            FROM booking_passengers bp
            JOIN passengers p ON bp.passenger_id = p.id
            WHERE bp.booking_id = (SELECT id FROM bookings WHERE pnr = %s)
            """,
            (pnr,),
        )
        passengers = await db.fetchall()

    async with get_db() as db:
        await db.execute(
            """
            SELECT old_status, new_status, reason, changed_at
            FROM booking_status_history
            WHERE booking_id = (SELECT id FROM bookings WHERE pnr = %s)
            ORDER BY changed_at ASC
            """,
            (pnr,),
        )
        history = await db.fetchall()

    # Mask passenger names (show first 3 chars + ***)
    pax_list = []
    for p in passengers:
        name = p.get("full_name", "")
        masked = name[:3] + "***" if len(name) > 3 else name
        pax_list.append({
            "name": masked,
            "age": p["age"],
            "gender": p["gender"],
            "status": p["status"],
            "coach": p["coach_number"],
            "seat": p["seat_number"],
            "berth": p["berth_allotted"],
            "waitlist_number": p["waitlist_number"],
            "fare": float(p["passenger_fare"] or 0),
        })

    for key in ["booking_time"]:
        if booking.get(key) and hasattr(booking[key], "isoformat"):
            booking[key] = booking[key].isoformat()
    for key in ["departure_time", "arrival_time"]:
        if booking.get(key):
            booking[key] = str(booking[key])
    if booking.get("journey_date") and hasattr(booking["journey_date"], "isoformat"):
        booking["journey_date"] = booking["journey_date"].isoformat()

    for h in history:
        if h.get("changed_at") and hasattr(h["changed_at"], "isoformat"):
            h["changed_at"] = h["changed_at"].isoformat()

    dur = booking.get("journey_duration_mins", 0) or 0
    return {
        "pnr": pnr,
        "booking_status": booking["booking_status"],
        "journey_date": booking["journey_date"],
        "travel_class": booking["travel_class"],
        "source": {"code": booking["source_station"], "name": booking["source_name"]},
        "destination": {"code": booking["dest_station"], "name": booking["dest_name"]},
        "total_fare": float(booking["total_fare"] or 0),
        "booking_time": booking["booking_time"],
        "train": {
            "number": booking["train_number"],
            "name": booking["train_name"],
            "departure_time": booking["departure_time"],
            "arrival_time": booking["arrival_time"],
            "duration": f"{dur // 60}h {dur % 60}m",
        },
        "passengers": pax_list,
        "status_history": [dict(h) for h in history],
        "disclaimer": "Demonstration system. Not connected to real railway services.",
    }
