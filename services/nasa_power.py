"""NASA POWER – API diaria puntual. Doc: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
Endpoint: https://power.larc.nasa.gov/api/temporal/daily/point  (community=AG)
"""
from datetime import date, timedelta
import numpy as np
import pandas as pd

from config.constants import POWER_FILL_VALUE, POWER_PARAMS, POWER_RESOLUTION
from config.settings import settings
from services import data_cache
from services.http import SourceUnavailable, get_json

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def parse_power_response(js: dict) -> pd.DataFrame:
    par = js["properties"]["parameter"]
    cols = {}
    for api_name, name in POWER_PARAMS.items():
        if api_name in par:
            cols[name] = pd.Series(par[api_name])
    df = pd.DataFrame(cols)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.replace(POWER_FILL_VALUE, np.nan)
    df.index.name = "date"
    return df.reset_index()


def fetch_daily(lat: float, lon: float, years: int | None = None):
    """Devuelve (DataFrame, meta). meta: source, product, fetched_at, is_cached, is_stale, resolution, error."""
    years = years or settings.history_years
    end = date.today() - timedelta(days=5)  # latencia típica de POWER
    start = date(end.year - years, 1, 1)
    key = data_cache.make_key("power", lat=round(lat, 2), lon=round(lon, 2), start=start.isoformat(),
                              end=end.isoformat())
    hit = data_cache.get(key, settings.ttl_power_h)
    meta = {"source": "NASA POWER", "product": "Daily AG community", "resolution": POWER_RESOLUTION, "error": None}
    if hit:
        df = pd.DataFrame(hit[0]); df["date"] = pd.to_datetime(df["date"])
        return df, {**meta, "fetched_at": hit[1], "is_cached": True, "is_stale": False}
    try:
        js = get_json(URL, {"parameters": ",".join(POWER_PARAMS), "community": "AG", "latitude": round(lat, 4),
                            "longitude": round(lon, 4), "start": start.strftime("%Y%m%d"),
                            "end": end.strftime("%Y%m%d"), "format": "JSON"})
        df = parse_power_response(js)
        out = df.copy(); out["date"] = out["date"].dt.strftime("%Y-%m-%d")
        data_cache.put(key, "power", out.to_dict("list"))
        from datetime import datetime
        return df, {**meta, "fetched_at": datetime.utcnow(), "is_cached": False, "is_stale": False}
    except (SourceUnavailable, KeyError) as e:
        stale = data_cache.get(key, settings.ttl_power_h, allow_stale=True)
        if stale:
            df = pd.DataFrame(stale[0]); df["date"] = pd.to_datetime(df["date"])
            return df, {**meta, "fetched_at": stale[1], "is_cached": True, "is_stale": True, "error": str(e)}
        return None, {**meta, "fetched_at": None, "is_cached": False, "is_stale": False, "error": str(e)}
