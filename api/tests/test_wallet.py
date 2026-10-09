import pytest


def test_empty_wallet(client, auth_headers):
    response = client.get("/wallet", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["total_in_pln"] == 0


def test_example_from_task(client, auth_headers, fake_rates):
    """100 EUR + 20 USD + 8000 JPY = 425 + 77 + 216 = 718 PLN."""
    client.post("/wallet/add/EUR/100", headers=auth_headers)
    client.post("/wallet/add/USD/20", headers=auth_headers)
    client.post("/wallet/add/JPY/8000", headers=auth_headers)

    response = client.get("/wallet", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_pln"] == 718.0
    assert body["wallet_report"] == [
        {"currency": "EUR", "value_pln": 425.0},
        {"currency": "USD", "value_pln": 77.0},
        {"currency": "JPY", "value_pln": 216.0},
    ]


def test_add_to_existing_currency_sums_amounts(client, auth_headers, fake_rates):
    client.post("/wallet/add/EUR/100", headers=auth_headers)

    response = client.post("/wallet/add/EUR/50", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["wallet_report"][0]["amount"] == 150


def test_subtract(client, auth_headers, fake_rates):
    client.post("/wallet/add/EUR/100", headers=auth_headers)

    response = client.post("/wallet/sub/EUR/40", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["wallet_report"][0]["amount"] == 60


def test_subtract_more_than_available_fails(client, auth_headers, fake_rates):
    client.post("/wallet/add/USD/20", headers=auth_headers)

    response = client.post("/wallet/sub/USD/50", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds in USD."


@pytest.mark.parametrize("url", ["/wallet/add/XYZ/10", "/wallet/sub/XYZ/10"])
def test_unsupported_currency_fails(client, auth_headers, url):
    response = client.post(url, headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Currency XYZ is not supported"


@pytest.mark.parametrize("amount", ["0", "-5"])
def test_non_positive_amount_fails(client, auth_headers, amount):
    response = client.post(f"/wallet/add/EUR/{amount}", headers=auth_headers)

    assert response.status_code == 400


def test_me_shows_total_balance(client, auth_headers, fake_rates):
    client.post("/wallet/add/EUR/100", headers=auth_headers)

    response = client.get("/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["balance in PLN"] == 425.0