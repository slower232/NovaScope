"""Climatología mensual y anomalías. Entrada: DataFrame diario con índice 'date' (datetime)."""
import numpy as np
import pandas as pd


def monthly_aggregate(df: pd.DataFrame, var: str, how: str) -> pd.Series:
    """how='sum' (precipitación) o 'mean' (temperaturas). Meses incompletos (<80 % de días) -> NaN."""
    s = df.set_index("date")[var] if "date" in df.columns else df[var]
    g = s.resample("MS")
    agg = g.sum(min_count=1) if how == "sum" else g.mean()
    cnt = g.count()
    expected = s.resample("MS").size()
    agg[(cnt / expected) < 0.8] = np.nan
    return agg


def monthly_climatology(monthly: pd.Series) -> pd.DataFrame:
    """Media y desviación por mes calendario, con número de años usados."""
    g = monthly.dropna().groupby(monthly.dropna().index.month)
    return pd.DataFrame({"mean": g.mean(), "std": g.std(ddof=1), "n_years": g.count()})


def monthly_anomalies(monthly: pd.Series) -> pd.DataFrame:
    """Anomalía absoluta y puntaje z respecto a la climatología del mismo mes."""
    clim = monthly_climatology(monthly)
    out = pd.DataFrame({"value": monthly})
    m = out.index.month
    out["clim_mean"] = clim["mean"].reindex(m).values
    out["clim_std"] = clim["std"].reindex(m).values
    out["anomaly"] = out["value"] - out["clim_mean"]
    std = out["clim_std"].replace(0, np.nan)
    out["z"] = out["anomaly"] / std
    return out


def classify_z(z: float) -> str:
    if z is None or np.isnan(z):
        return "unknown"
    if abs(z) >= 2:
        return "extreme"
    if abs(z) >= 1:
        return "notable"
    return "normal"
