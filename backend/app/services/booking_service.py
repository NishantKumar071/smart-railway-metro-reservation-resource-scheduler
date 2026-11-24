"""
SmartRail AI+ — Booking Service
Core booking logic executed inside worker threads.
Implements DBMS concepts: transactions, SELECT FOR UPDATE, row-level locking.
"""

import logging
import random
import string
import time
import uuid
from datetime import date, datetime
from typing import Dict, List, Optional

logger = logging.getLogger("smartrail.booking")


def generate_pnr() -> str:
    """Generate a 10-digit PNR number."""
    return "".join(random.choices(string.digits, k=10))


def _do_book_ticket(booking_data: dict) -> dict:
    """
    Core booking function — runs in a worker thread.

    DBMS Concepts Demonstrated:
    - BEGIN TRANSACTION / COMMIT / ROLLBACK
    - SELECT ... FOR UPDATE (row-level locking)
    - Parameterized queries (SQL injection prevention)
    - Data integrity checks before allocation
    - Atomic seat decrement

    Returns booking result dict.
    """
    from app.core.database import get_sync_db

    conn = get_sync_db()
    cursor = conn.cursor()
    result = {}
    txn_id = str(uuid.uuid4())

    try:
        # ── BEGIN TRANSACTION ─────────────────────────────────────────────────
        conn.begin()

        # Log transaction start
        cursor.execute(
            """
            INSERT INTO db_transactions_log
            (transaction_id, operation_type, table_affected, status, initiated_by)
            VALUES (%s, 'BOOKING', 'bookings,seat_inventory,booking_passengers', 'STARTED', %s)
            """,
            (txn_id, booking_data.get("user_id")),
        )

        # ── STEP 1: Lock seat inventory row (SELECT FOR UPDATE) ───────────────
        cursor.execute(
            """
            SELECT si.id, si.available_seats, si.confirmed_count,
                   si.waitlist_count, si.max_waitlist, si.total_seats
            FROM seat_inventory si
            WHERE si.train_id = %s
              AND si.coach_id = %s
              AND si.journey_date = %s
            FOR UPDATE
            """,
            (
                booking_data["train_id"],
                booking_data["coach_id"],
                booking_data["journey_date"],
            ),
        )
        inventory = cursor.fetchone()

        if not inventory:
            raise ValueError("No seat inventory found for this train/class/date")

        available = inventory["available_seats"]
        wl_count  = inventory["waitlist_count"]
        max_wl    = inventory["max_waitlist"]

        # ── STEP 2: Determine booking status ─────────────────────────────────
        if available > 0:
            booking_status = "CONFIRMED"
            waitlist_number = None
        elif wl_count < max_wl:
            booking_status = "WAITING"
            waitlist_number = wl_count + 1
        else:
            raise ValueError(
                f"No seats available and waitlist is full (WL/{max_wl}). Try a different date or class."
            )

        # ── STEP 3: Generate unique PNR ───────────────────────────────────────
        pnr = None
        for _ in range(10):
            candidate = generate_pnr()
            cursor.execute("SELECT id FROM bookings WHERE pnr = %s", (candidate,))
            if not cursor.fetchone():
                pnr = candidate
                break
        if not pnr:
            raise ValueError("Could not generate unique PNR. Please retry.")

        # ── STEP 4: Insert booking record ─────────────────────────────────────
        priority_map = {"EMERGENCY": 1, "SENIOR_CITIZEN": 2, "TATKAL": 3, "GENERAL": 4, "LADIES": 4}
        priority_level = priority_map.get(booking_data.get("quota", "GENERAL").upper(), 4)

        cursor.execute(
            """
            INSERT INTO bookings
            (pnr, user_id, train_id, coach_id, journey_date,
             source_station, dest_station, travel_class, quota,
             priority_level, booking_status, total_fare, payment_status,
             request_id, processing_thread)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'PAID', %s, %s)
            """,
            (
                pnr,
                booking_data["user_id"],
                booking_data["train_id"],
                booking_data["coach_id"],
                booking_data["journey_date"],
                booking_data["source_station"],
                booking_data["dest_station"],
                booking_data["travel_class"],
                booking_data.get("quota", "GENERAL"),
                priority_level,
                booking_status,
                booking_data["total_fare"],
                booking_data.get("request_id", str(uuid.uuid4())),
                booking_data.get("worker_thread_id", 0),
            ),
        )
        booking_id = cursor.lastrowid

        # ── STEP 5: Allocate physical seat (if confirmed) ─────────────────────
        seat_number = None
        berth_allotted = None

        if booking_status == "CONFIRMED":
            # Find an unoccupied physical seat
            preferred_berth = booking_data.get("preferred_berth", "LOWER")
            cursor.execute(
                """
                SELECT ps.id, ps.seat_number, ps.berth_type
                FROM physical_seats ps
                WHERE ps.coach_id = %s
                  AND ps.id NOT IN (
                      SELECT bp.seat_id FROM booking_passengers bp
                      JOIN bookings b ON bp.booking_id = b.id
                      WHERE b.coach_id = %s
                        AND b.journey_date = %s
                        AND bp.status IN ('CONFIRMED','RAC')
                        AND bp.seat_id IS NOT NULL
                  )
                ORDER BY
                    CASE ps.berth_type
                        WHEN %s THEN 0
                        ELSE 1
                    END, ps.id
                LIMIT 1
                FOR UPDATE
                """,
                (
                    booking_data["coach_id"],
                    booking_data["coach_id"],
                    booking_data["journey_date"],
                    preferred_berth,
                ),
            )
            seat_row = cursor.fetchone()
            if seat_row:
                seat_id = seat_row["id"]
                seat_number = seat_row["seat_number"]
                berth_allotted = seat_row["berth_type"]
            else:
                seat_id = None
                berth_allotted = None
        else:
            seat_id = None

        # ── STEP 6: Insert booking_passengers ────────────────────────────────
        passengers = booking_data.get("passengers", [])
        for pax in passengers:
            # Insert or get passenger
            cursor.execute(
                """
                INSERT INTO passengers (user_id, full_name, age, gender, id_type, phone)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    booking_data["user_id"],
                    pax["full_name"],
                    pax["age"],
                    pax.get("gender", "OTHER"),
                    pax.get("id_type", "AADHAAR"),
                    pax.get("phone", ""),
                ),
            )
            passenger_id = cursor.lastrowid

            fare_per_pax = booking_data["total_fare"] / max(len(passengers), 1)

            cursor.execute(
                """
                INSERT INTO booking_passengers
                (booking_id, passenger_id, seat_id, berth_type, berth_allotted,
                 coach_number, seat_number, waitlist_number, passenger_fare, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    booking_id,
                    passenger_id,
                    seat_id,
                    booking_data.get("preferred_berth", "NO_PREFERENCE"),
                    berth_allotted,
                    booking_data["coach_number"],
                    seat_number,
                    waitlist_number,
                    round(fare_per_pax, 2),
                    booking_status,
                ),
            )

        # ── STEP 7: Update seat inventory atomically ──────────────────────────
        if booking_status == "CONFIRMED":
            cursor.execute(
                """
                UPDATE seat_inventory
                SET confirmed_count  = confirmed_count + 1,
                    available_seats  = available_seats - 1,
                    updated_at       = NOW()
                WHERE id = %s AND available_seats > 0
                """,
                (inventory["id"],),
            )
            if cursor.rowcount == 0:
                raise ValueError("Race condition: seat was taken by another booking. Please retry.")
        else:
            cursor.execute(
                """
                UPDATE seat_inventory
                SET waitlist_count = waitlist_count + 1,
                    updated_at     = NOW()
                WHERE id = %s
                """,
                (inventory["id"],),
            )

        # ── STEP 8: Status history ────────────────────────────────────────────
        cursor.execute(
            """
            INSERT INTO booking_status_history (booking_id, old_status, new_status, reason)
            VALUES (%s, NULL, %s, 'Initial booking')
            """,
            (booking_id, booking_status),
        )

        # ── STEP 9: Update transaction log ────────────────────────────────────
        cursor.execute(
            """
            UPDATE db_transactions_log
            SET status = 'COMMITTED', rows_affected = %s
            WHERE transaction_id = %s
            """,
            (len(passengers) + 2, txn_id),
        )

        # ── COMMIT ────────────────────────────────────────────────────────────
        conn.commit()

        result = {
            "pnr": pnr,
            "booking_id": booking_id,
            "booking_status": booking_status,
            "seat_number": seat_number,
            "berth_allotted": berth_allotted,
            "coach_number": booking_data["coach_number"],
            "waitlist_number": waitlist_number,
            "total_fare": booking_data["total_fare"],
            "transaction_id": txn_id,
        }
        logger.info(
            f"Booking COMMITTED | PNR={pnr} | Status={booking_status} | "
            f"TxnID={txn_id[:8]}"
        )

    except Exception as exc:
        conn.rollback()
        # Update transaction log
        try:
            cursor.execute(
                """
                UPDATE db_transactions_log
                SET status = 'ROLLED_BACK', error_message = %s
                WHERE transaction_id = %s
                """,
                (str(exc)[:500], txn_id),
            )
            conn.commit()
        except Exception:
            pass
        logger.error(f"Booking ROLLED BACK | TxnID={txn_id[:8]} | Error: {exc}")
        raise

    finally:
        cursor.close()

    return result


