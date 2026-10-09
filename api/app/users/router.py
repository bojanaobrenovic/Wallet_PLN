"""Endpoints about the logged-in user."""

from fastapi import APIRouter, Depends

from app import models
from app.auth.dependencies import get_current_user
from app.rates.service import get_exchange_rates
from app.swagger_docs import user_me_docs
from app.wallet.service import get_balance_report

router = APIRouter(tags=["User"])

#Return data about the user; also returns the total balance in the wallet (for the user)
@router.get("/me", **user_me_docs)
def read_users_me(current_user: models.User = Depends(get_current_user)):

    exchange_rates,effective_date = get_exchange_rates()
    report=get_balance_report(user_wallets=current_user.wallets,exchange_rates=exchange_rates, effective_date=effective_date)

    return {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "username": current_user.username,
        "balance in PLN": report["total_pln"]
    }
