import os

from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    """Silences a required env variable, returns a clear error if it fails!"""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not set. Check your .env file or environmnet variables.")
    return value


# --- Database ---
# The app talks to Postgres through the async driver asyncpg,
# so "postgresql://..." from .env becomes "postgresql+asyncpg://..."
DATABASE_URL = _require_env("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)

# --- Authentication ---
SECRET_KEY = _require_env("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# --- Redis ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 3600))

# --- NBP API ---
NBP_API_URL = "https://api.nbp.pl/api/exchangerates/tables/c"

# --- Support ---
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@example.com")
