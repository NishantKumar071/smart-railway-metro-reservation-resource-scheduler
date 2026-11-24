"""
SmartRail AI+ — Unified Database Layer
Dual-mode:
1. Connects to MySQL 8.0 (InnoDB) if server is available and credentials in .env are valid.
2. Automatically falls back to an embedded SQLite database pre-seeded with all
   stations, trains, coaches, seats, and users if MySQL is unreachable or credentials are not yet configured.

This guarantees 100% immediate functionality out-of-the-box.
"""

import os
import re
import uuid
import datetime
import sqlite3
import logging
from typing import Optional, AsyncGenerator, Any, Dict, List
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger("smartrail.db")

# Connection mode
_use_sqlite: bool = False
_sqlite_db_path: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "smartrail_embedded.db")

# MySQL Pool (when available)
_mysql_pool = None

# Custom SQLite helper for DictCursor and MySQL function compatibility
def _sqlite_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _sqlite_curdate():
    return datetime.date.today().isoformat()

def _sqlite_uuid():
    return str(uuid.uuid4())

def _sqlite_date_add(d_str, days):
    try:
        base = datetime.date.fromisoformat(str(d_str))
        return (base + datetime.timedelta(days=int(days))).isoformat()
    except Exception:
        return d_str

def _get_sqlite_connection():
    conn = sqlite3.connect(_sqlite_db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.create_function("NOW", 0, _sqlite_now)
    conn.create_function("CURDATE", 0, _sqlite_curdate)
    conn.create_function("UUID", 0, _sqlite_uuid)
    conn.create_function("GREATEST", 2, max)
    conn.create_function("LEAST", 2, min)
    conn.create_function("DATE_ADD", 2, _sqlite_date_add)
    return conn

class SQLiteCursorAdapter:
    """Wraps SQLite cursor to mimic MySQL DictCursor and parameter syntax."""
    def __init__(self, conn):
        self._conn = conn
        self._cur = conn.cursor()
        self.lastrowid = None
        self.rowcount = 0

    def _adapt_query(self, query: str) -> str:
        # Replace MySQL DATE_SUB(NOW(), INTERVAL ...) with SQLite date string comparison
        q = re.sub(
            r"DATE_SUB\s*\(\s*NOW\(\)\s*,\s*INTERVAL\s+(\d+)\s+HOUR\s*\)",
            r"datetime('now', '-\1 hours')",
            query,
            flags=re.IGNORECASE
        )
        q = re.sub(
            r"DATE_ADD\s*\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+(\d+)\s+DAY\s*\)",
            r"date('now', '+\1 days')",
            q,
            flags=re.IGNORECASE
        )
        # Strip FOR UPDATE since SQLite has database-level locks
        q = re.sub(r"\s+FOR\s+UPDATE", "", q, flags=re.IGNORECASE)
        # Convert %s placeholders to ?
        q = q.replace("%s", "?")
        return q

    async def execute(self, query: str, args=None):
        adapted = self._adapt_query(query)
        try:
            if args:
                self._cur.execute(adapted, args)
            else:
                self._cur.execute(adapted)
            self.lastrowid = self._cur.lastrowid
            self.rowcount = self._cur.rowcount
            return self
        except Exception as e:
            logger.debug(f"SQLite execute error on [{adapted}]: {e}")
            raise

    async def fetchone(self) -> Optional[Dict[str, Any]]:
        row = self._cur.fetchone()
        if row is None:
            return None
        return dict(row)

    async def fetchall(self) -> List[Dict[str, Any]]:
        rows = self._cur.fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self._cur.close()


def _init_sqlite_schema(conn):
    """Seed embedded SQLite database with the full schema and demonstration data."""
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT,
        date_of_birth TEXT,
        gender TEXT DEFAULT 'OTHER',
        role TEXT DEFAULT 'PASSENGER',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        last_login TEXT
    );

    CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_code TEXT UNIQUE NOT NULL,
        station_name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        zone TEXT,
        latitude REAL,
        longitude REAL,
        is_major INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS trains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_number TEXT UNIQUE NOT NULL,
        train_name TEXT NOT NULL,
        train_type TEXT DEFAULT 'EXPRESS',
        source_station TEXT NOT NULL,
        dest_station TEXT NOT NULL,
        departure_time TEXT NOT NULL,
        arrival_time TEXT NOT NULL,
        journey_duration_mins INTEGER NOT NULL,
        runs_on TEXT DEFAULT '1234567',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS train_routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_id INTEGER NOT NULL,
        station_code TEXT NOT NULL,
        stop_number INTEGER NOT NULL,
        arrival_time TEXT,
        departure_time TEXT,
        halt_minutes INTEGER DEFAULT 0,
        distance_km REAL DEFAULT 0,
        day_offset INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS train_coaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_id INTEGER NOT NULL,
        coach_number TEXT NOT NULL,
        coach_type TEXT NOT NULL,
        total_seats INTEGER NOT NULL,
        berth_config TEXT,
        fare_per_km REAL DEFAULT 0.50,
        base_fare REAL DEFAULT 50.00,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS seat_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_id INTEGER NOT NULL,
        coach_id INTEGER NOT NULL,
        journey_date TEXT NOT NULL,
        total_seats INTEGER NOT NULL,
        confirmed_count INTEGER DEFAULT 0,
        rac_count INTEGER DEFAULT 0,
        waitlist_count INTEGER DEFAULT 0,
        max_waitlist INTEGER DEFAULT 20,
        available_seats INTEGER NOT NULL,
        fare_sl REAL,
        fare_3ac REAL,
        fare_2ac REAL,
        fare_1ac REAL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS physical_seats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coach_id INTEGER NOT NULL,
        seat_number TEXT NOT NULL,
        berth_type TEXT NOT NULL,
        is_window INTEGER DEFAULT 0,
        bay_number INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS passengers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        full_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        id_type TEXT DEFAULT 'AADHAAR',
        id_number TEXT,
        phone TEXT,
        is_senior INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pnr TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        train_id INTEGER NOT NULL,
        coach_id INTEGER NOT NULL,
        journey_date TEXT NOT NULL,
        source_station TEXT NOT NULL,
        dest_station TEXT NOT NULL,
        travel_class TEXT NOT NULL,
        quota TEXT DEFAULT 'GENERAL',
        priority_level INTEGER DEFAULT 4,
        booking_status TEXT DEFAULT 'CONFIRMED',
        total_fare REAL NOT NULL,
        payment_status TEXT DEFAULT 'PAID',
        booking_time TEXT DEFAULT (datetime('now')),
        cancellation_time TEXT,
        cancellation_reason TEXT,
        request_id TEXT,
        processing_thread INTEGER,
        processing_time_ms INTEGER,
        ai_recommendation INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS booking_passengers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        passenger_id INTEGER NOT NULL,
        seat_id INTEGER,
        berth_type TEXT,
        berth_allotted TEXT,
        coach_number TEXT,
        seat_number TEXT,
        waitlist_number INTEGER,
        passenger_fare REAL,
        status TEXT DEFAULT 'CONFIRMED',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS booking_status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        reason TEXT,
        changed_by INTEGER,
        changed_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS db_transactions_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT NOT NULL,
        operation_type TEXT NOT NULL,
        table_affected TEXT,
        rows_affected INTEGER DEFAULT 0,
        status TEXT NOT NULL,
        error_message TEXT,
        duration_ms INTEGER,
        initiated_by INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS os_scheduling_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT NOT NULL,
        request_type TEXT,
        priority_level INTEGER DEFAULT 4,
        priority_name TEXT DEFAULT 'NORMAL',
        queue_wait_time_ms INTEGER DEFAULT 0,
        processing_time_ms INTEGER DEFAULT 0,
        total_time_ms INTEGER DEFAULT 0,
        worker_thread_id INTEGER,
        queue_position_at_entry INTEGER,
        result_status TEXT DEFAULT 'COMPLETED',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS ai_prediction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_type TEXT NOT NULL,
        input_data TEXT NOT NULL,
        output_data TEXT NOT NULL,
        model_version TEXT,
        prediction_score REAL,
        confidence_level TEXT DEFAULT 'MEDIUM',
        was_accurate INTEGER,
        user_id INTEGER,
        booking_id INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)

    # Check if users already seeded
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        # Seed users (passwords validate to Demo@123 via security.verify_password)
        cur.executescript("""
        INSERT OR IGNORE INTO users (id, email, username, password_hash, full_name, phone, role) VALUES
        (1, 'admin@smartrail.local', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUdfufCB7PLt3GS8UQ/fiFi.S', 'System Administrator', '9999999999', 'ADMIN'),
        (2, 'nishant@smartrail.local', 'nishant', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUdfufCB7PLt3GS8UQ/fiFi.S', 'Nishant Kumar', '9876543210', 'PASSENGER'),
        (3, 'robert@smartrail.local', 'robert', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUdfufCB7PLt3GS8UQ/fiFi.S', 'Robert Sandi Thomas', '9876543211', 'PASSENGER'),
        (4, 'demo_user@smartrail.local', 'demo_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUdfufCB7PLt3GS8UQ/fiFi.S', 'Demo Passenger', '9000000001', 'PASSENGER');

        INSERT OR IGNORE INTO stations (station_code, station_name, city, state, zone, latitude, longitude, is_major) VALUES
        ('NDLS', 'New Delhi Railway Station', 'New Delhi', 'Delhi', 'NR', 28.6428, 77.2197, 1),
        ('HWH', 'Howrah Junction', 'Howrah', 'West Bengal', 'ER', 22.5839, 88.3421, 1),
        ('DDN', 'Dehradun', 'Dehradun', 'Uttarakhand', 'NR', 30.3165, 78.0322, 1),
        ('BCT', 'Mumbai Central', 'Mumbai', 'Maharashtra', 'WR', 18.9690, 72.8205, 1),
        ('PNBE', 'Patna Junction', 'Patna', 'Bihar', 'ECR', 25.5941, 85.1376, 1),
        ('BPL', 'Bhopal Junction', 'Bhopal', 'Madhya Pradesh', 'WCR', 23.2599, 77.4126, 1),
        ('SBC', 'KSR Bengaluru City', 'Bangalore', 'Karnataka', 'SWR', 12.9771, 77.5713, 1),
        ('CNB', 'Kanpur Central', 'Kanpur', 'Uttar Pradesh', 'NCR', 26.4499, 80.3319, 1),
        ('HRW', 'Haridwar Junction', 'Haridwar', 'Uttarakhand', 'NR', 29.9457, 78.1642, 0);

        INSERT OR IGNORE INTO trains (id, train_number, train_name, train_type, source_station, dest_station, departure_time, arrival_time, journey_duration_mins) VALUES
        (1, '12001', 'Bhopal Shatabdi', 'SHATABDI', 'NDLS', 'BPL', '06:00:00', '13:55:00', 475),
        (2, '12301', 'Howrah Rajdhani', 'RAJDHANI', 'NDLS', 'HWH', '16:55:00', '10:00:00', 1025),
        (3, '12951', 'Mumbai Rajdhani', 'RAJDHANI', 'NDLS', 'BCT', '17:00:00', '08:35:00', 935),
        (7, '12017', 'Dehradun Shatabdi', 'SHATABDI', 'NDLS', 'DDN', '06:45:00', '11:50:00', 305),
        (8, '22691', 'Rajdhani Express', 'RAJDHANI', 'DDN', 'NDLS', '05:17:00', '08:35:00', 198);

        INSERT OR IGNORE INTO train_routes (train_id, station_code, stop_number, arrival_time, departure_time, halt_minutes, distance_km) VALUES
        (2, 'NDLS', 1, NULL, '16:55:00', 0, 0),
        (2, 'CNB', 2, '21:30:00', '21:35:00', 5, 440),
        (2, 'HWH', 3, '10:00:00', NULL, 0, 1450),
        (7, 'NDLS', 1, NULL, '06:45:00', 0, 0),
        (7, 'HRW', 2, '10:40:00', '10:42:00', 2, 260),
        (7, 'DDN', 3, '11:50:00', NULL, 0, 305),
        (8, 'DDN', 1, NULL, '05:17:00', 0, 0),
        (8, 'HRW', 2, '05:50:00', '05:52:00', 2, 54),
        (8, 'NDLS', 3, '08:35:00', NULL, 0, 305);

        INSERT OR IGNORE INTO train_coaches (id, train_id, coach_number, coach_type, total_seats, fare_per_km, base_fare) VALUES
        (1, 7, 'C1', 'CC', 78, 2.10, 300.00),
        (2, 7, 'EC', 'EC', 56, 3.50, 500.00),
        (7, 2, 'S1', 'SL', 72, 0.80, 100.00),
        (8, 2, 'B1', '3AC', 72, 1.90, 200.00),
        (9, 2, 'A1', '2AC', 46, 2.80, 350.00),
        (10, 2, 'H1', '1AC', 24, 4.50, 600.00);

        INSERT OR IGNORE INTO physical_seats (id, coach_id, seat_number, berth_type, is_window, bay_number) VALUES
        (1, 8, '1', 'LOWER', 1, 1),
        (2, 8, '2', 'MIDDLE', 0, 1),
        (3, 8, '3', 'UPPER', 0, 1),
        (4, 8, '4', 'LOWER', 1, 1),
        (5, 8, '5', 'MIDDLE', 0, 1),
        (6, 8, '6', 'UPPER', 0, 1),
        (7, 8, '7', 'SIDE_LOWER', 1, 1),
        (8, 8, '8', 'SIDE_UPPER', 0, 1);
        """)

        # Populate seat inventory for upcoming 60 days
        today = datetime.date.today()
        for offset in range(60):
            d_str = (today + datetime.timedelta(days=offset)).isoformat()
            cur.execute("""
            INSERT OR IGNORE INTO seat_inventory (train_id, coach_id, journey_date, total_seats, available_seats, confirmed_count, waitlist_count, max_waitlist)
            VALUES
            (2, 8, ?, 72, 28, 44, 0, 20),
            (2, 7, ?, 72, 35, 37, 0, 50),
            (7, 1, ?, 78, 42, 36, 0, 10),
            (7, 2, ?, 56, 18, 38, 0, 5)
            """, (d_str, d_str, d_str, d_str))

        # Sample initial bookings
        cur.executescript("""
        INSERT OR IGNORE INTO bookings (id, pnr, user_id, train_id, coach_id, journey_date, source_station, dest_station, travel_class, total_fare, booking_status)
        VALUES
        (1, '5101234567', 2, 2, 8, date('now', '+7 days'), 'NDLS', 'HWH', '3AC', 1245.00, 'CONFIRMED'),
        (2, '5109876543', 3, 7, 1, date('now', '+14 days'), 'NDLS', 'DDN', 'CC', 540.00, 'CONFIRMED');

        INSERT OR IGNORE INTO booking_passengers (booking_id, passenger_id, seat_id, berth_type, berth_allotted, coach_number, seat_number, passenger_fare, status)
        VALUES
        (1, 1, 1, 'LOWER', 'LOWER', 'B1', '1', 1245.00, 'CONFIRMED'),
        (2, 2, NULL, 'WINDOW', 'WINDOW', 'C1', '5', 540.00, 'CONFIRMED');

        INSERT OR IGNORE INTO os_scheduling_metrics (request_id, request_type, priority_level, priority_name, queue_wait_time_ms, processing_time_ms, total_time_ms, worker_thread_id, result_status)
        VALUES
        ('REQ-SAMPLE-1', 'BOOKING', 1, 'EMERGENCY', 2, 84, 86, 1, 'COMPLETED'),
        ('REQ-SAMPLE-2', 'BOOKING', 3, 'TATKAL', 4, 102, 106, 2, 'COMPLETED'),
        ('REQ-SAMPLE-3', 'BOOKING', 4, 'NORMAL', 12, 142, 154, 3, 'COMPLETED');
        """)
        conn.commit()


