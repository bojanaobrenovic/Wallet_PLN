from tests.utils import USER, register_and_login


def test_login_returns_token(client):
    response = register_and_login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_fails(client):
    client.post("/registration", json=USER)

    response = client.post("/login", json={"username": USER["username"], "password": "pogresna"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_register_duplicate_email_fails(client):
    client.post("/registration", json=USER)
    other = {**USER, "username": "druga_ana"}

    response = client.post("/registration", json=other)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"


def test_valid_token_gives_access_to_wallet(client):
    token = register_and_login(client).json()["access_token"]

    response = client.get("/wallet", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_invalid_token_is_rejected(client):
    response = client.get("/wallet", headers={"Authorization": "Bearer nije-pravi-token"})

    assert response.status_code == 401
