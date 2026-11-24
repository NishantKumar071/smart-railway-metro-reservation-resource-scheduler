"""
SmartRail AI+ — Application Configuration
Reads settings from environment variables (.env file).
No external third-party pydantic_settings dependency required.
"""

import os
from typing import List

class Settings:
    # ── Database ──────────────────────────────────────────────────────────────
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_NAME: str = os.getenv("DB_NAME", "smartrail_db")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # ── Application ───────────────────────────────────────────────────────────
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", 8080))
    AI_SERVICE_PORT: int = int(os.getenv("AI_SERVICE_PORT", 8000))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", 3000))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_A_SECURE_RANDOM_KEY_IN_PRODUCTION")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "null",
        "*",
    ]

    # ── AI Service ────────────────────────────────────────────────────
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://localhost:8000")

    # ── OS Scheduling ─────────────────────────────────────────────────
    WORKER_THREAD_COUNT: int = int(os.getenv("WORKER_THREAD_COUNT", 6))
    REQUEST_QUEUE_MAX_SIZE: int = int(os.getenv("REQUEST_QUEUE_MAX_SIZE", 100))

    # ── Logging ───────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/smartrail.log")

settings = Settings()
