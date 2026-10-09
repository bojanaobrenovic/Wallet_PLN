"""Application entry point: creates the FastAPI app and plugs in the feature routers."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.auth.router import router as auth_router
from app.core.database import Base, engine
from app.rates.router import router as rates_router
from app.users.router import router as users_router
from app.wallet.router import router as wallet_router

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
app.include_router(users_router)
app.include_router(wallet_router)
app.include_router(rates_router)

# Creating tables in the database
Base.metadata.create_all(bind=engine)

#Check if the app is running
@app.get("/", summary="Check if the application is running")
def read_root():
    '''Checking if the application is runnig.'''
    return {"message": "Welcome to PLN Wallet API."}

