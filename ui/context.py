"""Utilidades compartidas de la interfaz: idioma, trazabilidad, carga de datos y análisis de parcela."""
import json
import streamlit as st

from algorithms.climate_anomalies import monthly_aggregate
from algorithms.drought_index import spi
from algorithms.water_summary import water_summary
from modules.crop_rotation.crop_catalog import get_crop, load_crops
from modules.risk_engine.engine import evaluate_risks, overall_level
from services.nasa_power import fetch_daily
from services.weather_forecast import fetch_forecast
from ui.styles import ICON
from ui.translations import t

CROPS = load_crops()
PAGES = ["dashboard", "recommendations", "environment"]
MONTHS = {"es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
          "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}


def lang() -> str:
    return st.session_state.get("lang", "en")


def T(key: str, **kw) -> str:
    return t(key, lang(), **kw)


def crop_name(crop_id: str) -> str:
    for c in CROPS:
        if c["id"] == crop_id:
            return c["name_es"] if lang() == "es" else c["name_en"]
    return crop_id


def go(page: str):
    st.session_state["page"] = page


def badge(level: str) -> str:
    return f'<span class="fs-badge fs-{level}">{ICON[level]} {T("level." + level)}</span>'


def data_status(meta: dict):
    if meta.get("fetched_at") is None:
        st.error(T("status.unavailable", e=meta.get("error")))
        return
    when = meta["fetched_at"].strftime("%Y-%m-%d %H:%M UTC")
    if meta.get("is_stale"):
        st.warning(T("status.stale", t=when))
    elif meta.get("is_cached"):
        st.caption("💾 " + T("status.cached", t=when))
    else:
        st.caption("🛰️ " + T("status.fresh"))


def trace_caption(meta: dict):
    """Trazabilidad: fuente, tipo de dato, resolución y fecha de consulta."""
    when = meta["fetched_at"].strftime("%Y-%m-%d %H:%M UTC") if meta.get("fetched_at") else "—"
    st.caption("🔎 " + T("trace.line", s=f"{meta['source']} ({meta['product']})", d=T("dtype." + meta["data_type"]),
                         r=meta.get("resolution", "—"), t=when))


def farm_dict(farm) -> dict:
    """Perfil de la parcela. 'crop_history' = [cultivo actual] + ciclos anteriores (más reciente primero)."""
    hist = json.loads(farm.crop_history) if farm.crop_history else []
    prefs = json.loads(farm.preferences) if farm.preferences else {}
    return {"id": farm.id, "name": farm.name, "lat": farm.lat, "lon": farm.lon, "crop_id": farm.crop_id,
            "irrigated": farm.irrigated, "soil_ph": farm.soil_ph, "soil_texture": farm.soil_texture,
            "organic_matter": farm.organic_matter, "water_availability": farm.water_availability,
            "crop_history": [farm.crop_id] + hist, "past_history": hist, "exclude": prefs.get("exclude", [])}


@st.cache_data(ttl=3600, show_spinner=False)
def load_power(lat, lon):
    return fetch_daily(lat, lon)


@st.cache_data(ttl=900, show_spinner=False)
def load_forecast(lat, lon):
    return fetch_forecast(lat, lon, 7)


def analyze(farm) -> dict:
    """Reúne datos REALES y corre los motores. Un fallo de fuente se refleja como gris/insuficiente, nunca se inventa."""
    crop = get_crop(farm.crop_id, CROPS)
    power, pmeta = load_power(farm.lat, farm.lon)
    fc, fmeta = load_forecast(farm.lat, farm.lon)
    spi_val, spi_warn, p90, recent, series = None, [], None, None, None
    if power is not None:
        series, spi_warn = spi(monthly_aggregate(power, "precip", "sum"), 3)
        v = series.dropna()
        spi_val = float(v.iloc[-1]) if len(v) else None
        p90 = power.groupby(power["date"].dt.month)["tmax"].quantile(0.9).to_dict()
        recent = power.dropna(subset=["tmax", "tmin", "precip"]).tail(40)
    risks = evaluate_risks(crop, fc, recent, spi_val, p90, farm.irrigated, farm.lat)
    wsum = water_summary(power, farm.irrigated, spi_val) if power is not None else {"status": "insufficient", "reason": "no_data"}
    return dict(crop=crop, power=power, pmeta=pmeta, fc=fc, fmeta=fmeta, risks=risks, overall=overall_level(risks),
                spi_series=spi_series_safe(series), spi_warn=spi_warn, spi_value=spi_val, p90=p90, recent=recent, water=wsum)


def spi_series_safe(s):
    return s
