"""Endpoints about the logged-in user."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.rates.dependencies import get_rates
from app.rates.service import ExchangeRates
from app.swagger_docs import user_me_docs
from app.wallet.service import get_balance_report

router = APIRouter(tags=["User"])


# Return data about the user; also returns the total balance in the wallet (for the user)
@router.get("/me", **user_me_docs)
def read_users_me(
    rates: Annotated[ExchangeRates, Depends(get_rates)],
    current_user: User = Depends(get_current_user),
):

    report = get_balance_report(current_user.wallets, rates)

    return {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "username": current_user.username,
        "balance in PLN": report["total_pln"],
    }
