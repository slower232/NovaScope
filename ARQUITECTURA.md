# Arquitectura
```
app.py                  Enrutamiento, login, selector de parcela
ui/context.py           Idioma, trazabilidad, carga de datos con caché, analyze(farm)
ui/pages/               dashboard (Canvas), farms, recommendations, rotation, environment, water, alerts, simulator, reports
ui/translations/        es.py, en.py (todo el texto visible)
modules/                geospatial, risk_engine, recommendations, crop_rotation (catálogo), simulation, reporting
algorithms/             SPI, anomalías, ET0, idoneidad, probabilidad, resumen hídrico, optimizador, incertidumbre
services/               nasa_power, weather_forecast, data_cache (SQLite), http
database/               models, connection, repositories, initialization, migrations
authentication/         auth, permissions, password_security (scrypt)
data/                   crops/crops.json (catálogo editable), reference/rotation_weights.json
```
Flujo: UI → `analyze()` → servicios (caché SQLite → API) → algoritmos/motores → UI. Un fallo de fuente produce estado "no disponible/gris", nunca datos sustitutos.
Esquema: `users`, `farms` (+ perfil agrícola), `farm_boundaries`, `api_cache`, `risk_alerts`, `rotation_plans`, `simulations`. `ensure_columns()` agrega columnas nuevas a bases existentes sin borrar datos.
