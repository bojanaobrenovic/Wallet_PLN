"""Endpoints for exchange rates and supported currencies."""

from fastapi import APIRouter

from app.rates.service import get_exchange_rates
from app.swagger_docs import currencies_docs, exchange_rates_docs

router = APIRouter(tags=["Exchange rates"])


# Returns available exchange rates from NBP
@router.get("/exchange_rates", **exchange_rates_docs)
def get_supported_exrate():
    exchange_rates, effective_date = get_exchange_rates()
    return {
        "message": "Available exchange rate list",
        "exchange_rates": exchange_rates,
        "effective_date": effective_date,
    }


# Returns available currencies from API of NBL Bank
@router.get("/currencies", **currencies_docs)
def get_currencies():
    exchange_rates, effective_date = get_exchange_rates()
    currency_list = list(exchange_rates.keys())
    return {"available_currencies": currency_list, "effective_date": effective_date}
