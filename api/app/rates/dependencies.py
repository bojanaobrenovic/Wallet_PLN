"""FastAPI dependencies that give endpoints the current exchange rates."""

from typing import Annotated

import redis
from fastapi import Depends, HTTPException, status

from app.core.config import REDIS_HOST, REDIS_PORT, SUPPORT_EMAIL
from app.rates.service import ExchangeRates, ExchangeRateService, RatesUnavailableError

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


def get_rate_service() -> ExchangeRateService:
    return ExchangeRateService(cache=redis_client)


def get_rates(
    service: Annotated[ExchangeRateService, Depends(get_rate_service)],
) -> ExchangeRates:
    try:
        return service.get_rates()
    except RatesUnavailableError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Exchange rates are currently unavailable (NBP API cannot be reached). "
                f"Please try again later or contact {SUPPORT_EMAIL}."
            ),
        ) from err
