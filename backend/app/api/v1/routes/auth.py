"""
Authentication routes — JWT login, refresh, registration.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.dependencies import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

router = APIRouter()
logger = logging.getLogger(__name__)


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None
    role: UserRole = UserRole.VIEWER

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Register new user")
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = UserRepository(db)
    if await repo.get_by_email(payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if await repo.get_by_username(payload.username):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role.value,
    )
    user = await repo.create(user)
    logger.info("New user registered: %s", user.username)
    return {"id": user.id, "email": user.email, "username": user.username, "role": user.role}


@router.post("/token", response_model=TokenResponse, summary="Login and get tokens")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    repo = UserRepository(db)
    user = await repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")

    user.last_login = datetime.now(timezone.utc)
    await repo.update(user)

    return TokenResponse(
        access_token=create_access_token(subject=user.id, extra_claims={"role": user.role}),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    data = decode_refresh_token(payload.refresh_token)
    if not data:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    repo = UserRepository(db)
    user = await repo.get_by_id(data["sub"])
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(subject=user.id, extra_claims={"role": user.role}),
        refresh_token=create_refresh_token(subject=user.id),
    )
