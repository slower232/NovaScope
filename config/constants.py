"""Constantes. Los umbrales operativos son CONFIGURABLES y deben validarse localmente."""

POWER_PARAMS = {
    "T2M": "tmean",
    "T2M_MAX": "tmax",
    "T2M_MIN": "tmin",
    "PRECTOTCORR": "precip",
    "ALLSKY_SFC_SW_DWN": "solar",
    "RH2M": "rh",
    "WS2M": "wind",
}
POWER_FILL_VALUE = -999.0
POWER_RESOLUTION = "~0.5° x 0.625° (temperatura, MERRA-2); precipitación corregida con IMERG"

LEVELS = ("green", "yellow", "red", "gray")
SEVERITY = {"gray": -1, "green": 0, "yellow": 1, "red": 2}

# Umbrales de helada por sensibilidad del cultivo (°C de temperatura mínima diaria).
# Valores operativos genéricos; NO son umbrales fisiológicos por especie. Validar con INIFAP.
FROST_THRESHOLDS = {
    "high": {"yellow": 2.0, "red": 0.0},
    "medium": {"yellow": 0.0, "red": -2.0},
    "low": {"yellow": -2.0, "red": -5.0},
}
# Clasificación SPI de McKee et al. (1993)
SPI_YELLOW = -1.0
SPI_RED = -1.5
# Precipitación intensa (mm/día) y acumulado 3 días (indicador indirecto de inundación)
HEAVY_RAIN_YELLOW = 25.0
HEAVY_RAIN_RED = 50.0
FLOOD_3D_YELLOW = 50.0
FLOOD_3D_RED = 75.0
# Viento máximo diario a 10 m (km/h)
WIND_YELLOW = 40.0
WIND_RED = 60.0
# Razón P/ET0 de 30 días para estrés hídrico en temporal
WATER_STRESS_YELLOW = 0.7
WATER_STRESS_RED = 0.4
HEATWAVE_PERCENTILE = 90
HEATWAVE_MIN_DAYS_YELLOW = 3
HEATWAVE_MIN_DAYS_RED = 5
# Fracción máxima de días del ciclo con Tmax > Tmax del cultivo para "ciclo completado"
MAX_HOT_DAY_FRACTION = 0.10
# Factor de precipitación efectiva (supuesto; configurable)
EFFECTIVE_RAIN_FACTOR = 0.75
COVER_SCORE = {"low": 0.3, "medium": 0.6, "high": 0.9}
MIN_YEARS_PROBABILITY = 15
MIN_YEARS_SPI = 20
