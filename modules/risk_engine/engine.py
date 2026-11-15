"""Motor de riesgos independiente: 8 categorías, semáforo verde/amarillo/rojo/gris.

Devuelve claves de traducción + parámetros; el texto lo resuelve la capa de UI/reportes.
Ausencia de datos => GRIS (nunca verde).
"""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from algorithms.water_balance import et0_hargreaves
from config import constants as K

RISKS = ["meteorological_drought", "water_stress", "extreme_temperature", "frost",
         "heat_wave", "heavy_rain", "flood", "strong_wind"]


@dataclass
class RiskResult:
    key: str
    level: str
    params: dict = field(default_factory=dict)
    source: str = ""
    importance: str = "medium"
    kind: str = "forecast"   # forecast = pronóstico meteorológico; estimate = estimación con datos NASA POWER (modelo/reanálisis)


def _lvl(value, yellow, red, higher_is_worse=True):
    if higher_is_worse:
        return "red" if value >= red else "yellow" if value >= yellow else "green"
    return "red" if value <= red else "yellow" if value <= yellow else "green"


def _consecutive_max(mask) -> int:
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def evaluate_risks(crop: dict, forecast: pd.DataFrame | None, recent: pd.DataFrame | None,
                   spi_value: float | None, tmax_p90_by_month: dict | None, irrigated: bool,
                   lat: float, horizon_days: int = 7) -> list[RiskResult]:
    """forecast: date,tmax,tmin,precip,wind_max (Open-Meteo). recent: date,tmax,tmin,precip (POWER)."""
    f = forecast.head(horizon_days) if forecast is not None and len(forecast) else None
    res = []
    imp = {"high": "high", "medium": "medium", "low": "low"}
    # 1 Sequía meteorológica (SPI-3)
    if spi_value is None or np.isnan(spi_value):
        res.append(RiskResult("meteorological_drought", "gray", {}, "NASA POWER (SPI)", imp[crop["drought_sensitivity"]]))
    else:
        res.append(RiskResult("meteorological_drought", _lvl(spi_value, K.SPI_YELLOW, K.SPI_RED, False),
                              {"spi": round(float(spi_value), 2)}, "NASA POWER (SPI-3)", imp[crop["drought_sensitivity"]]))
    # 2 Estrés hídrico (P/ET0 30 días; solo temporal)
    if irrigated or recent is None or len(recent) < 25:
        res.append(RiskResult("water_stress", "gray", {"reason": "irrigated" if irrigated else "no_data"},
                              "NASA POWER + Hargreaves", imp[crop["drought_sensitivity"]]))
    else:
        r = recent.tail(30)
        et0 = et0_hargreaves(r["tmin"], r["tmax"], lat, r["date"]).sum()
        ratio = float(r["precip"].sum() / et0) if et0 > 0 else float("nan")
        level = "gray" if np.isnan(ratio) else _lvl(ratio, K.WATER_STRESS_YELLOW, K.WATER_STRESS_RED, False)
        res.append(RiskResult("water_stress", level, {"ratio": round(ratio, 2), "p": round(float(r["precip"].sum()), 1),
                              "et0": round(float(et0), 1)}, "NASA POWER + Hargreaves", imp[crop["drought_sensitivity"]]))
    # 3 Temperaturas extremas (requiere Tmax del cultivo)
    tmaxc = crop.get("t_max_growth_c")
    if f is None or tmaxc is None:
        res.append(RiskResult("extreme_temperature", "gray", {}, "Open-Meteo", imp[crop["heat_sensitivity"]]))
    else:
        peak = float(f["tmax"].max())
        res.append(RiskResult("extreme_temperature", _lvl(peak, tmaxc - 3, tmaxc),
                              {"peak": round(peak, 1), "limit": tmaxc}, "Open-Meteo (pronóstico)", imp[crop["heat_sensitivity"]]))
    # 4 Heladas
    if f is None:
        res.append(RiskResult("frost", "gray", {}, "Open-Meteo", imp[crop["frost_sensitivity"]]))
    else:
        thr = K.FROST_THRESHOLDS[crop["frost_sensitivity"]]
        low = float(f["tmin"].min())
        res.append(RiskResult("frost", _lvl(low, thr["yellow"], thr["red"], False),
                              {"min": round(low, 1), "thr": thr["red"]}, "Open-Meteo (pronóstico)", imp[crop["frost_sensitivity"]]))
    # 5 Ola de calor (≥3 días seguidos sobre P90 climatológico mensual)
    if f is None or not tmax_p90_by_month:
        res.append(RiskResult("heat_wave", "gray", {}, "Open-Meteo + NASA POWER", imp[crop["heat_sensitivity"]]))
    else:
        p90 = f["date"].dt.month.map(tmax_p90_by_month)
        n = _consecutive_max((f["tmax"] > p90).values)
        level = "red" if n >= K.HEATWAVE_MIN_DAYS_RED else "yellow" if n >= K.HEATWAVE_MIN_DAYS_YELLOW else "green"
        res.append(RiskResult("heat_wave", level, {"days": n}, "Open-Meteo + NASA POWER (P90)", imp[crop["heat_sensitivity"]]))
    # 6 Precipitación intensa
    if f is None:
        res.append(RiskResult("heavy_rain", "gray", {}, "Open-Meteo", "medium"))
        res.append(RiskResult("flood", "gray", {}, "Open-Meteo", "medium"))
    else:
        mx = float(f["precip"].max())
        res.append(RiskResult("heavy_rain", _lvl(mx, K.HEAVY_RAIN_YELLOW, K.HEAVY_RAIN_RED), {"max": round(mx, 1)},
                              "Open-Meteo (pronóstico)", "medium"))
        acc3 = float(f["precip"].rolling(3, min_periods=1).sum().max())
        res.append(RiskResult("flood", _lvl(acc3, K.FLOOD_3D_YELLOW, K.FLOOD_3D_RED), {"acc3": round(acc3, 1)},
                              "Open-Meteo (indicador indirecto; sin topografía)", "medium"))
    # 8 Viento
    if f is None or "wind_max" not in f:
        res.append(RiskResult("strong_wind", "gray", {}, "Open-Meteo", "medium"))
    else:
        w = float(f["wind_max"].max())
        res.append(RiskResult("strong_wind", _lvl(w, K.WIND_YELLOW, K.WIND_RED), {"max": round(w, 0)},
                              "Open-Meteo (pronóstico)", "medium"))
    for r in res:
        r.kind = "estimate" if r.key in ("meteorological_drought", "water_stress") else "forecast"
    return res


def overall_level(results: list[RiskResult]) -> dict:
    """El peor riesgo individual manda; un promedio nunca oculta un rojo."""
    sev = [K.SEVERITY[r.level] for r in results]
    worst = max(sev) if sev else -1
    level = {v: k for k, v in K.SEVERITY.items()}[worst] if worst >= 0 else "gray"
    n_gray = sum(r.level == "gray" for r in results)
    return {"level": level, "n_gray": n_gray, "n_red": sum(r.level == "red" for r in results),
            "n_yellow": sum(r.level == "yellow" for r in results),
            "critical": [r.key for r in results if r.level == "red"]}
