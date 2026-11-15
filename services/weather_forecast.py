"""Open-Meteo (pronóstico, NO es NASA). Doc: https://open-meteo.com/en/docs  Licencia CC BY 4.0: atribuir."""
from datetime import datetime
import pandas as pd

from config.settings import settings
from services import data_cache
from services.http import SourceUnavailable, get_json

URL = "https://api.open-meteo.com/v1/forecast"
DAILY = ("temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,"
         "wind_speed_10m_max,wind_gusts_10m_max,shortwave_radiation_sum")


def parse_forecast(js: dict) -> pd.DataFrame:
    d = js["daily"]
    return pd.DataFrame({"date": pd.to_datetime(d["time"]), "tmax": d["temperature_2m_max"],
                         "tmin": d["temperature_2m_min"], "precip": d["precipitation_sum"],
                         "precip_prob": d.get("precipitation_probability_max"),
                         "wind_max": d["wind_speed_10m_max"], "gust_max": d.get("wind_gusts_10m_max"),
                         "solar": d.get("shortwave_radiation_sum")})


def fetch_forecast(lat: float, lon: float, days: int = 7):
    key = data_cache.make_key("openmeteo", lat=round(lat, 2), lon=round(lon, 2), days=days)
    meta = {"source": "Open-Meteo", "product": "Forecast API (modelos meteorológicos; no NASA)",
            "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)", "data_type": "forecast", "error": None}
    hit = data_cache.get(key, settings.ttl_forecast_h)
    if hit:
        return parse_forecast(hit[0]), {**meta, "fetched_at": hit[1], "is_cached": True, "is_stale": False}
    try:
        js = get_json(URL, {"latitude": round(lat, 4), "longitude": round(lon, 4), "daily": DAILY,
                            "forecast_days": days, "timezone": "auto"})
        data_cache.put(key, "openmeteo", js)
        return parse_forecast(js), {**meta, "fetched_at": datetime.utcnow(), "is_cached": False, "is_stale": False}
    except (SourceUnavailable, KeyError) as e:
        stale = data_cache.get(key, settings.ttl_forecast_h, allow_stale=True)
        if stale:
            return parse_forecast(stale[0]), {**meta, "fetched_at": stale[1], "is_cached": True, "is_stale": True, "error": str(e)}
        return None, {**meta, "fetched_at": None, "is_cached": False, "is_stale": False, "error": str(e)}
