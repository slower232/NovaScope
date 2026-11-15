# Auditoría del proyecto FieldShift

**Alcance de la auditoría:** el repositorio es el generado en la sesión anterior (v1, ~1 900 líneas, 60 archivos); no existe otro código previo.
Entorno de verificación: Python 3.12 con numpy/pandas/scipy/reportlab; **sin internet y sin Streamlit, SQLAlchemy, Folium ni Plotly**. Lo que depende de ellos no pudo ejecutarse.

## 1. Arquitectura (v1 → v2)
v1: `app.py` monolítico (~300 líneas) + `algorithms/`, `modules/`, `services/`, `database/`, `authentication/`, `ui/translations/`.
v2: `app.py` solo enruta; páginas en `ui/pages/*`, utilidades en `ui/context.py`.

## 2. Estado real de cada funcionalidad
| Componente | Estado (v2) | Evidencia |
|---|---|---|
| SPI, anomalías, ET0 Hargreaves, idoneidad, probabilidad empírica | Funcional y comprobado (datos sintéticos de prueba) | `tests/test_algorithms.py` |
| Motor de riesgos (8 categorías, gris = sin datos) | Funcional y comprobado | `tests/test_risk_engine.py` |
| Optimizador de rotación, historial, exclusiones, comparación con estrategia actual, sensibilidad de pesos | Funcional y comprobado | `tests/test_rotation.py`, `tests/test_v2.py` |
| Recomendaciones por categoría de compatibilidad | Funcional y comprobado | `tests/test_v2.py` |
| Resumen hídrico simple | Funcional y comprobado | `tests/test_v2.py` |
| Cálculo de superficie, validación de polígono y alcance Chihuahua | Funcional y comprobado | `tests/test_geospatial.py`, `tests/test_v2.py` |
| Migración de columnas SQLite | Funcional y comprobado (SQLite en memoria) | `tests/test_v2.py` |
| Hash scrypt de contraseñas | Comprobado manualmente | verificación directa (la prueba formal se omite sin SQLAlchemy) |
| PDF de diagnóstico | Funcional (generado y abierto) | smoke test |
| Traducciones es/en | Funcional; prueba de claves faltantes | `tests/test_translations.py` |
| Base de datos SQLAlchemy, autenticación, repositorios | **Implementado, sin validación** (falta SQLAlchemy aquí) | `tests/test_database.py` se omite |
| NASA POWER y Open-Meteo | **Implementado, sin validación contra la red real** | `scripts/validate_connections.py` |
| Interfaz Streamlit (dashboard Canvas, mapa Folium/Draw) | **Implementado, sin ejecutar** | solo comprobación sintáctica |
| SMAP, GPM/IMERG, Sentinel-2/HLS (NDVI), ECOSTRESS, ERA5, suelo para México | **No implementado** | — |
| Alertas por vegetación | No implementado (depende de NDVI) | — |
| Asistente explicativo | No implementado | — |

## 3. Problemas identificados en v1 (y qué se hizo)
1. `app.py` concentraba toda la interfaz → dividido en `ui/pages/`.
2. Sin validación de cobertura geográfica → solo Chihuahua (caja aproximada; no es el polígono oficial).
3. Rotación ignoraba historial y preferencias, y no comparaba con la estrategia del agricultor → corregido.
4. Pesos del optimizador sin justificación → se documentan como juicio a priori y se añade prueba de sensibilidad.
5. Sin resumen hídrico ni historial de alertas → agregados (alertas guardadas en SQLite).
6. Perfil de parcela incompleto (tipo de agricultura, disponibilidad de agua, historial, materia orgánica) → ampliado con migración no destructiva.
7. Trazabilidad parcial → cada fuente muestra tipo de dato (estimación/pronóstico), resolución y fecha de consulta.
8. Edición de parcelas inexistente → agregada.
9. Contornos autointersectantes no se detectaban → validación agregada.

## 4. Conservar / corregir
Conservar: algoritmos, motor de riesgos, caché con TTL, separación de capas. Corregir pendiente: validar servicios contra la red, ejecutar la UI y ajustar.

## 5. Funcionalidades faltantes
NDVI (Sentinel-2/HLS/MODIS), SMAP, GPM, suelo para México (ver FUENTES_DE_DATOS.md), asistente, pruebas de interfaz, reportes adicionales, modo demostración (la app no usa datos ficticios).

## 6. Riesgos técnicos y científicos
- Catálogo de cultivos con `verified=false`: valores aproximados, no validados con INIFAP/FAO.
- Umbrales operativos (helada, viento, lluvia, categorías de compatibilidad) son heurísticos y configurables.
- POWER tiene celdas de ~50 km: no representa una parcela pequeña.
- Calendarios de siembra de Chihuahua aproximados; pendientes de validación regional.
- La interfaz puede tener errores de integración no detectados.

## 7. Plan
Etapas 1–4 y 6–8 aplicadas a nivel de código y pruebas; Etapa 5 (datos) parcial: solo POWER y Open-Meteo; Etapas 9–10 parciales (alertas sí; asistente no). Siguiente: ejecutar localmente, validar APIs, integrar NDVI y SMAP.
