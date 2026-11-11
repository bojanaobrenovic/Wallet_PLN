"""Wallet endpoints: show the wallet, add and subtract currency amounts."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from app.auth.dependencies import CurrentUser
from app.core.database import DbSession
from app.rates.dependencies import Rates
from app.swagger_docs import wallet_add, wallet_report, wallet_sub
from app.wallet.models import SUPPORTED_CURRENCIES, Wallet
from app.wallet.service import (
    find_wallet,
    get_balance_report,
    get_user_wallets,
    process_wallet_update,
)

router = APIRouter(tags=["Wallet"])

# A positive amount with at most two decimal places, taken from the URL
Amount = Annotated[Decimal, Path(decimal_places=2)]


def validate_currency_and_amount(currency: str, amount: Decimal) -> None:
    """Shared checks for add and subtract."""
    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Currency {currency} is not supported")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0.00")


# Return the balance for each currency along with the user's overall total balance
@router.get("/wallet", **wallet_report)
async def get_wallet_report(rates: Rates, current_user: CurrentUser, db: DbSession):
    user_wallets = await get_user_wallets(db, current_user.id)
    return get_balance_report(user_wallets, rates)


# Adding amount in different currencies to the wallet
@router.post("/wallet/add/{currency}/{amount}", **wallet_add)
async def add_to_wallet(
    currency: str, amount: Amount, rates: Rates, current_user: CurrentUser, db: DbSession
):
    validate_currency_and_amount(currency, amount)

    wallet = await find_wallet(db, current_user.id, currency)
    if wallet:
        wallet.amount += amount
    else:
        wallet = Wallet(user_id=current_user.id, currency=currency, amount=amount)
        db.add(wallet)
    await db.commit()

    return await process_wallet_update(
        db, current_user.id, currency, wallet, f"Successfully added {amount} {currency}.", rates
    )


# Subtracting amount in different currencies from the wallet
@router.post("/wallet/sub/{currency}/{amount}", **wallet_sub)
async def subtract_from_wallet(
    currency: str, amount: Amount, rates: Rates, current_user: CurrentUser, db: DbSession
):
    validate_currency_and_amount(currency, amount)

    wallet = await find_wallet(db, current_user.id, currency)
    if not wallet or wallet.amount < amount:
        raise HTTPException(status_code=400, detail=f"Insufficient funds in {currency}.")

    wallet.amount -= amount
    if wallet.amount == 0:
        await db.delete(wallet)
    await db.commit()

    return await process_wallet_update(
        db,
        current_user.id,
        currency,
        wallet,
        f"Successfully subtracted {amount} {currency}.",
        rates,
    )
