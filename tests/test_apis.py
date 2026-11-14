"""Pruebas de PARSEO con respuestas de ejemplo con la forma documentada (no requieren red).
La validación contra los servicios reales se hace con scripts/validate_connections.py."""
from services.nasa_power import parse_power_response
from services.weather_forecast import parse_forecast


def test_power_parse_handles_fill_values():
    js = {"properties": {"parameter": {"T2M": {"20240101": 5.0, "20240102": -999.0},
                                       "PRECTOTCORR": {"20240101": 0.0, "20240102": 2.5}}}}
    df = parse_power_response(js)
    assert list(df.columns) == ["date", "tmean", "precip"] and df["tmean"].isna().sum() == 1


def test_open_meteo_parse():
    js = {"daily": {"time": ["2026-07-01"], "temperature_2m_max": [30.1], "temperature_2m_min": [15.0],
                    "precipitation_sum": [0.0], "wind_speed_10m_max": [12.0]}}
    df = parse_forecast(js)
    assert df.loc[0, "tmax"] == 30.1
