"""Resumen hídrico SIMPLE: orientación, no necesidades exactas de riego.

Entradas: precipitación diaria (NASA POWER), SPI-3 opcional. NO usa humedad de suelo (SMAP aún no integrado).
Estados: favorable | limited | possible_stress | insufficient.
Regla (heurística documentada en METODOLOGIA_AGRONOMICA.md):
  ratio = P(30 d recientes) / media histórica de P en el mismo periodo calendario.
  - sin climatología suficiente (<10 años) o base < 10 mm -> 'insufficient' (o 'limited' si hay lluvia nula en época normalmente seca)
  - ratio >= 0.8 y SPI >= -0.5 (o sin SPI) -> favorable
  - ratio < 0.5 o SPI <= -1  -> possible_stress (en riego se reporta como 'limited': la lluvia no es la única fuente de agua)
  - resto -> limited
"""
import numpy as np
import pandas as pd

from config.constants import WATER_MIN_BASELINE_MM, WATER_RATIO_FAVORABLE, WATER_RATIO_STRESS


def water_summary(daily: pd.DataFrame, irrigated: bool, spi_value=None, window: int = 30):
    d = daily.dropna(subset=["precip"]).sort_values("date")
    if len(d) < window:
        return {"status": "insufficient", "reason": "no_recent_data"}
    end = d["date"].iloc[-1]
    start = end - pd.Timedelta(days=window - 1)
    recent = d[(d["date"] >= start) & (d["date"] <= end)]
    if len(recent) < 0.8 * window:
        return {"status": "insufficient", "reason": "gaps_in_recent_data"}
    p30 = float(recent["precip"].sum()); p7 = float(recent.tail(7)["precip"].sum())
    hist = []
    for k in range(1, 21):
        s, e = start - pd.DateOffset(years=k), end - pd.DateOffset(years=k)
        w = d[(d["date"] >= s) & (d["date"] <= e)]
        if len(w) >= 0.8 * window:
            hist.append(float(w["precip"].sum()))
    tmean = float(recent["tmean"].mean()) if "tmean" in recent and recent["tmean"].notna().any() else None
    out = {"p30_mm": round(p30, 1), "p7_mm": round(p7, 1), "tmean_30d": None if tmean is None else round(tmean, 1),
           "period": (start.date().isoformat(), end.date().isoformat()), "n_hist_years": len(hist),
           "spi3": None if spi_value is None or np.isnan(spi_value) else round(float(spi_value), 2),
           "irrigated": irrigated, "data_through": end.date().isoformat(),
           "basis": "NASA POWER (estimación; celda ~50 km). Sin humedad de suelo."}
    if len(hist) < 10:
        return {**out, "status": "insufficient", "reason": "short_history", "baseline_mm": None, "ratio": None}
    base = float(np.mean(hist))
    out["baseline_mm"] = round(base, 1)
    if base < WATER_MIN_BASELINE_MM:
        return {**out, "status": "limited", "reason": "normally_dry_period", "ratio": None}
    ratio = p30 / base
    out["ratio"] = round(ratio, 2)
    spi = out["spi3"]
    if ratio >= WATER_RATIO_FAVORABLE and (spi is None or spi >= -0.5):
        status = "favorable"
    elif ratio < WATER_RATIO_STRESS or (spi is not None and spi <= -1.0):
        status = "limited" if irrigated else "possible_stress"
    else:
        status = "limited"
    return {**out, "status": status, "reason": "ok"}
