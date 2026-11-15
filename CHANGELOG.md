# Changelog
## v2.1 (imágenes y base científica)
- Imágenes por cultivo (`assets/crops/<id>.png`) con respaldo de icono; usadas en Overview, parcelas, recomendaciones y rotación. Script `scripts/check_crop_images.py`.
- Ayudas bajo demanda (`ui/science.py`): popovers ℹ️ y paneles «¿Cómo se calcula?» con datos, método, significado y límites; etiquetas observación / estimación / pronóstico / modelo / dato del agricultor.
- Nueva página «Sources & scientific basis» (`ui/pages/sources.py`) accesible desde el pie, con NASA POWER, Open-Meteo, OpenStreetMap y los métodos referenciados (SPI, Hargreaves–Samani, FAO).
- Sin cambios en algoritmos, umbrales, catálogo ni esquema de base de datos. Mis parcelas ahora muestra una tarjeta por parcela y un expansor «Editar».
- Pruebas nuevas: `tests/test_ui_assets_and_sources.py`.
## v2 (segundo prompt maestro)
- Alcance limitado a Chihuahua (validación de pin y polígono; polígonos autointersectantes rechazados).
- Dashboard Canvas con 6 tarjetas navegables y botón "Agregar nueva parcela"; idioma inicial español.
- `app.py` dividido en `ui/pages/*` y `ui/context.py`.
- Perfil de parcela ampliado (tipo de agricultura, agua, historial, materia orgánica, preferencias); edición de parcelas; migración no destructiva.
- Módulo de recomendaciones con categorías de compatibilidad y lista de información faltante.
- Resumen hídrico simple (`algorithms/water_summary.py`).
- Rotación: historial, exclusiones, comparación con estrategia actual, ventajas/desventajas, prueba de sensibilidad de pesos.
- Alertas persistidas, etiquetadas como pronóstico/estimación; trazabilidad de fuentes en la interfaz.
- Eliminados `docs/algorithms.md` y `docs/data_sources.md`: reemplazados por `METODOLOGIA_AGRONOMICA.md` y `FUENTES_DE_DATOS.md`.
- Pruebas nuevas: `test_v2.py`, `test_translations.py` (31 pasan; 2 módulos se omiten sin SQLAlchemy).
## v1
- Primera versión: algoritmos, motor de riesgos, POWER/Open-Meteo, auth, PDF.
