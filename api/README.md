# PLN Wallet API

![CI](https://github.com/bojanaobrenovic/Wallet_PLN/actions/workflows/ci.yml/badge.svg?branch=refactor)

A REST API that tracks the value of a multi-currency wallet in Polish złoty (PLN),
using live exchange rates from the [National Bank of Poland (NBP) API](https://api.nbp.pl/en.html).

Users register, log in, add or subtract amounts in foreign currencies, and get the
PLN value of each currency and of the whole wallet, always calculated with the latest
"ask" rates.

**Tech stack:** Python 3.12 · FastAPI · PostgreSQL · SQLAlchemy · Redis · JWT · Docker · pytest · GitHub Actions

---

## Example

A wallet with **100 EUR**, **20 USD** and **8000 JPY**, with rates
1 EUR = 4.25 PLN, 1 USD = 3.85 PLN, 1 JPY = 0.027 PLN:

```http
GET /wallet
```
```json
{
  "wallet_report": [
    {"currency": "EUR", "amount": 100.0,  "value_pln": 425.0},
    {"currency": "USD", "amount": 20.0,   "value_pln": 77.0},
    {"currency": "JPY", "amount": 8000.0, "value_pln": 216.0}
  ],
  "total_pln": 718.0,
  "effective_date": "2026-11-06"
}
```

## Quick start

Requirements: **Docker** with Docker Compose.

```bash
git clone https://github.com/bojanaobrenovic/Wallet_PLN.git
cd Wallet_PLN/api
cp .env.example .env          # then set your own SECRET_KEY (see the comment in the file)
docker compose up --build
```

The API runs at **http://localhost:8000**, interactive docs at **http://localhost:8000/docs**.

## API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/registration` | | Create a user |
| `POST` | `/login` | | Get a JWT access token |
| `GET` | `/me` | ✔ | User profile and total wallet value in PLN |
| `GET` | `/wallet` | ✔ | Wallet composition, PLN value per currency, total in PLN |
| `POST` | `/wallet/add/{currency}/{amount}` | ✔ | Add an amount of a currency |
| `POST` | `/wallet/sub/{currency}/{amount}` | ✔ | Subtract an amount of a currency |
| `GET` | `/currencies` | | Supported currency codes |
| `GET` | `/exchange_rates` | | Current NBP "ask" rates |

Authenticated endpoints expect the header `Authorization: Bearer <token>`.
Amounts accept at most two decimal places.

## Design decisions

**Money is never a float.** Amounts are stored as `NUMERIC(18, 2)` in PostgreSQL and
handled as `Decimal` in Python, with explicit `ROUND_HALF_UP` rounding to whole grosze.
With floats, `0.30 - 0.10 - 0.20` is not zero, and a user could be told they have
insufficient funds when they don't.

**Exchange rates are cached, with a fallback.** NBP publishes table C once per working day.
The API keeps two copies in Redis:

- a *fresh* copy that expires after one hour, so NBP is called at most once an hour;
- a *last known good* copy that never expires, used when NBP is unreachable.

A Redis lock (`SET NX`) makes sure that when the cache expires, only one request
calls NBP even if many arrive at once. NBP calls have a 5-second timeout. If NBP is
down and nothing was ever cached, the API answers `503 Service Unavailable`.

**Code is organised by feature, not by layer.** Each feature folder has its own
router (HTTP), service (logic) and models (tables):

```
api/app/
├── main.py        # creates the app and plugs in the routers
├── core/          # config, database session, password hashing and JWT
├── auth/          # registration, login, current-user dependency
├── users/         # /me
├── wallet/        # wallet endpoints and PLN calculations
└── rates/         # NBP client and Redis cache
```

## Development

Run the tests and the linter locally (Python 3.12):

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

pytest            # tests use an in-memory SQLite database and fake exchange rates
ruff check .      # lint (PEP 8, import order, common bugs)
ruff format .     # format
```

Tests never call the real NBP API or Redis: exchange rates are replaced with fixed
values through FastAPI's `dependency_overrides`, and the cache logic is tested
against `fakeredis`. GitHub Actions runs `ruff` and `pytest` on every push.

## Roadmap

- Async database, HTTP and Redis clients (`asyncpg`, `httpx`, `redis.asyncio`)
- Database migrations with Alembic instead of `create_all`
- Pydantic response models, so the OpenAPI docs are generated from the code