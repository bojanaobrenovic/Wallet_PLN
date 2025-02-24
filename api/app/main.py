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
from . import security
from . import database

from .database import engine, Base, get_db
from .security import verify_token

from .swagger_docs import *

import redis

#Email support in case of errors
SUPPORT_EMAIL = "bojana.n.obrenovic@gmail.com"

#FastAPI application initialization
app = FastAPI()

#OAuth2 authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#Settings for swagger documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="PLNConvert – Conversion of foreign currencies to PLN",
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

#Creating tables in the database
Base.metadata.create_all(bind=engine)

#Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#Initializing the Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
#redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

#Supported currencies and exchange rate URLs
from .models import SUPPORTED_CURRENCIES
NBP_API_URL = "https://api.nbp.pl/api/exchangerates/tables/c"

class UserCreate(BaseModel):
    '''Model for data entry during user registration'''
    first_name: str
    last_name: str
    email: EmailStr
    username: str
    password: str

def get_password_hash(password: str) -> str:
    '''Hashes the password using bcrypt.'''
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    '''Retrieves the user from the database based on the username.'''
    return db.query(models.User).filter(models.User.username == username).first()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    '''Validates the JWT token and returns the currently loggedin user.
    If the token is not valid or the user does not exist, it raises an HTTPException.'''

    user_data = verify_token(token)

    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(models.User).filter(models.User.username == user_data.username).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def get_exchange_rates():

    '''Fetches exchange rates from the NBP API and caches them in Redis for 24 hours.
    After 24 hours, the data is refreshed by fetching new rates from the API to ensure accuracy while maintaining availability if the API is down.
    If the API is unavailable, the system uses the last saved exchange rates from the cache.
    '''

    today = date.today()
    redis_key = f"exchange_rates:{today.isoformat()}"

    #Checking the Redis cache
    cached_data = redis_client.get(redis_key)
    if cached_data:
        data = json.loads(cached_data)
        return data["rates"], data["effectiveDate"]

    #Attempting to retrieve data from API
    try:
        response = requests.get(NBP_API_URL)
        response.raise_for_status()

    except requests.RequestException:
        #If the API is unavailable, try to use the cached data
        last_available_key = redis_client.keys("exchange_rates:*")
        if last_available_key:
            last_available_key = sorted(last_available_key)[-1]
            cached_data=redis_client.get(last_available_key)
            if cached_data:
                data=json.loads(cached_data)
                return data["rates"],data["effectiveDate"]
        else:
            raise HTTPException(
                #If the NBP API is unavailable and there is no data in the redis cached
                status_code=500,
                    detail=f"Currently, it is not possible to access the Polish National Bank's public API - NBP. "
                           f"Please contact support via email: {SUPPORT_EMAIL}"
            )

    #Retrieving relevant data from the API response
    data_api = response.json()[0]
    effectivedate = data_api["effectiveDate"]
    rates_data = data_api["rates"]
    rate_list = {rate['code']: rate['ask'] for rate in rates_data} #ask values need to use

    #Caching data in Redis
    cache_payload = {"rates": rate_list, "effectiveDate": effectivedate}
    redis_client.setex(redis_key, 86400, json.dumps(cache_payload))

    #Deleting old cache (all keys that are not for today's date)
    all_keys = redis_client.keys("exchange_rates:*")
    for key in all_keys:
        if key != redis_key:
            redis_client.delete(key)

    return rate_list, effectivedate

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


#Endpoint for registration
@app.post("/registration", **registration_docs)
def register(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(or_(models.User.username == user.username, models.User.email == user.email)).first()

    #Check if user with the same email and username is already exists
    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        if existing_user.email == user.email:
            raise HTTPException(status_code=400, detail="Email already exists")

    #Create a new user
    new_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        username=user.username,
        password_hash=get_password_hash(user.password)  #Save a hashed password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User successfully registered", "email": new_user.email, "user_name": new_user.username}


#Endpoint for login - returns only access token
@app.post("/login", response_model=security.Token,**login_docs)
def login_for_access_token(
        form_data: security.UserLogin, db: Session = Depends(database.get_db)):

    user = get_user(db, form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    #Create access token
    access_token = security.create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

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

#Returns available exchange rates from NBP
@app.get("/exchange_rates", **exchange_rates_docs)
def get_supported_exrate():
    exchange_rates, effective_date = get_exchange_rates()
    return {
        "message": "Available exchange rate list",
        "exchange_rates": exchange_rates,
        "effective_date": effective_date
    }

#Returns available currencies from API of NBL Bank
@app.get("/currencies", **currencies_docs)
def get_currencies():
    exchange_rates, effective_date = get_exchange_rates()
    currency_list = list(exchange_rates.keys())
    return {"available_currencies": currency_list,
            "effective_date": effective_date}

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
async def subtract_from_wallet(currency: str, amount: float, db: Session = Depends(database.get_db),
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

