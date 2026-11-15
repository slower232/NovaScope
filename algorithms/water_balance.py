"""ET0 de Hargreaves-Samani (FAO-56 ec. 52) y balance hídrico simplificado.

ΔS = P_efectiva + Riego − ETc − Escorrentía − Drenaje. Sin parámetros de suelo/Kc
no se estiman escorrentía ni drenaje: el balance es de "disponibilidad vs. requerimiento".
"""
import math
import numpy as np
import pandas as pd

from config.constants import EFFECTIVE_RAIN_FACTOR

GSC = 0.0820  # MJ m-2 min-1


def extraterrestrial_radiation(lat_deg: float, doy: np.ndarray) -> np.ndarray:
    """Ra en MJ m-2 día-1 (FAO-56 ec. 21)."""
    phi = math.radians(lat_deg)
    doy = np.asarray(doy, dtype=float)
    dr = 1 + 0.033 * np.cos(2 * math.pi * doy / 365)
    delta = 0.409 * np.sin(2 * math.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    ra = (24 * 60 / math.pi) * GSC * dr * (
        ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))
    return np.maximum(ra, 0)


def et0_hargreaves(tmin, tmax, lat_deg: float, dates) -> np.ndarray:
    """ET0 (mm/día) = 0.0023·Ra·(Tmean+17.8)·sqrt(Tmax−Tmin), Ra en mm/día (÷2.45)."""
    tmin = np.asarray(tmin, float); tmax = np.asarray(tmax, float)
    doy = pd.DatetimeIndex(dates).dayofyear.values
    ra = extraterrestrial_radiation(lat_deg, doy) / 2.45
    tmean = (tmin + tmax) / 2
    return np.maximum(0.0023 * ra * (tmean + 17.8) * np.sqrt(np.maximum(tmax - tmin, 0)), 0)


def effective_rain(p_mm: float, factor: float = EFFECTIVE_RAIN_FACTOR) -> float:
    return float(p_mm) * factor


def supply_requirement(p_total_mm: float, requirement_mm: float, irrigated: bool):
    """Devuelve dict con P efectiva, requerimiento y déficit (mm). Si hay riego se reporta la brecha a cubrir."""
    peff = effective_rain(p_total_mm)
    deficit = max(requirement_mm - peff, 0.0)
    return {"p_effective_mm": peff, "requirement_mm": requirement_mm, "deficit_mm": deficit,
            "irrigation_needed_mm": deficit if irrigated else None,
            "coverage_ratio": min(peff / requirement_mm, 1.0) if requirement_mm else None}
