"""Exchange rates from the NBP API, cached in Redis."""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

import redis
import requests

from app.core.config import CACHE_TTL_SECONDS, NBP_API_URL

logger = logging.getLogger(__name__)

FRESH_KEY = "nbp:rates:fresh"  # expires after CACHE_TTL_SECONDS
LAST_GOOD_KEY = "nbp:rates:last_good"  # never expires, used when NBP is down
LOCK_KEY = "nbp:rates:lock"  # only one request at a time refreshes from NBP
LOCK_SECONDS = 10
NBP_TIMEOUT_SECONDS = 5


class RatesUnavailableError(Exception):
    """NBP is not reachable and there are no cached rates to fall back to."""


@dataclass(frozen=True)
class ExchangeRates:
    """'Ask' prices in PLN for one unit of each currency, and the date they are valid for."""

    rates: dict[str, Decimal]
    effective_date: str

    def to_json(self) -> str:
        # Decimals are stored as strings, so no precision is lost in Redis
        return json.dumps(
            {
                "effective_date": self.effective_date,
                "rates": {code: str(rate) for code, rate in self.rates.items()},
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> "ExchangeRates":
        data = json.loads(raw)
        return cls(
            rates={code: Decimal(rate) for code, rate in data["rates"].items()},
            effective_date=data["effective_date"],
        )


def fetch_from_nbp() -> ExchangeRates:
    """Downloads table C (buy/sell prices) from the NBP API."""
    response = requests.get(NBP_API_URL, timeout=NBP_TIMEOUT_SECONDS)
    response.raise_for_status()
    table = response.json()[0]
    return ExchangeRates(
        rates={rate["code"]: Decimal(str(rate["ask"])) for rate in table["rates"]},
        effective_date=table["effectiveDate"],
    )


class ExchangeRateService:
    """Returns exchange rates, calling NBP at most once per cache period.

    1. Fresh rates in the cache -> return them, NBP is not called.
    2. No fresh rates -> download from NBP and cache them.
    3. NBP is down -> return the last rates that were successfully downloaded.
    4. NBP is down and nothing was ever cached -> RatesUnavailableError.
    """

    def __init__(
        self,
        cache: redis.Redis,
        fetch: Callable[[], ExchangeRates] = fetch_from_nbp,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ):
        self.cache = cache
        self.fetch = fetch
        self.ttl_seconds = ttl_seconds

    def get_rates(self) -> ExchangeRates:
        fresh = self.cache.get(FRESH_KEY)
        if fresh:
            return ExchangeRates.from_json(fresh)

        # SET NX = "set only if it does not exist": exactly one request gets the lock
        got_lock = self.cache.set(LOCK_KEY, "1", nx=True, ex=LOCK_SECONDS)
        if not got_lock:
            # Another request is already refreshing - don't hit NBP a second time
            last_good = self.cache.get(LAST_GOOD_KEY)
            if last_good:
                return ExchangeRates.from_json(last_good)

        try:
            rates = self.fetch()
        except (requests.RequestException, KeyError, IndexError, ValueError) as err:
            logger.warning("NBP API is unavailable: %s", err)
            return self._last_good_or_raise(err)
        else:
            payload = rates.to_json()
            self.cache.set(FRESH_KEY, payload, ex=self.ttl_seconds)
            self.cache.set(LAST_GOOD_KEY, payload)
            return rates
        finally:
            if got_lock:
                self.cache.delete(LOCK_KEY)

    def _last_good_or_raise(self, err: Exception) -> ExchangeRates:
        last_good = self.cache.get(LAST_GOOD_KEY)
        if last_good:
            return ExchangeRates.from_json(last_good)
        raise RatesUnavailableError("NBP API is unavailable and no rates are cached") from err
