"""
SmartRail AI+ — API Routes: Authentication
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user

logger = logging.getLogger("smartrail.auth")
router = APIRouter(prefix="/auth")


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str
    phone: Optional[str] = None
    gender: Optional[str] = "OTHER"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """Register a new user account."""
    async with get_db() as db:
        # Check existing email/username
        await db.execute(
            "SELECT id FROM users WHERE email = %s OR username = %s",
            (req.email, req.username),
        )
        existing = await db.fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already registered",
            )

        # Validate password strength
        if len(req.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters",
            )

        pwd_hash = hash_password(req.password)

        await db.execute(
            """
            INSERT INTO users (email, username, password_hash, full_name, phone, gender, role)
            VALUES (%s, %s, %s, %s, %s, %s, 'PASSENGER')
            """,
            (req.email, req.username, pwd_hash, req.full_name, req.phone, req.gender),
        )
        user_id = db.lastrowid

    logger.info(f"New user registered: {req.email} (id={user_id})")
    return {
        "message": "Registration successful",
        "user_id": user_id,
        "email": req.email,
    }


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token."""
    async with get_db() as db:
        await db.execute(
            "SELECT id, email, username, password_hash, full_name, role, is_active FROM users WHERE email = %s OR username = %s",
            (form_data.username, form_data.username),
        )
        user = await db.fetchone()

    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact support.",
        )

    # Update last login
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET last_login = NOW() WHERE id = %s",
            (user["id"],),
        )

    token = create_access_token({"sub": user["id"], "email": user["email"], "role": user["role"]})
    logger.info(f"User logged in: {user['email']}")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    }


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    async with get_db() as db:
        await db.execute(
            "SELECT id, email, username, full_name, phone, gender, role, created_at, last_login FROM users WHERE id = %s",
            (current_user["id"],),
        )
        user = await db.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert datetime to string
    for key in ["created_at", "last_login"]:
        if user.get(key) and hasattr(user[key], "isoformat"):
            user[key] = user[key].isoformat()

    return user


@router.put("/profile")
async def update_profile(
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Update user profile."""
    updates = {}
    if full_name:
        updates["full_name"] = full_name
    if phone:
        updates["phone"] = phone

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    async with get_db() as db:
        await db.execute(
            f"UPDATE users SET {set_clause} WHERE id = %s",
            (*updates.values(), current_user["id"]),
        )

    return {"message": "Profile updated successfully"}
