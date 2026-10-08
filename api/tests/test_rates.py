FAKE_RATES = {"EUR": 4.25, "USD": 3.85, "JPY": 0.027}

def fake_get_excange_rates():
    return FAKE_RATES, "2026-10-08"

def test_currencies_returns_codes_from_nbp(client, monkeypatch):
    monkeypatch.setattr("app.rates.router.get_exchange_rates", fake_get_excange_rates)

    response = client.get("/currencies")

    assert response.status_code == 200
    assert response.json() == {
        "available_currencies": ["EUR", "USD", "JPY"],
        "effective_date": "2026-10-08"
    }
