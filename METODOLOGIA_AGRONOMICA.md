# Metodología
**Catálogo** (`data/crops/crops.json`): parámetros generales tipo FAO EcoCrop/CropWat; `verified=false` en todos; `null` = dato no disponible. Ventanas de siembra de Chihuahua aproximadas, pendientes de validar con INIFAP.

**Idoneidad (C):** respuesta trapezoidal a temperatura media diaria durante el ciclo × cobertura de agua (P efectiva = 0.75·P / requerimiento medio; con riego se supone agua suficiente); SI = √(T·W), promedio sobre años históricos. **No es probabilidad.**

**Categorías de compatibilidad:** alta ≥ 0.70; moderada ≥ 0.45; baja < 0.45; "información insuficiente" si no se puede evaluar (perenne, parámetros faltantes, sin ventana de siembra o pocos años). Umbrales heurísticos (no calibrados); se ajustan en `config/constants.py`. pH fuera de rango, repetición de familia y catálogo sin validar se muestran como limitaciones, sin alterar el índice.

**Probabilidad empírica (A):** fracción de años históricos que cumplen: sin helada bajo umbral operativo, ≤10 % de días sobre la Tmax del cultivo y (temporal) P efectiva ≥ 50 % del mínimo; IC de Wilson 95 %; mínimo 15 años. No pronostica los próximos años ni estima rendimiento.

**Rotación:** búsqueda exhaustiva de secuencias de 3–5 años. Restricciones duras: no repetir familia en ciclos consecutivos; el primer cultivo no repite la familia del cultivo actual; respeta cultivos excluidos por el agricultor.
Criterios (0–1): compatibilidad climática, agua, cobertura del suelo (clase cualitativa del catálogo), potencial relativo (= idoneidad; aproximación, no rendimiento) y menor riesgo climático (1 − tasa de fallo histórica). Bonificación +0.03 por transición a leguminosa (beneficio *potencial*, no medido; no se asume cantidad de N fijado).
**Pesos:** 0.25 clima, 0.25 agua, 0.15 cobertura, 0.15 potencial, 0.20 riesgo. Son juicio a priori, **no derivados de datos**. Por eso se incluye una **prueba de sensibilidad** (pesos iguales y énfasis del 60 % en cada criterio): se reporta en qué fracción de variaciones se mantiene la mejor secuencia. Pendiente: calibrar con asesores agrícolas.
**Comparación:** la estrategia actual del agricultor se evalúa con los mismos criterios (sin restricción dura de familia; la repetición se reporta). Ventajas/desventajas = diferencias ≥ 0.05 en criterios, más diversidad de familias y leguminosas.

**Resumen hídrico:** ratio = lluvia de 30 días / media histórica del mismo periodo (≥10 años). Favorable: ratio ≥ 0.8 y SPI-3 ≥ −0.5; posible estrés: ratio < 0.5 o SPI ≤ −1 (en riego se reporta "limitada"); si hay <10 años, base < 10 mm o huecos: "información insuficiente"/"limitada". Sin humedad de suelo; no calcula necesidades de riego.

**Riesgos:** SPI-3 (McKee), P/ET0 de 30 días (Hargreaves), heladas por sensibilidad del cultivo, ola de calor (≥3 días sobre P90 mensual), lluvia intensa, indicador indirecto de inundación, viento. El riesgo general es el máximo de los individuales. Cada alerta se etiqueta como pronóstico o estimación.

**Limitaciones:** clima histórico ≠ pronóstico; resolución ~50 km; catálogo sin validar; sin suelo medido.
