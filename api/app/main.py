import json
from http.client import responses

import requests
from datetime import date

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from sqlalchemy.orm import Session
from sqlalchemy import or_

from . import models
from .core import security
from .core.database import engine, Base, get_db
from .core.security import verify_token


from .swagger_docs import *

from .rates.router import router as rates_router
from .rates.service import get_exchange_rates

from .auth.dependencies import get_current_user
from .auth.router import router as auth_router

#Email support in case of errors
SUPPORT_EMAIL = "bojana.n.obrenovic@gmail.com"

#FastAPI application initialization
app = FastAPI()


#Settings for swagger documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Wallet PLN – Conversion of foreign currencies to PLN",
        version="1.0.0",
        description="API for tracking and managing multi-currency balances in PLN",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
app.include_router(auth_router)
app.include_router(rates_router)

#Creating tables in the database
Base.metadata.create_all(bind=engine)


#Supported currencies and exchange rate URLs
from .models import SUPPORTED_CURRENCIES

def get_balance_report(user_wallets, exchange_rates, effective_date):

    '''Creating a report that shows the user's balance. The report contains the balance for each currency expressed in PLN,
    as well as the user's total balance in foreign currencies (also in PLN).
    In addition, the report includes the effective date, which allows the user to see the date when the exchange rates are valid.'''

    report_list = []
    total_pln = 0.0

    for wallet in user_wallets:
        currency = wallet.currency
        amount = wallet.amount

        pln_value = amount * exchange_rates[currency]
        total_pln += pln_value

        report_list.append({
            "currency": currency,
            #"amount": amount, #useful info in report
            "value_pln": round(pln_value,2) #Two decimal places are correct for currency conversions
        })

    return {
        "wallet_report": report_list,
        "total_pln": round(total_pln,2),
        "effective_date": effective_date
    }


def process_wallet_update(db: Session, user_id: int, currency: str, wallet: models.Wallet, operation_message: str) -> dict:

    ''' Helper function for generating a report after adding or subtracting a foreign currency amount.
    The report shows:
    - the new balance in that currency expressed in PLN;
    - and the user's overall total balance in PLN across all currencies.'''

    exchange_rates, effective_date = get_exchange_rates()

    #Calculating the balance for the updated currency
    updated_in_pln = wallet.amount * exchange_rates[currency] if currency in exchange_rates else "N/A"
    wallet_report = [{
        "currency": currency,
        "amount": wallet.amount,
        "value_pln": round(updated_in_pln,2)
    }]

    #Calculating the total balance in PLN
    all_wallets = db.query(models.Wallet).filter_by(user_id=user_id).all()
    total_in_pln = sum(
        w.amount * exchange_rates[w.currency]
        for w in all_wallets if w.currency in exchange_rates
    )

    #Report after updating currency
    return {
        "message": operation_message,
        "wallet_report": wallet_report,
        "total_in_pln": round(total_in_pln,2),
        "effective_date":effective_date
    }

#Check if the app is running
@app.get("/", summary="Check if the application is running")
def read_root():
    '''Checking if the application is runnig.'''
    return {"message": "Welcome to PLN Wallet API."}

#Return data about the user; also returns the total balance in the wallet (for the user)
@app.get("/me",tags=["User"], **user_me_docs)
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

#Return the balance for each currency along with the user's overall total balance
@app.get("/wallet", tags=["Wallet"], **wallet_report)
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
@app.post("/wallet/add/{currency}/{amount}", tags=["Wallet"],**wallet_add)
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
@app.post("/wallet/sub/{currency}/{amount}", tags=["Wallet"],**wallet_sub)
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

