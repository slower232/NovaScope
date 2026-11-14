# Algoritmos
- **ET0**: Hargreaves-Samani (FAO-56 ec. 52) con Ra de FAO-56 ec. 21.
- **SPI**: precipitación acumulada (escala 3), ajuste gamma por mes calendario, mezcla con ceros, transformación normal (McKee 1993). Mínimo 20 años o se advierte.
- **Idoneidad (C)**: respuesta trapezoidal a temperatura media diaria durante el ciclo × cobertura de agua efectiva (P·0.75 / requerimiento medio); SI = √(T·W), promedio sobre años históricos. Con riego se supone agua suficiente.
- **Probabilidad (A)**: fracción de años históricos que cumplen: sin helada bajo umbral operativo, ≤10 % de días con Tmax > Tmax del cultivo, y (temporal) P efectiva ≥ 50 % del mínimo. IC de Wilson 95 %. Requiere ≥15 años.
- **Confianza (D)**: producto heurístico de cobertura, años, verificación del catálogo, horizonte, resolución y datos locales.
- **Rotación**: búsqueda exhaustiva de secuencias; restricción dura de no repetir familia en años consecutivos; score = Σ pesos·criterios + 0.03 por transición a leguminosa. Pesos en `data/reference/rotation_weights.json`.
- **Riesgos**: umbrales en `config/constants.py`; el riesgo general es el máximo de los individuales.
