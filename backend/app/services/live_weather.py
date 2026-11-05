
from datetime import datetime, timezone
from time import monotonic
import asyncio
import logging

import httpx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

CACHE_TTL_SECONDS = 15 * 60
CACHE_MAX_SIZE = 100

logger = logging.getLogger(__name__)

# In-memory cache: rounded coordinates -> (expiry, weather features)
_weather_cache = {}
_cache_lock = asyncio.Lock()


def _calculate_features(data):
    h = data.get("hourly", {})

    rain = h.get("precipitation", [])
    sm0 = h.get("soil_moisture_0_to_7cm", [])
    sm1 = h.get("soil_moisture_7_to_28cm", [])

    def total(n):
        vals = [float(v) for v in rain[-n:] if v is not None]
        return sum(vals) if vals else None

    def mean_pct(values):
        vals = [float(v) for v in values[-24:] if v is not None]
        return sum(vals) / len(vals) * 100 if vals else None

    return {
        "rain_24h_mm": total(24),
        "rain_72h_mm": total(72),
        "rain_7d_mm": total(168),
        "soil_moisture_0_7cm_pct": mean_pct(sm0),
        "soil_moisture_7_28cm_pct": mean_pct(sm1),
        "elevation_m": data.get("elevation"),
        "weather_source": "Open-Meteo Forecast API",
        "source_model": "Best Match; hourly precipitation and soil moisture",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "timezone": "UTC",
        "weather_status": "live",
    }


def _cached_result(features, status):
    result = features.copy()
    result["weather_status"] = status
    result["weather_cache_notice"] = (
        "Using previously retrieved weather data because the weather provider "
        "is temporarily unavailable."
        if status == "stale_cache"
        else None
    )
    return result


async def get_live_features(latitude: float, longitude: float):
    # Rounded coordinates allow nearby repeated requests to share a cache entry.
    cache_key = (round(latitude, 3), round(longitude, 3))

    async with _cache_lock:
        cached = _weather_cache.get(cache_key)

        if cached and monotonic() < cached[0]:
            return _cached_result(cached[1], "cached")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "precipitation,"
            "soil_moisture_0_to_7cm,"
            "soil_moisture_7_to_28cm"
        ),
        "past_days": 7,
        "forecast_days": 1,
        "timezone": "UTC",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(FORECAST_URL, params=params)

            if response.status_code == 429:
                logger.warning("Open-Meteo rate limit reached.")

                async with _cache_lock:
                    cached = _weather_cache.get(cache_key)

                if cached:
                    return _cached_result(cached[1], "stale_cache")

                raise RuntimeError(
                    "Weather provider rate limit reached and no cached "
                    "weather data is available for this location."
                )

            response.raise_for_status()
            data = response.json()

        features = _calculate_features(data)

        async with _cache_lock:
            # Remove expired entries.
            now = monotonic()
            expired = [
                key for key, value in _weather_cache.items()
                if now >= value[0]
            ]

            for key in expired:
                _weather_cache.pop(key, None)

            # Keep the cache bounded.
            if len(_weather_cache) >= CACHE_MAX_SIZE:
                oldest_key = next(iter(_weather_cache))
                _weather_cache.pop(oldest_key, None)

            _weather_cache[cache_key] = (
                now + CACHE_TTL_SECONDS,
                features,
            )

        return _cached_result(features, "live")

    except httpx.HTTPStatusError as exc:
        logger.error("Weather API HTTP error: %s", exc)

    except (httpx.RequestError, ValueError) as exc:
        logger.error("Weather API request failed: %s", exc)

    # Fallback to an expired cache entry when the provider is unavailable.
    async with _cache_lock:
        cached = _weather_cache.get(cache_key)

    if cached:
        return _cached_result(cached[1], "stale_cache")

    raise RuntimeError(
        "Weather data is temporarily unavailable. "
        "No cached weather data exists for this location."
    )
