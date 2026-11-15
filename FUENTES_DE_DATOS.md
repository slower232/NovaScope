# Fuentes de datos
| Fuente | Estado | Tipo de dato | Resolución | Notas |
|---|---|---|---|---|
| NASA POWER, API diaria puntual (`https://power.larc.nasa.gov/api/temporal/daily/point`, comunidad AG) | Implementada, **no probada contra la red** | Estimación (reanálisis MERRA-2 + satélite; precipitación corregida) | ~0.5°×0.625° (~50 km) | `-999` = faltante. Latencia de días. Citar NASA/POWER. |
| Open-Meteo Forecast (`https://api.open-meteo.com/v1/forecast`) | Implementada, **no probada** | Pronóstico de modelos (no NASA) | Variable | CC BY 4.0: atribución obligatoria; uso gratuito no comercial. |
| OpenStreetMap (teselas del mapa) | En uso por Folium | Cartografía | — | © colaboradores de OpenStreetMap. |
| SMAP (NSIDC) | **No implementada** | Humedad superficial (no zona radicular) | 9–36 km | Requiere Earthdata. |
| GPM IMERG | **No implementada** | Precipitación estimada | ~0.1° | Early/Late/Final: documentar latencia. |
| Sentinel-2 / HLS (NDVI) | **No implementada** | Imágenes ópticas | 10–30 m | Requiere acceso real (Earthdata/STAC) y máscara de nubes. |
| Suelo para México | **No implementada**; no se usan USDA SSURGO/STATSGO2 | — | — | Candidatos a evaluar: SoilGrids (global, verificar disponibilidad de su API) e INEGI. No se asigna suelo a parcelas sin fuente verificada: solo datos del agricultor. |
Datos del agricultor (pH, textura, materia orgánica, historial) se etiquetan como "dato del agricultor".
