"""
SmartRail AI+ — API Routes: Trains Search & Details
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.core.database import get_db

logger = logging.getLogger("smartrail.trains")
router = APIRouter(prefix="/trains")


@router.get("/search")
async def search_trains(
    source: str = Query(..., description="Source station code (e.g. NDLS)"),
    destination: str = Query(..., description="Destination station code (e.g. HWH)"),
    journey_date: date = Query(..., description="Journey date (YYYY-MM-DD)"),
    travel_class: Optional[str] = Query(None, description="Travel class: SL/3AC/2AC/1AC/CC"),
    quota: Optional[str] = Query("GENERAL", description="Quota: GENERAL/TATKAL/SENIOR_CITIZEN"),
):
    """
    Search available trains between source and destination on a given date.
    Returns real data from the database — no fake results.
    """
    async with get_db() as db:
        # Find trains that have both source and destination in route
        # Join stations by searched source/destination codes (not train's terminus)
        await db.execute(
            """
            SELECT DISTINCT
                t.id, t.train_number, t.train_name, t.train_type,
                t.source_station, t.dest_station,
                tr_src.departure_time AS departure_time,
                tr_dst.arrival_time AS arrival_time,
                t.journey_duration_mins,
                s_search_src.station_name AS source_name,
                s_search_dst.station_name AS dest_name
            FROM trains t
            JOIN train_routes tr_src ON t.id = tr_src.train_id AND tr_src.station_code = %s
            JOIN train_routes tr_dst ON t.id = tr_dst.train_id AND tr_dst.station_code = %s
            JOIN stations s_search_src ON s_search_src.station_code = %s
            JOIN stations s_search_dst ON s_search_dst.station_code = %s
            WHERE t.is_active = 1
              AND tr_src.stop_number < tr_dst.stop_number
            ORDER BY tr_src.departure_time
            """,
            (source.upper(), destination.upper(), source.upper(), destination.upper()),
        )
        trains = await db.fetchall()

    if not trains:
        return {
            "source": source.upper(),
            "destination": destination.upper(),
            "journey_date": str(journey_date),
            "trains": [],
            "message": "No trains found for this route. Try different stations.",
        }

    results = []
    for train in trains:
        async with get_db() as db:
            # Get availability for each coach class
            coach_query = """
                SELECT tc.coach_type, tc.coach_number, tc.id AS coach_id,
                       si.available_seats, si.confirmed_count, si.waitlist_count,
                       si.max_waitlist,
                       ROUND(tc.base_fare + (tc.fare_per_km * 1000), 2) AS estimated_fare
                FROM train_coaches tc
                LEFT JOIN seat_inventory si
                    ON si.coach_id = tc.id AND si.journey_date = %s
                WHERE tc.train_id = %s
            """
            args = [str(journey_date), train["id"]]
            if travel_class:
                coach_query += " AND tc.coach_type = %s"
                args.append(travel_class.upper())

            await db.execute(coach_query, args)
            coaches = await db.fetchall()

        # Serialize datetime
        dep_time = str(train["departure_time"]) if train["departure_time"] else "N/A"
        arr_time = str(train["arrival_time"]) if train["arrival_time"] else "N/A"
        dur_hrs = train["journey_duration_mins"] // 60
        dur_mins = train["journey_duration_mins"] % 60

        coach_info = []
        for c in coaches:
            avail = c["available_seats"] if c["available_seats"] is not None else 0
            coach_info.append({
                "coach_id": c["coach_id"],
                "coach_number": c["coach_number"],
                "coach_type": c["coach_type"],
                "available_seats": avail,
                "confirmed_count": c["confirmed_count"] or 0,
                "waitlist_count": c["waitlist_count"] or 0,
                "max_waitlist": c["max_waitlist"] or 0,
                "estimated_fare": float(c["estimated_fare"] or 0),
                "availability_status": (
                    "AVAILABLE" if avail > 0
                    else "WAITLIST" if (c["waitlist_count"] or 0) < (c["max_waitlist"] or 0)
                    else "FULLY_BOOKED"
                ),
            })

        results.append({
            "train_id": train["id"],
            "train_number": train["train_number"],
            "train_name": train["train_name"],
            "train_type": train["train_type"],
            "source_code": source.upper(),
            "source_name": train["source_name"],
            "dest_code": destination.upper(),
            "dest_name": train["dest_name"],
            "departure_time": dep_time,
            "arrival_time": arr_time,
            "duration": f"{dur_hrs}h {dur_mins}m",
            "journey_duration_mins": train["journey_duration_mins"],
            "coaches": coach_info,
            "disclaimer": "Demonstration data only. Not connected to real railway systems.",
        })

    return {
        "source": source.upper(),
        "destination": destination.upper(),
        "journey_date": str(journey_date),
        "total_trains": len(results),
        "trains": results,
    }


@router.get("/{train_number}")
async def get_train_details(train_number: str):
    """Get full details for a specific train including route and coaches."""
    async with get_db() as db:
        await db.execute(
            """
            SELECT t.*, s_src.station_name AS source_name, s_dst.station_name AS dest_name
            FROM trains t
            JOIN stations s_src ON t.source_station = s_src.station_code
            JOIN stations s_dst ON t.dest_station = s_dst.station_code
            WHERE t.train_number = %s
            """,
            (train_number,),
        )
        train = await db.fetchone()

    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_number} not found")

    async with get_db() as db:
        await db.execute(
            """
            SELECT tr.stop_number, tr.station_code, s.station_name, s.city,
                   tr.arrival_time, tr.departure_time, tr.halt_minutes, tr.distance_km, tr.day_offset
            FROM train_routes tr
            JOIN stations s ON tr.station_code = s.station_code
            WHERE tr.train_id = %s
            ORDER BY tr.stop_number
            """,
            (train["id"],),
        )
        route = await db.fetchall()

    async with get_db() as db:
        await db.execute(
            "SELECT * FROM train_coaches WHERE train_id = %s ORDER BY coach_type, coach_number",
            (train["id"],),
        )
        coaches = await db.fetchall()

    # Serialize
    for item in route:
        for k in ["arrival_time", "departure_time"]:
            if item.get(k):
                item[k] = str(item[k])
    for c in coaches:
        if c.get("created_at"):
            c["created_at"] = str(c["created_at"])

    dep = str(train["departure_time"]) if train["departure_time"] else "N/A"
    arr = str(train["arrival_time"]) if train["arrival_time"] else "N/A"
    dur_hrs = (train["journey_duration_mins"] or 0) // 60
    dur_mins = (train["journey_duration_mins"] or 0) % 60

    return {
        "train_id": train["id"],
        "train_number": train["train_number"],
        "train_name": train["train_name"],
        "train_type": train["train_type"],
        "source": {"code": train["source_station"], "name": train["source_name"]},
        "destination": {"code": train["dest_station"], "name": train["dest_name"]},
        "departure_time": dep,
        "arrival_time": arr,
        "duration": f"{dur_hrs}h {dur_mins}m",
        "runs_on": train["runs_on"],
        "is_active": bool(train["is_active"]),
        "route": [dict(r) for r in route],
        "coaches": [dict(c) for c in coaches],
        "disclaimer": "Demonstration data. Not connected to live Indian Railways systems.",
    }


@router.get("/availability/{train_number}")
async def get_seat_availability(
    train_number: str,
    journey_date: date = Query(...),
):
    """Get seat availability for all classes on a given date."""
    async with get_db() as db:
        await db.execute(
            """
            SELECT si.*, tc.coach_type, tc.coach_number, tc.total_seats AS coach_total,
                   t.train_number, t.train_name
            FROM seat_inventory si
            JOIN train_coaches tc ON si.coach_id = tc.id
            JOIN trains t ON si.train_id = t.id
            WHERE t.train_number = %s AND si.journey_date = %s
            ORDER BY tc.coach_type, tc.coach_number
            """,
            (train_number, str(journey_date)),
        )
        rows = await db.fetchall()

    for r in rows:
        for k in ["created_at", "updated_at"]:
            if r.get(k):
                r[k] = str(r[k])

    return {
        "train_number": train_number,
        "journey_date": str(journey_date),
        "availability": [dict(r) for r in rows],
    }


@router.get("/stations")
async def get_all_stations():
    """Get all railway stations in the system."""
    async with get_db() as db:
        await db.execute(
            """
            SELECT station_code, station_name, city, state, zone, is_major
            FROM stations
            ORDER BY is_major DESC, station_name ASC
            """
        )
        stations = await db.fetchall()
    return {"total": len(stations), "stations": [dict(s) for s in stations]}

