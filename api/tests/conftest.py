import os

# Mora PRE importa aplikacije: config.py čita ove promenljive čim se modul učita.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.rates.dependencies import get_rates
from tests.utils import FAKE_RATES, register_and_login


@pytest.fixture
def db_session():
    """Svaki test dobija svoju, potpuno praznu bazu u memoriji."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    """TestClient with a test database and fixed exchange rates (no NBP, no Redis)."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_rates] = lambda: FAKE_RATES
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Registers and logs in a test user, returns the Authorization header."""
    token = register_and_login(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
