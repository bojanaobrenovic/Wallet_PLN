user_me_docs = {
    "summary": "Return user profile and total wallet balance in PLN",
    "description": """
    This endpoint returns details about the authenticated user, including:
    **First name**, **Last name**, **Email** and **Username**.
    Additionally, it calculates and provides the user's **total wallet balance** converted to **Polish Zloty (PLN)** based on the latest exchange rates.
    
    ### Example Response:
    {
        "first_name": "John",
        "last_name": "Jonannatan",
        "email": "john.jonannatan@example.com",
        "username": "johnjonannatan",
        "balance_in_PLN": 527.77
    }
    """,
    "responses": {
        401: {"description": "Unauthorized - Could not validate credentials"},
        500: {"description": "NBP API is not available, and Redis cache does not contain exchange rates."}
    }
}

login_docs = {
    "summary": "User Login - Generate Access Token",
    "description": """
    This endpoint allows users to log in by providing their username and password.
    If the credentials are valid, the API returns a **JWT access token** that can be used for authenticated requests.""",

    "responses": {
        401: {"description": "Unauthorized - Invalid credentials"}}}

# swagger_docs.py

registration_docs = {
    "summary": "User Registration",
    "description": """
    This endpoint allows a user to create an account by providing their personal details,
    username, and a secure password.
    If the username or email already exists, the registration will fail with an appropriate error message.

    ### Example Response:
    {
        "message": "User successfully registered",
        "email": "john.doe@example.com",
        "username": "johndoe"
    },
    """,
    "responses": {
        400: {"description": "Bad Request - Username or Email already exists"}
    }
}

exchange_rates_docs = {
    "summary": "Returns available exchange rates from NBP",
    "description": """
    This endpoint returns the most recent exchange rates for supported currencies, 
    along with the effective date of the rates. The data is retrieved from the Polish 
    National Bank (NBP) and cached for 24 hours to optimize performance and availability.
    
    ### Example Response:
    {
        "message": "Available exchange rate list"
        "exchange_rates": {
            "USD": 3.95,
            "EUR": 4.50,
            "GBP": 5.30
        },
        "effective_date": "2025-02-24"
    }
    """,
    "responses": {
        500: {"description": "NBP API is not available, and Redis cache does not contain exchange rates."}
    }
}

currencies_docs = {
    "summary":"Returns available currencies from API of NBL Bank",
    "description":"""
    This endpoint provides a list of all supported currency codes for which exchange rates
    are available. The data is retrieved from the Polish National Bank (NBP) and includes
    the effective date of the rates.
    
    ### Example Response:
    {
        "available_currencies": ["USD", "EUR", "GBP", "CHF", "JPY"],
        "effective_date": "2025-02-24"
    }
    """,
    "responses":{
         500: {"description": "NBP API is not available, and Redis cache does not contain exchange rates."}}
}



wallet_report = {
    "summary":"Returns the current wallet composition, the PLN value for each currency, and the total PLN value",
    "description":
    """
    This endpoint returns a report containing only the currencies the user holds, their equivalent value in PLN,
    and the total balance of all currencies converted to PLN. The exchange rates are fetched from the Polish National Bank (NBP).
    
    ### Example Response:
    {
    "wallet_report": [
        {
            "currency": "XDR",
            "value_pln": 9078.92
        },
        {
            "currency": "EUR",
            "value_pln": 2101.7
        },
        {
            "currency": "CZK",
            "value_pln": 83.9
        },
        {
            "currency": "JPY",
            "value_pln": 13.39
        }
    ],
    "total_pln": 11277.91,
    "effective_date": "2025-02-24"}
    """,
    "responses":{
        401: {"description": "Unauthorized - Invalid credentials"},
        500: {"description": "NBP API is not available, and Redis cache does not contain exchange rates."}}
}


wallet_add = {
    "summary":"Adds a specified amount of a currency to the wallet",
    "description":
    """
    This endpoint allows users to add a given amount of a specific currency to their wallet.
    If the currency already exists in the wallet, the amount is increased. If it does not exist,
    a new entry is created.
    
    ### Parameters:
    - **currency** *(str)*: The currency code (e.g., "USD", "EUR").
    - **amount** *(float)*: The amount to add (must be greater than 0).
    
    ### Example Response:
    {
    "message": "Successfully added 500.0 JPY.",
    "wallet_report": [
        {
            "currency": "JPY",
            "amount": 500.0,
            "IN PLN": 13.39
        }
    ],
    "total_in_pln": 11277.91,
    "effectiveDate": "2025-02-20"}
    """,
    "responses":{
        400: {"description": "Bad Request - Invalid currency or amount"},
        401: {"description": "Could not validate credentials"},
        500: {"description": "NBP API is not available, and Redis cache does not contain exchange rates."}}}


wallet_sub = {
    "summary":"Subtracts a specified amount of a currency from the wallet",
    "description":
    """
    This endpoint allows users to subtract a given amount of a specific currency from their wallet.
    It checks if the user has sufficient funds before proceeding. If the deduction results in a zero balance
    for that currency, the currency entry is removed from the wallet.
    
    ### Parameters:
    - **currency** *(str)*: The currency code (e.g., "USD", "EUR").
    - **amount** *(float)*: The amount to add (must be greater than 0).
    
    ### Example Response:
    {
    "message": "Successfully subtracted 100.0 EUR.",
    "wallet_report": [
        {
            "currency": "EUR",
            "amount": 23,
            "IN PLN": 96.68
        }
    ],
    "total_in_pln": 11277.91,
    "effectiveDate": "2025-02-20"}
    """,
    "responses":{
        400: {"description": "Bad Request - Invalid currency or amount"},
        401: {"description": "Could not validate credentials"},
        500: {"description": "NBP API is not available, and Redis cache does not contain exchange rates."}}}