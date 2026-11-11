"""Async database engine and the DbSession dependency."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import DATABASE_URL

engine = create_async_engine(DATABASE_URL)

# expire_on_commit=False: objects stay readable after commit without another DB round trip
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one DB session per request, always closed at the end."""
    async with SessionLocal() as session:
        yield session


# Short name for endpoint parameters: `db: DbSession`
DbSession = Annotated[AsyncSession, Depends(get_db)]
