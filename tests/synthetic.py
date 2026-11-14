"""Series SINTÉTICAS solo para pruebas unitarias (nunca se usan en la app)."""
import numpy as np, pandas as pd


def synthetic_daily(years=20, lat=28.6, seed=0, start_year=2005):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(f"{start_year}-01-01", periods=int(years * 365.25), freq="D")
    doy = dates.dayofyear.values
    tmean = 17 + 10 * np.sin(2 * np.pi * (doy - 110) / 365) + rng.normal(0, 2, len(dates))
    rain_season = np.where((dates.month >= 6) & (dates.month <= 9), 0.35, 0.05)
    precip = np.where(rng.random(len(dates)) < rain_season, rng.gamma(1.5, 6, len(dates)), 0.0)
    return pd.DataFrame({"date": dates, "tmean": tmean, "tmax": tmean + 7, "tmin": tmean - 7, "precip": precip})
