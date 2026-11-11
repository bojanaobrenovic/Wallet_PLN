"""Endpoints about the logged-in user."""

from fastapi import APIRouter

from app.auth.dependencies import CurrentUser
from app.core.database import DbSession
from app.rates.dependencies import Rates
from app.swagger_docs import user_me_docs
from app.wallet.service import get_balance_report, get_user_wallets

router = APIRouter(tags=["User"])


# Return data about the user; also returns the total balance in the wallet (for the user)
@router.get("/me", **user_me_docs)
async def read_users_me(rates: Rates, current_user: CurrentUser, db: DbSession):
    # Wallets are loaded with an explicit query: async SQLAlchemy cannot
    # lazy-load current_user.wallets in the background like sync code did
    user_wallets = await get_user_wallets(db, current_user.id)
    report = get_balance_report(user_wallets, rates)

    return {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "username": current_user.username,
        "total_pln": report["total_pln"],
    }
