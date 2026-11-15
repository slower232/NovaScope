"""Prueba las conexiones reales (requiere internet). Uso: python -m scripts.validate_connections"""
from services.nasa_power import fetch_daily
from services.weather_forecast import fetch_forecast
from database.initialization import init_db

if __name__ == "__main__":
    init_db()
    lat, lon = 28.6353, -106.0889  # Chihuahua, Chih.
    df, m = fetch_daily(lat, lon, years=2)
    print("POWER:", "OK" if df is not None else "FALLÓ", len(df) if df is not None else "", m["error"])
    df, m = fetch_forecast(lat, lon)
    print("Open-Meteo:", "OK" if df is not None else "FALLÓ", len(df) if df is not None else "", m["error"])
