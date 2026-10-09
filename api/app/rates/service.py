"""Fetching exchange rates from the NBP API and caching them in Redis."""

import json
from datetime import date

import redis
import requests
from fastapi import HTTPException

from app.core.config import NBP_API_URL, REDIS_HOST, REDIS_PORT, SUPPORT_EMAIL

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


def get_exchange_rates():
    """Fetches exchange rates from the NBP API and caches them in Redis for 24 hours.
    After 24 hours, the data is refreshed by fetching new rates from the API
    to ensure accuracy while maintaining availability if the API is down.
    If the API is unavailable, the system uses the last saved exchange rates from the cache.
    """

    today = date.today()
    redis_key = f"exchange_rates:{today.isoformat()}"

    # Checking the Redis cache
    cached_data = redis_client.get(redis_key)
    if cached_data:
        data = json.loads(cached_data)
        return data["rates"], data["effectiveDate"]

    # Attempting to retrieve data from API
    try:
        response = requests.get(NBP_API_URL)
        response.raise_for_status()

    except requests.RequestException as err:
        # If the API is unavailable, try to use the cached data
        last_available_key = redis_client.keys("exchange_rates:*")
        if last_available_key:
            last_available_key = sorted(last_available_key)[-1]
            cached_data = redis_client.get(last_available_key)
            if cached_data:
                data = json.loads(cached_data)
                return data["rates"], data["effectiveDate"]
        else:
            raise HTTPException(
                # If the NBP API is unavailable and there is no data in the redis cached
                status_code=500,
                detail=f"Currently, it is not possible to access the NBP API"
                f"Please contact support via email: {SUPPORT_EMAIL}",
            ) from err

    # Retrieving relevant data from the API response
    data_api = response.json()[0]
    effectivedate = data_api["effectiveDate"]
    rates_data = data_api["rates"]
    rate_list = {rate["code"]: rate["ask"] for rate in rates_data}  # ask values need to use

    # Caching data in Redis
    cache_payload = {"rates": rate_list, "effectiveDate": effectivedate}
    redis_client.setex(redis_key, 86400, json.dumps(cache_payload))

    # Deleting old cache (all keys that are not for today's date)
    all_keys = redis_client.keys("exchange_rates:*")
    for key in all_keys:
        if key != redis_key:
            redis_client.delete(key)

    return rate_list, effectivedate
