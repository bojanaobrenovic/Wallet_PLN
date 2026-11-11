"""Application entry point: creates the FastAPI app and plugs in the feature routers."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.auth.router import router as auth_router
from app.core.database import Base, engine
from app.rates.router import router as rates_router
from app.users.router import router as users_router
from app.wallet.router import router as wallet_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts (not on import!)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Runs once when the server stops
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


# Settings for swagger documentation
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
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
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


# Check if the app is running
@app.get("/", summary="Check if the application is running")
async def read_root():
    """Checking if the application is runnig."""
    return {"message": "Welcome to PLN Wallet API."}
