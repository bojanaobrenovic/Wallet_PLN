# FastAPI Application with Docker - PLN Wallet

This project provides a FastAPI application that allows users to manage a wallet with multiple currencies, track exchange rates, and perform conversions between currencies, with Redis integration for data caching and PostgreSQL for persistent storage.

### Core Features

- **Wallet with multiple currencies**: Each user has one wallet that can hold funds in various currencies.
- **Currency conversion**ng real-time exchange rates from the National Bank of Poland (NBP) API.
- **Caching with Redis**: Exchange rates are cached for 24 hours in Redis to reduce requests to the NBP API and improve performance.
- **Persistent storage**: Wallet data is stored in a PostgreSQL database for reliability. Only the current wallet balance is stored, without history.

### How It Works

This application allows users to track the current value of their wallet in different currencies, expressed in Polish złoty (PLN). The exchange rates are fetched from the **National Bank of Poland (NBP) API**.

The application uses the NBP API, with the following endpoint:
[https://api.nbp.pl/api/exchangerates/tables/c](https://api.nbp.pl/api/exchangerates/tables/c)

#### Details::
- Provides the latest  available exchange rates for various currencies against the Polish złoty (PLN)
- Returns the "ask" rate for conversions.
- Updates every working day, with no updates on weekends.

### API Endpoints
### 1. **User Endpoints**

- **POST /registration**: Registers a new user.
- **POST /login**: Authenticates a user and returns an access token.
- **GET /me**: Retrieves the authenticated user's details and wallet balance in PLN.

### 2. **Currency Endpoints**

- **GET /exchange_rates**: Fetches the current exchange rate for a specified currency.
- **GET /currencies**: Returns a list of all supported currencies.

### 3. **Wallet Endpoints**

- **GET /wallet**: Returns the current state of the wallet in foreign currencies and the total value in PLN, along with the exchange rate date.
- **POST /wallet/add/{currency}/{amount}**: Adds a specified amount of a currency to the wallet.
- **POST /wallet/sub/{currency}/{amount}**: Subtracts a specified amount of a currency from the wallet.

### **Swagger Documentation**

You can explore and test all API endpoints interactively using Swagger at:

- [http://localhost:8000/docs](http://localhost:8000/docs)

# Prerequisites
- Docker
- Docker Compose
- PostgreSQL >= 12.0
- Python 3.10 (optional, if you want to run outside Docker)

## Setup

### Step 1:
First, clone this repository to your local machine.
#### git clone git@github.com:bojanaobrenovic/PLNConvert.git
#### navgate to the folder api: PLNConvert/api

### Step 2:
Create a .env file in the project root/api (PLNConvert/api) to store the environment variables.

#### Add theese variables:
- SECRET_KEY = "your_secret_key" #secret_key = secrets.token_hex(32)
- ALGORITHM = "HS256"
- ACCESS_TOKEN_EXPIRE_MINUTES = 30

- DATABASE_URL=postgresql://user:password@db/database_name
- POSTGRES_USER=user
- POSTGRES_PASSWORD=password
- POSTGRES_DB=database_name

### Step 3:

Build the Docker containers:
- docker-compose up --build
