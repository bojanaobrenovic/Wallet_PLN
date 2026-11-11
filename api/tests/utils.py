"""Shared test data and helpers."""

from decimal import Decimal

from app.rates.service import ExchangeRates

# The rates from the example in the task description
FAKE_RATES = ExchangeRates(
    rates={"EUR": Decimal("4.25"), "USD": Decimal("3.85"), "JPY": Decimal("0.027")},
    effective_date="2026-10-08",
)

USER = {
    "first_name": "Ana",
    "last_name": "Anić",
    "email": "ana@example.com",
    "username": "ana",
    "password": "tajna1234",
}


def register_and_login(client):
    """Registers USER and logs in. Returns the login response."""
    client.post("/registration", json=USER)
    return client.post("/login", json={"username": USER["username"], "password": USER["password"]})
