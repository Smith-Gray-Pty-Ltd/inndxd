"""Authentication router — registration and login."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from inndxd_core.auth import create_access_token, hash_password, verify_password
from inndxd_core.domain.user import UserCreate, UserLogin
from inndxd_core.repositories.users import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = UserRepository(db)
    existing = await repo.get_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    hashed = hash_password(body.password)
    user = await repo.create(body.email, hashed, body.tenant_id)
    await db.commit()
    logger.info("User registered: %s", user.email)
    return {"id": str(user.id), "email": user.email}


@router.post("/login")
async def login(
    body: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    token = create_access_token(user.id, str(user.tenant_id) if user.tenant_id else None)
    logger.info("User logged in: %s", user.email)
    return {"access_token": token, "token_type": "bearer"}