def _do_cancel_ticket(pnr: str, user_id: int, reason: str = "User requested") -> dict:
    """
    Cancel a booking and promote waitlisted passengers.

    DBMS Concepts: Transaction, SELECT FOR UPDATE, cascade updates
    """
    from app.core.database import get_sync_db

    conn = get_sync_db()
    cursor = conn.cursor()
    txn_id = str(uuid.uuid4())

    try:
        conn.begin()

        cursor.execute(
            """
            SELECT b.id, b.pnr, b.booking_status, b.train_id, b.coach_id,
                   b.journey_date, b.total_fare, b.user_id
            FROM bookings b
            WHERE b.pnr = %s
            FOR UPDATE
            """,
            (pnr,),
        )
        booking = cursor.fetchone()

        if not booking:
            raise ValueError(f"PNR {pnr} not found")
        if booking["user_id"] != user_id:
            raise PermissionError("You can only cancel your own bookings")
        if booking["booking_status"] == "CANCELLED":
            raise ValueError(f"PNR {pnr} is already cancelled")

        was_confirmed = booking["booking_status"] == "CONFIRMED"

        # Cancel the booking
        cursor.execute(
            """
            UPDATE bookings
            SET booking_status = 'CANCELLED',
                cancellation_time = NOW(),
                cancellation_reason = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (reason, booking["id"]),
        )

        # Cancel all passengers
        cursor.execute(
            """
            UPDATE booking_passengers
            SET status = 'CANCELLED', updated_at = NOW()
            WHERE booking_id = %s
            """,
            (booking["id"],),
        )

        # Release seat inventory
        if was_confirmed:
            cursor.execute(
                """
                UPDATE seat_inventory
                SET confirmed_count = GREATEST(0, confirmed_count - 1),
                    available_seats = available_seats + 1,
                    updated_at = NOW()
                WHERE train_id = %s AND coach_id = %s AND journey_date = %s
                """,
                (booking["train_id"], booking["coach_id"], booking["journey_date"]),
            )

            # Promote first waitlisted passenger
            cursor.execute(
                """
                SELECT b2.id AS booking_id, b2.pnr, bp2.id AS bp_id, bp2.waitlist_number
                FROM bookings b2
                JOIN booking_passengers bp2 ON b2.id = bp2.booking_id
                WHERE b2.train_id = %s
                  AND b2.coach_id = %s
                  AND b2.journey_date = %s
                  AND b2.booking_status = 'WAITING'
                  AND bp2.status = 'WAITING'
                ORDER BY bp2.waitlist_number ASC
                LIMIT 1
                FOR UPDATE
                """,
                (booking["train_id"], booking["coach_id"], booking["journey_date"]),
            )
            next_wl = cursor.fetchone()

            if next_wl:
                cursor.execute(
                    "UPDATE bookings SET booking_status = 'CONFIRMED', updated_at = NOW() WHERE id = %s",
                    (next_wl["booking_id"],),
                )
                cursor.execute(
                    "UPDATE booking_passengers SET status = 'CONFIRMED', waitlist_number = NULL, updated_at = NOW() WHERE id = %s",
                    (next_wl["bp_id"],),
                )
                cursor.execute(
                    """
                    UPDATE seat_inventory
                    SET confirmed_count = confirmed_count + 1,
                        available_seats = available_seats - 1,
                        waitlist_count = GREATEST(0, waitlist_count - 1),
                        updated_at = NOW()
                    WHERE train_id = %s AND coach_id = %s AND journey_date = %s
                    """,
                    (booking["train_id"], booking["coach_id"], booking["journey_date"]),
                )
                cursor.execute(
                    """
                    INSERT INTO booking_status_history (booking_id, old_status, new_status, reason)
                    VALUES (%s, 'WAITING', 'CONFIRMED', 'Promoted from waitlist due to cancellation of PNR %s')
                    """,
                    (next_wl["booking_id"], pnr),
                )
                promoted_pnr = next_wl["pnr"]
            else:
                promoted_pnr = None
        else:
            # WL cancellation — just decrement WL count
            cursor.execute(
                """
                UPDATE seat_inventory
                SET waitlist_count = GREATEST(0, waitlist_count - 1),
                    updated_at = NOW()
                WHERE train_id = %s AND coach_id = %s AND journey_date = %s
                """,
                (booking["train_id"], booking["coach_id"], booking["journey_date"]),
            )
            promoted_pnr = None

        cursor.execute(
            """
            INSERT INTO booking_status_history (booking_id, old_status, new_status, reason)
            VALUES (%s, %s, 'CANCELLED', %s)
            """,
            (booking["id"], booking["booking_status"], reason),
        )

        conn.commit()
        return {
            "pnr": pnr,
            "cancelled": True,
            "refund_amount": booking["total_fare"],
            "promoted_pnr": promoted_pnr,
            "transaction_id": txn_id,
        }

    except Exception as exc:
        conn.rollback()
        raise
    finally:
        cursor.close()