async def init_db() -> None:
    """Initialize database connection, falling back to SQLite if MySQL is unavailable."""
    global _use_sqlite, _mysql_pool

    # Try MySQL first if aiomysql is installed
    try:
        import aiomysql
        _mysql_pool = await aiomysql.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            db=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            charset="utf8mb4",
            autocommit=False,
            minsize=1,
            maxsize=10,
            connect_timeout=3,
        )
        logger.info(f"✓ Connected to MySQL database on {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        _use_sqlite = False
        return
    except Exception as e:
        logger.info(f"ℹ️ MySQL connection bypassed ({e}). Using embedded demonstration database.")
        _use_sqlite = True

    # Initialize SQLite database
    conn = _get_sqlite_connection()
    _init_sqlite_schema(conn)
    conn.close()
    logger.info(f"✓ Embedded demonstration database ready at {_sqlite_db_path}")


async def check_db_connection() -> bool:
    try:
        async with get_db() as db:
            await db.execute("SELECT 1")
        return True
    except Exception:
        return False


@asynccontextmanager
async def get_db() -> AsyncGenerator[Any, None]:
    """Get database cursor (MySQL DictCursor or SQLite adapter)."""
    global _use_sqlite, _mysql_pool

    if not _use_sqlite and _mysql_pool is not None:
        async with _mysql_pool.acquire() as conn:
            import aiomysql
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    yield cursor
                    await conn.commit()
                except Exception:
                    await conn.rollback()
                    raise
    else:
        conn = _get_sqlite_connection()
        adapter = SQLiteCursorAdapter(conn)
        try:
            yield adapter
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            adapter.close()
            conn.close()


def get_sync_db():
    """Get synchronous DB connection for OS worker threads."""
    global _use_sqlite
    if not _use_sqlite:
        try:
            import pymysql
            import pymysql.cursors
            return pymysql.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                db=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                charset="utf8mb4",
                autocommit=False,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=3,
            )
        except Exception:
            pass

    # SQLite sync connection wrapped
    class SyncSQLiteAdapter:
        def __init__(self):
            self.conn = _get_sqlite_connection()
            self.open = True

        def cursor(self):
            return SyncSQLiteCursor(self.conn)

        def begin(self):
            pass

        def commit(self):
            self.conn.commit()

        def rollback(self):
            self.conn.rollback()

        def close(self):
            self.open = False
            self.conn.close()

    class SyncSQLiteCursor:
        def __init__(self, conn):
            self.adapter = SQLiteCursorAdapter(conn)

        def execute(self, q, args=None):
            import asyncio
            # Synchronous execute
            adapted = self.adapter._adapt_query(q)
            if args:
                self.adapter._cur.execute(adapted, args)
            else:
                self.adapter._cur.execute(adapted)
            self.lastrowid = self.adapter._cur.lastrowid
            self.rowcount = self.adapter._cur.rowcount
            return self

        def fetchone(self):
            row = self.adapter._cur.fetchone()
            return dict(row) if row else None

        def fetchall(self):
            return [dict(r) for r in self.adapter._cur.fetchall()]

        def close(self):
            self.adapter.close()

    return SyncSQLiteAdapter()

engine = None
