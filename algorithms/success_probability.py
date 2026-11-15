"""Probabilidad EMPÍRICA de completar el ciclo (resultado A).

Definición: P = (#años históricos en que se cumplen TODOS los criterios) / (#años evaluables),
con intervalo de Wilson al 95 %. Criterios por año (ventana desde la fecha de siembra):
  1. Ninguna helada bajo el umbral operativo de la sensibilidad del cultivo.
  2. Fracción de días con Tmax > Tmax_cultivo  <= MAX_HOT_DAY_FRACTION.
  3. Temporal: P efectiva >= 50 % del requerimiento mínimo. Riego: se asume suficiente.
Requiere >= MIN_YEARS_PROBABILITY años; si no, devuelve None y lista qué falta.
NO estima rendimiento (resultado B): no hay datos de rendimiento locales validados.
"""
import math
import numpy as np

from algorithms.crop_suitability import crop_ready, cycle_days, season_window
from algorithms.water_balance import effective_rain
from config.constants import FROST_THRESHOLDS, MAX_HOT_DAY_FRACTION, MIN_YEARS_PROBABILITY


def wilson_interval(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def cycle_completion_probability(daily, crop, month, day=1, irrigated=False, dT=0.0, p_factor=1.0):
    missing = []
    if not crop_ready(crop):
        missing.append("crop_parameters_incomplete")
        return {"probability": None, "missing": missing}
    n = cycle_days(crop)
    thr = FROST_THRESHOLDS[crop["frost_sensitivity"]]["red"]
    req_min = crop["water_mm_min"]
    ok = tot = 0
    fails = {"frost": 0, "heat": 0, "water": 0}
    for y in sorted(set(daily["date"].dt.year)):
        w = season_window(daily, y, month, day, n, dT, p_factor)
        if w is None:
            continue
        tot += 1
        f = bool((w["tmin"] <= thr).any())
        h = bool((w["tmax"] > crop["t_max_growth_c"]).mean() > MAX_HOT_DAY_FRACTION)
        wa = (not irrigated) and effective_rain(float(w["precip"].sum())) < 0.5 * req_min
        fails["frost"] += f; fails["heat"] += h; fails["water"] += wa
        ok += not (f or h or wa)
    if tot < MIN_YEARS_PROBABILITY:
        return {"probability": None, "n_years": tot,
                "missing": [f"need_{MIN_YEARS_PROBABILITY}_years_have_{tot}"]}
    lo, hi = wilson_interval(ok, tot)
    return {"probability": ok / tot, "ci95": (lo, hi), "n_years": tot, "failures": fails,
            "frost_threshold_c": thr, "missing": [],
            "definition": "empirical_fraction_of_historical_years_meeting_all_criteria"}
