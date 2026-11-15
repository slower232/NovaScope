"""Índice de idoneidad agroclimática (C). NO es una probabilidad."""
import numpy as np
import pandas as pd

from algorithms.water_balance import effective_rain


def temperature_response(t, tmin, tlo, thi, tmax):
    """Respuesta trapezoidal 0-1 a la temperatura media diaria."""
    t = np.asarray(t, float)
    r = np.zeros_like(t)
    up = (t > tmin) & (t < tlo)
    r[up] = (t[up] - tmin) / (tlo - tmin)
    r[(t >= tlo) & (t <= thi)] = 1.0
    dn = (t > thi) & (t < tmax)
    r[dn] = (tmax - t[dn]) / (tmax - thi)
    return r


def crop_ready(crop: dict) -> bool:
    keys = ["t_min_growth_c", "t_opt_low_c", "t_opt_high_c", "t_max_growth_c",
            "cycle_days_min", "cycle_days_max", "water_mm_min", "water_mm_max"]
    return all(crop.get(k) is not None for k in keys)


def cycle_days(crop: dict) -> int:
    return int(round((crop["cycle_days_min"] + crop["cycle_days_max"]) / 2))


def season_window(daily: pd.DataFrame, year: int, month: int, day: int, n_days: int,
                  dT: float = 0.0, p_factor: float = 1.0):
    """Ventana del ciclo para un año histórico; None si faltan >10 % de días."""
    start = pd.Timestamp(year=year, month=month, day=day)
    end = start + pd.Timedelta(days=n_days - 1)
    w = daily[(daily["date"] >= start) & (daily["date"] <= end)].copy()
    if len(w) < 0.9 * n_days or w["tmean"].isna().mean() > 0.1:
        return None
    for c in ("tmean", "tmax", "tmin"):
        w[c] = w[c] + dT
    w["precip"] = w["precip"] * p_factor
    return w


def suitability_for_year(w: pd.DataFrame, crop: dict, irrigated: bool):
    t = temperature_response(w["tmean"].fillna(w["tmean"].mean()).values,
                             crop["t_min_growth_c"], crop["t_opt_low_c"],
                             crop["t_opt_high_c"], crop["t_max_growth_c"])
    t_score = float(t.mean())
    req = (crop["water_mm_min"] + crop["water_mm_max"]) / 2
    if irrigated:
        w_score = 1.0  # supuesto explícito: riego suficiente
    else:
        w_score = min(effective_rain(float(w["precip"].sum())) / req, 1.0)
    return t_score, w_score


def suitability_index(daily: pd.DataFrame, crop: dict, month: int, day: int = 1,
                      irrigated: bool = False, dT: float = 0.0, p_factor: float = 1.0):
    """Media sobre años históricos de SI = sqrt(T_score · W_score). Devuelve dict o None."""
    if not crop_ready(crop):
        return None
    n = cycle_days(crop)
    years = sorted(set(daily["date"].dt.year))
    rows = []
    for y in years:
        w = season_window(daily, y, month, day, n, dT, p_factor)
        if w is None:
            continue
        ts, ws = suitability_for_year(w, crop, irrigated)
        rows.append((ts, ws, float(np.sqrt(ts * ws))))
    if len(rows) < 3:
        return None
    a = np.array(rows)
    return {"temperature_score": a[:, 0].mean(), "water_score": a[:, 1].mean(),
            "index": a[:, 2].mean(), "index_std": a[:, 2].std(ddof=1), "n_years": len(rows),
            "assumes_irrigation_sufficient": irrigated}
