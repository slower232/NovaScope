# 🌾 Field Shift — NASA Space Apps Challenge 2026
Sistema de apoyo a decisiones agrícolas (Streamlit + SQLite) que combina **NASA POWER** (clima histórico) y **Open-Meteo** (pronóstico) con un catálogo de cultivos, un motor de riesgos de 8 categorías, un optimizador de rotaciones, un modelo de probabilidad empírica y un simulador de escenarios. Caso de estudio: Chihuahua, México.

## Estado de esta entrega (honesto)
| Componente | Estado |
|---|---|
| Usuarios, roles, hash scrypt, admin inicial sin credenciales por defecto | ✅ implementado (probado en tests; requiere SQLAlchemy) |
| Parcelas con pin/polígono (Folium Draw), área calculada | ✅ implementado (**no ejecutado aún en este entorno**) |
| NASA POWER diario + caché SQLite + reintentos + datos viejos marcados | ✅ implementado (**sin probar contra la red real**: ejecuta `scripts/validate_connections.py`) |
| Open-Meteo pronóstico 7 días | ✅ implementado (mismo aviso) |
| Motor de riesgos (8 categorías, semáforo, gris = sin datos) | ✅ probado |
| SPI-3, anomalías, ET0 Hargreaves, balance simple | ✅ probado con series sintéticas |
| Idoneidad (C), probabilidad empírica (A) + IC Wilson, confianza (D) | ✅ probado |
| Optimizador de rotación (búsqueda exhaustiva, pesos en JSON) | ✅ probado |
| Simulador y comparación base vs escenario | ✅ probado |
| PDF de diagnóstico | ✅ generado y verificado |
| Español / Inglés centralizado | ✅ |
| **SMAP, GPM IMERG, HLS/MODIS (NDVI), ECOSTRESS, GRACE, SoilGrids** | ❌ **pendiente** (requieren Earthdata/rasters). No hay stubs falsos. |
| Rendimiento esperado (B) | ❌ no se calcula: no hay datos de rendimiento validados |
| Reportes 2–4, comunidad, asistente IA, modo demostración | ❌ pendiente |

Los valores del catálogo (`data/crops/crops.json`) son aproximaciones generales tipo FAO EcoCrop/CropWat con `verified=false`; **debes validarlos con INIFAP/FAO** y citar la fuente exacta. Los umbrales operativos (heladas, viento, lluvia) están en `config/constants.py` y son configurables.

## Instalación
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.validate_connections   # prueba NASA POWER y Open-Meteo
streamlit run app.py
```
Primera ejecución: la app pide crear el administrador. Pruebas: `python -m pytest`.

## Estructura
`algorithms/` (modelos), `modules/` (riesgos, rotación, simulación, geometría, PDF), `services/` (APIs + caché), `database/`, `authentication/`, `ui/translations/`, `data/` (catálogo y pesos editables), `tests/`.

## Fuentes y licencias
NASA POWER (datos abiertos, citar a NASA/POWER); Open-Meteo (CC BY 4.0, atribución obligatoria, uso gratuito no comercial); OpenStreetMap (© colaboradores).

## Limitaciones
POWER tiene celdas de ~50 km; no representa mediciones dentro de una parcela. El SPI requiere ≥20 años. La probabilidad es empírica (años históricos) y no pronostica los próximos años. Los índices no sustituyen asesoría agronómica.
