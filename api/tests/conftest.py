import os

# Mora PRE importa aplikacije: database.py i security.py
# čitaju ove promenljive čim se modul učita.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from tests.utils import register_and_login


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
    """TestClient kome je get_db zamenjen test bazom."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


FAKE_RATES = {"EUR": 4.25, "USD": 3.85, "JPY": 0.027}
FAKE_DATE = "2026-10-08"


@pytest.fixture
def fake_rates(monkeypatch):
    """Replaces the NBP + Redis call with fixed rates everywhere it is used."""

    def fake_get_exchange_rates():
        return FAKE_RATES, FAKE_DATE

    for module in ("app.wallet.router", "app.wallet.service", "app.users.router"):
        monkeypatch.setattr(f"{module}.get_exchange_rates", fake_get_exchange_rates)


@pytest.fixture
def auth_headers(client):
    """Registers and logs in a test user, returns the Authorization header."""
    token = register_and_login(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
