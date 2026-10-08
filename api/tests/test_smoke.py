USER = {
    "first_name": "Ana",
    "last_name": "Anić",
    "email": "ana@example.com",
    "username": "ana",
    "password": "tajna1234",
}


def test_root_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200

def test_wallet_requires_auth(client):
    response = client.get("/wallet")
    assert response.status_code == 401

def test_register_new_user(client):
    payload = {
        "first_name": "Ana",
        "last_name": "Anić",
        "email": "ana@example.com",
        "username": "ana",
        "password": "tajna1234",
    }
    response = client.post("/registration", json=payload)
    assert response.status_code == 200, response.text


def test_register_duplicate_username_fails(client):
    client.post("/registration", json=USER)
    response = client.post("/registration", json=USER)
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already exists"}

