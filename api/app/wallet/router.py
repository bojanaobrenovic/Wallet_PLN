"""Wallet endpoints: show the wallet, add and subtract currency amounts."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models import SUPPORTED_CURRENCIES
from app.rates.service import get_exchange_rates
from app.swagger_docs import wallet_add, wallet_report, wallet_sub
from app.wallet.service import get_balance_report, process_wallet_update

router = APIRouter(tags=["Wallet"])


#Return the balance for each currency along with the user's overall total balance
@router.get("/wallet",**wallet_report)
def get_wallet_report(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):

    user_wallets = db.query(models.Wallet).filter_by(user_id=current_user.id).all()

    if not user_wallets:
        message = {
            "message": f"The user has no money entered in any foreign currency..",
            "total_in_pln": 0.00
        }
        return message

    exchange_rates, effective_date = get_exchange_rates()
    return get_balance_report(user_wallets, exchange_rates, effective_date)

#Adding amount in different currencies to the wallet
@router.post("/wallet/add/{currency}/{amount}",**wallet_add)
async def add_to_wallet(currency: str, amount: float, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):

    #Checking if the currency is in the list of predefined currencies
    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Currency {currency} is not supported")

    #The currency amount must be greater than 0.0
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0.00")

    #user
    user_id = current_user.id

    #user's wallet
    wallet = db.query(models.Wallet).filter_by(user_id=user_id, currency=currency).first()

    if wallet:
        wallet.amount += amount
    else:
        wallet = models.Wallet(user_id=user_id, currency=currency, amount=amount)
        db.add(wallet)

    db.commit()

    #Using an already defined function for updated amount of currency
    return process_wallet_update(db, user_id, currency, wallet, f"Successfully added {amount} {currency}.")

#Substracting amount in different currencies from the wallet
@router.post("/wallet/sub/{currency}/{amount}",**wallet_sub)
async def subtract_from_wallet(currency: str, amount: float, db: Session = Depends(get_db),
                               current_user: models.User = Depends(get_current_user)):

    #Checking if the currency is in the list of predefined currencies
    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Currency {currency} is not supported")

    #The currency amount must be greater than 0.0
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0.00")

    user_id = current_user.id

    wallet = db.query(models.Wallet).filter_by(user_id=user_id, currency=currency).first()

    #Check if there are enough amounts to deduct from the wallet
    if not wallet or wallet.amount < amount:
        raise HTTPException(status_code=400, detail = f"Insufficient funds in {currency}.")

    #Substrating the amount of the specified currency
    wallet.amount -= amount
    if wallet.amount == 0:
        db.delete(wallet)
    db.commit()

    #Using an already defined function for updated amount of currency
    return process_wallet_update(db, user_id, currency, wallet, f"Successfully subtracted {amount} {currency}.")

