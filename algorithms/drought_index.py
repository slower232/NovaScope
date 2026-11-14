"""SPI (McKee et al., 1993) con ajuste gamma por mes calendario.

Requisitos documentados: precipitación mensual, mínimo 20 años (MIN_YEARS_SPI);
con menos años se devuelve el índice pero con advertencia explícita.
"""
import numpy as np
import pandas as pd
from scipy import stats

from config.constants import MIN_YEARS_SPI


def spi(monthly_precip: pd.Series, scale: int = 3):
    """Devuelve (serie SPI, lista de advertencias). monthly_precip: índice mensual (MS)."""
    warnings = []
    p = monthly_precip.asfreq("MS")
    if p.isna().mean() > 0.1:
        warnings.append("more_than_10pct_missing_months")
    acc = p.rolling(scale, min_periods=scale).sum()
    out = pd.Series(np.nan, index=acc.index)
    n_years = int(p.dropna().index.year.nunique())
    if n_years < MIN_YEARS_SPI:
        warnings.append(f"series_shorter_than_{MIN_YEARS_SPI}_years")
    for month in range(1, 13):
        sel = acc[acc.index.month == month].dropna()
        if len(sel) < 10:
            continue
        zeros = (sel <= 0).mean()
        pos = sel[sel > 0]
        if len(pos) < 8:
            continue
        a, loc, scl = stats.gamma.fit(pos, floc=0)
        cdf = zeros + (1 - zeros) * stats.gamma.cdf(sel, a, loc=0, scale=scl)
        cdf = np.clip(cdf, 1e-6, 1 - 1e-6)
        out.loc[sel.index] = stats.norm.ppf(cdf)
    return out, warnings


def spi_category(v: float) -> str:
    if v is None or np.isnan(v):
        return "unknown"
    if v <= -2: return "extreme_dry"
    if v <= -1.5: return "severe_dry"
    if v <= -1: return "moderate_dry"
    if v < 1: return "near_normal"
    if v < 1.5: return "moderate_wet"
    if v < 2: return "severe_wet"
    return "extreme_wet"
