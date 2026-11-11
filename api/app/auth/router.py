"""Endpoints for user registration and login."""

import asyncio

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import Token, UserCreate, UserLogin
from app.core.database import DbSession
from app.core.security import create_access_token, get_password_hash, verify_password
from app.swagger_docs import login_docs, registration_docs

router = APIRouter(tags=["Auth"])


async def get_user(db: AsyncSession, username: str) -> User | None:
    """Retrieves the user from the database based on the username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


@router.post("/registration", **registration_docs)
async def register(user: UserCreate, db: DbSession):
    result = await db.execute(
        select(User).where(or_(User.username == user.username, User.email == user.email))
    )
    existing_user = result.scalars().first()

    # Check if user with the same email and username is already exists
    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        if existing_user.email == user.email:
            raise HTTPException(status_code=400, detail="Email already exists")

    # bcrypt is slow on purpose (pure CPU work) - run it in a separate thread
    # so it does not block every other request while it hashes
    password_hash = await asyncio.to_thread(get_password_hash, user.password)

    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        username=user.username,
        password_hash=password_hash,
    )
    db.add(new_user)
    await db.commit()

    return {
        "message": "User successfully registered",
        "email": new_user.email,
        "user_name": new_user.username,
    }


@router.post("/login", response_model=Token, **login_docs)
async def login_for_access_token(form_data: UserLogin, db: DbSession):
    user = await get_user(db, form_data.username)
    password_ok = user is not None and await asyncio.to_thread(
        verify_password, form_data.password, user.password_hash
    )
    if not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}
