# 🛰️ NovaScope — NASA Space Apps Challenge 2026
Sistema de apoyo a decisiones agrícolas (Streamlit + SQLite), con navegación agrupada en Overview, Recommendations y Environmental conditions. Administra parcelas, agua y alertas desde Overview; el plan de rotación está dentro de Recommendations y Reports se abre desde el icono del pie de página. que combina **NASA POWER** (clima histórico) y **Open-Meteo** (pronóstico) con un catálogo de cultivos, un motor de riesgos de 8 categorías, un optimizador de rotaciones, un modelo de probabilidad empírica y un simulador de escenarios. Cobertura de esta versión: **solo Chihuahua, México**. Idioma inicial: inglés (también español).

## Estado (v2)
Detalle completo en `AUDITORIA_PROYECTO.md`. Resumen:
- ✅ Probado (datos sintéticos solo en pruebas): algoritmos, riesgos, recomendaciones, resumen hídrico, rotación + comparación + sensibilidad, geometría/alcance Chihuahua, migración, PDF.
- ⚠️ Escrito pero **sin ejecutar**: interfaz Streamlit/Folium, base SQLAlchemy y login, conexiones reales a NASA POWER y Open-Meteo. Ejecuta `python -m scripts.validate_connections` y `python -m pytest` en tu equipo.
- ❌ No implementado: SMAP, GPM, NDVI (Sentinel-2/HLS), ECOSTRESS, ERA5, suelo para México, asistente explicativo.
- Catálogo de cultivos y umbrales: aproximaciones sin validar con INIFAP/FAO (`verified=false`).
Documentos: `AUDITORIA_PROYECTO.md`, `ARQUITECTURA.md`, `FUENTES_DE_DATOS.md`, `METODOLOGIA_AGRONOMICA.md`, `CHANGELOG.md`.

## Instalación
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.validate_connections   # prueba NASA POWER y Open-Meteo
streamlit run app.py
```
Primera ejecución: la app pide crear el administrador. Pruebas: `python -m pytest`.

## Imágenes de cultivos y página de fuentes
- Coloca **un PNG por cultivo** en `assets/crops/` con el id del catálogo: `assets/crops/maiz.png`, `frijol.png`, etc. (lista completa en `assets/crops/README.md`). Si falta un PNG, la interfaz muestra un icono de respaldo y no falla. `python -m scripts.check_crop_images` indica qué imágenes faltan.
- Las imágenes se usan en Overview (tarjeta de la parcela, mapa), Mis parcelas, Recommendations y Rotation.
- Los iconos ℹ️ y los paneles «¿Cómo se calcula?» (Recommendations, Rotation, Alerts, Water, Environmental conditions) explican datos, método, significado y límites bajo demanda, y distinguen estimación, pronóstico, modelo y dato del agricultor. Textos en `ui/translations/` (claves `sci.*`).
- El botón **Sources & scientific basis** al pie abre `ui/pages/sources.py`, con las fuentes realmente usadas y enlaces a sus páginas oficiales (se abren en pestaña nueva).

## Estructura
`algorithms/` (modelos), `modules/` (riesgos, rotación, simulación, geometría, PDF), `services/` (APIs + caché), `database/`, `authentication/`, `ui/translations/`, `data/` (catálogo y pesos editables), `tests/`.

## Fuentes y licencias
NASA POWER (datos abiertos, citar a NASA/POWER); Open-Meteo (CC BY 4.0, atribución obligatoria, uso gratuito no comercial); OpenStreetMap (© colaboradores).

## Limitaciones
POWER tiene celdas de ~50 km; no representa mediciones dentro de una parcela. El SPI requiere ≥20 años. La probabilidad es empírica (años históricos) y no pronostica los próximos años. Los índices no sustituyen asesoría agronómica.

## Solución de problemas
**`OpenBLAS error: Memory allocation still failed after 10 retries`** — NumPy/OpenBLAS no logra reservar memoria para sus hilos (muchos núcleos, poca RAM libre o Python de 32 bits). Lanza con `python run.py` o define antes `OPENBLAS_NUM_THREADS=1`
(PowerShell: `$env:OPENBLAS_NUM_THREADS=1; streamlit run app.py` · CMD: `set OPENBLAS_NUM_THREADS=1` · Linux/macOS: `OPENBLAS_NUM_THREADS=1 streamlit run app.py`). Comprueba que Python sea de 64 bits.
