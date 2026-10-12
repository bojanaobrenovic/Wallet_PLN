"""Endpoints for exchange rates and supported currencies."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.rates.dependencies import get_rates
from app.rates.service import ExchangeRates
from app.swagger_docs import currencies_docs, exchange_rates_docs

router = APIRouter(tags=["Exchange rates"])


@router.get("/exchange_rates", **exchange_rates_docs)
def get_supported_exrate(rates: Annotated[ExchangeRates, Depends(get_rates)]):
    return {
        "message": "Available exchange rate list",
        "exchange_rates": rates.rates,
        "effective_date": rates.effective_date,
    }


@router.get("/currencies", **currencies_docs)
def get_currencies(rates: Annotated[ExchangeRates, Depends(get_rates)]):
    return {
        "available_currencies": list(rates.rates),
        "effective_date": rates.effective_date,
    }
