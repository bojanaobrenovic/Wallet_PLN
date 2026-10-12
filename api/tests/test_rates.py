from decimal import Decimal

import fakeredis
import pytest
import requests

from app.main import app
from app.rates.dependencies import get_rate_service, get_rates
from app.rates.service import (
    FRESH_KEY,
    LAST_GOOD_KEY,
    LOCK_KEY,
    ExchangeRates,
    ExchangeRateService,
    RatesUnavailableError,
)
from tests.utils import FAKE_RATES

NBP_RATES = ExchangeRates(rates={"EUR": Decimal("4.3010")}, effective_date="2026-10-12")
OLD_RATES = ExchangeRates(rates={"EUR": Decimal("4.2000")}, effective_date="2026-10-09")


class FakeNbp:
    """Stands in for the NBP API: counts calls and can pretend to be down."""

    def __init__(self, rates=NBP_RATES, is_down=False):
        self.rates = rates
        self.is_down = is_down
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.is_down:
            raise requests.ConnectionError("NBP is down")
        return self.rates


@pytest.fixture
def cache():
    return fakeredis.FakeRedis(decode_responses=True)


# --- ExchangeRateService ---------------------------------------------------


def test_first_call_downloads_from_nbp_and_caches(cache):
    nbp = FakeNbp()
    service = ExchangeRateService(cache, fetch=nbp)

    assert service.get_rates() == NBP_RATES
    assert nbp.calls == 1
    assert cache.ttl(FRESH_KEY) > 0  # fresh copy expires
    assert cache.ttl(LAST_GOOD_KEY) == -1  # fallback copy never expires


def test_second_call_uses_cache_without_calling_nbp(cache):
    nbp = FakeNbp()
    service = ExchangeRateService(cache, fetch=nbp)

    service.get_rates()
    service.get_rates()
    service.get_rates()

    assert nbp.calls == 1


def test_nbp_down_returns_last_good_rates(cache):
    cache.set(LAST_GOOD_KEY, OLD_RATES.to_json())
    service = ExchangeRateService(cache, fetch=FakeNbp(is_down=True))

    assert service.get_rates() == OLD_RATES


def test_nbp_down_and_empty_cache_raises(cache):
    service = ExchangeRateService(cache, fetch=FakeNbp(is_down=True))

    with pytest.raises(RatesUnavailableError):
        service.get_rates()


def test_while_another_request_refreshes_nbp_is_not_called_again(cache):
    cache.set(LAST_GOOD_KEY, OLD_RATES.to_json())
    cache.set(LOCK_KEY, "1")  # someone else is already downloading
    nbp = FakeNbp()
    service = ExchangeRateService(cache, fetch=nbp)

    assert service.get_rates() == OLD_RATES
    assert nbp.calls == 0


def test_rates_survive_redis_without_losing_precision():
    assert ExchangeRates.from_json(NBP_RATES.to_json()) == NBP_RATES


# --- Endpoints ---------------------------------------------------------------


def test_currencies_returns_codes(client):
    response = client.get("/currencies")

    assert response.status_code == 200
    assert response.json() == {
        "available_currencies": ["EUR", "USD", "JPY"],
        "effective_date": FAKE_RATES.effective_date,
    }


def test_nbp_down_and_empty_cache_returns_503(client, cache):
    del app.dependency_overrides[get_rates]  # use the real dependency in this test
    app.dependency_overrides[get_rate_service] = lambda: ExchangeRateService(
        cache, fetch=FakeNbp(is_down=True)
    )

    response = client.get("/currencies")

    assert response.status_code == 503
