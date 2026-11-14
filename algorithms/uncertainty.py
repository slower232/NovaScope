"""Índice heurístico de CONFIANZA (D). No es un intervalo estadístico; es transparente y configurable.

confianza = f_cobertura · f_años · f_cultivo · f_resolución · f_horizonte
"""
POWER_RESOLUTION_FACTOR = 0.75   # celdas de ~50 km: no resuelven una parcela pequeña
UNVERIFIED_CROP_FACTOR = 0.7     # catálogo con verified=false
NO_LOCAL_DATA_FACTOR = 0.9       # sin suelo/rendimientos locales


def confidence(coverage: float, n_years: int, crop_verified: bool, horizon_years: float = 0.0,
               has_local_soil: bool = False, resolution_factor: float = POWER_RESOLUTION_FACTOR):
    f_cov = max(0.0, min(1.0, coverage))
    f_years = max(0.0, min(1.0, n_years / 20))
    f_crop = 1.0 if crop_verified else UNVERIFIED_CROP_FACTOR
    f_hor = max(0.5, 1.0 - 0.1 * horizon_years)
    f_loc = 1.0 if has_local_soil else NO_LOCAL_DATA_FACTOR
    score = f_cov * f_years * f_crop * f_hor * resolution_factor * f_loc
    label = "high" if score >= 0.6 else "medium" if score >= 0.35 else "low"
    return {"score": round(score, 3), "label": label,
            "components": {"coverage": f_cov, "years": f_years, "crop_data": f_crop,
                           "horizon": f_hor, "resolution": resolution_factor, "local_data": f_loc}}
