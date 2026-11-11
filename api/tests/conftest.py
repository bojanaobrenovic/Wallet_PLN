import os

# Mora PRE importa aplikacije: config.py čita ove promenljive čim se modul učita.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["SECRET_KEY"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.rates.dependencies import get_rates
from tests.utils import FAKE_RATES, register_and_login


@pytest.fixture
def anyio_backend():
    """Async tests (marked with @pytest.mark.anyio) run on asyncio."""
    return "asyncio"


@pytest.fixture
def client():
    """TestClient with its own empty in-memory database and fixed exchange rates."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_rates] = lambda: FAKE_RATES

    with TestClient(app) as test_client:
        # The tables must be created on the same event loop the requests run on
        test_client.portal.call(create_tables)
        yield test_client
        test_client.portal.call(engine.dispose)

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Registers and logs in a test user, returns the Authorization header."""
    token = register_and_login(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
