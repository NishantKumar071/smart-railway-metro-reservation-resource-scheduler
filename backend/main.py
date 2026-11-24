"""
SmartRail AI+ — Main Backend Application
=========================================
Implements OS concepts in Python:
  - Multithreading (threading.Thread)
  - Producer-Consumer with bounded queue
  - Priority Scheduling (heapq-based priority queue)
  - Mutex/Lock, Condition Variables, Atomic variables
  - Deadlock prevention via consistent lock ordering

University: Graphic Era (Deemed to be University), Dehradun
Team: OSDBMS-V-2026-T281
"""

import os
import sys

# Ensure backend directory is first in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import signal
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load .env early
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from app.core.database import engine, init_db
from app.core.scheduler import booking_scheduler
from app.api.routes import auth, trains, bookings, pnr, waitlist, telemetry, admin
from app.core.logger import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger("smartrail")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("SmartRail AI+ Backend starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Workers: {settings.WORKER_THREAD_COUNT} threads")
    logger.info("=" * 60)

    # Initialize database
    try:
        await init_db()
        logger.info("✓ Database connection established")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        logger.error("  → Check DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD in .env")
        # Continue startup; individual requests will fail gracefully

    # Start OS-concept worker pool
    booking_scheduler.start()
    logger.info(f"✓ Booking scheduler started ({settings.WORKER_THREAD_COUNT} worker threads)")
    logger.info("✓ SmartRail AI+ Backend is READY")
    logger.info(f"  API: http://localhost:{settings.BACKEND_PORT}")
    logger.info(f"  Docs: http://localhost:{settings.BACKEND_PORT}/docs")

    yield

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("SmartRail AI+ Backend shutting down...")
    booking_scheduler.stop()
    logger.info("✓ Scheduler stopped cleanly")


# Create FastAPI application
app = FastAPI(
    title="SmartRail AI+ Backend API",
    description=(
        "SmartRail AI+ — Smart Railway Reservation & Resource Scheduler\n\n"
        "**Academic Project**: B.Tech 5th Semester — OS, DBMS, AI/ML\n"
        "**University**: Graphic Era (Deemed to be University), Dehradun\n"
        "**Team**: OSDBMS-V-2026-T281\n\n"
        "⚠️ DISCLAIMER: This is an academic demonstration system. "
        "It is NOT connected to live IRCTC or Indian Railways systems. "
        "All data is fictional and created for educational purposes only."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── API ROUTES ────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api",     tags=["Authentication"])
app.include_router(trains.router,    prefix="/api",     tags=["Trains"])
app.include_router(bookings.router,  prefix="/api",     tags=["Bookings"])
app.include_router(pnr.router,       prefix="/api",     tags=["PNR Enquiry"])
app.include_router(waitlist.router,  prefix="/api",     tags=["Waitlist"])
app.include_router(telemetry.router, prefix="/api",     tags=["OS Telemetry"])
app.include_router(admin.router,     prefix="/api",     tags=["Admin"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from app.core.database import check_db_connection
    from app.core.scheduler import booking_scheduler
    db_ok = await check_db_connection()
    sched_status = booking_scheduler.get_status()
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": "SmartRail AI+ Backend",
        "version": "1.0.0",
        "database": "connected" if db_ok else "disconnected",
        "scheduler": sched_status,
        "disclaimer": "Academic demonstration system only. Not connected to real railway services.",
    }


@app.get("/api/stations", tags=["Stations"])
async def get_stations():
    """Get all railway stations."""
    from app.core.database import get_db
    async with get_db() as db:
        await db.execute("SELECT station_code, station_name, city, state, zone, is_major FROM stations ORDER BY is_major DESC, station_name ASC")
        rows = await db.fetchall()
    return {"total": len(rows), "stations": [dict(r) for r in rows]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        log_level="info",
    )
