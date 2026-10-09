"""Shared test data and helpers."""

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
