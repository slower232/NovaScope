"""Optimizador de rotación: búsqueda combinatoria EXHAUSTIVA (transparente y reproducible).

Para cada secuencia de N cultivos anuales (N=3..5) se calcula:
  score = Σ_k w_k · media_años(criterio_k)  + bonus_leguminosa
Criterios (todos 0-1, mayor = mejor):
  climate      = componente de temperatura del índice de idoneidad
  water        = cobertura de requerimiento hídrico (temporal) o 1.0 (riego, supuesto)
  soil_cover   = clase cualitativa de cobertura (catálogo) -> COVER_SCORE
  yield_proxy  = índice de idoneidad (PROXY relativo; no es rendimiento en t/ha)
  climate_risk = 1 − tasa de fallo histórica (usa probabilidad empírica; si no existe, se usa idoneidad y se advierte)
Restricciones duras: (1) no repetir familia botánica en años consecutivos; (2) cultivos con parámetros completos.
Bonus: +BONUS si una leguminosa (fijadora de N) sigue a un cultivo de otra familia (beneficio POTENCIAL, no medido).
"""
from itertools import product
import numpy as np

from algorithms.crop_suitability import crop_ready, suitability_index
from algorithms.success_probability import cycle_completion_probability
from config.constants import COVER_SCORE

LEGUME_BONUS = 0.03

def default_sowing_month(crop: dict, irrigated: bool):
    months = crop["sowing_months_irrigated"] if irrigated else crop["sowing_months_rainfed"]
    return months[0] if months else None

def evaluate_crop(daily, crop, irrigated):
    """Evalúa un cultivo con su primera ventana de siembra documentada. None si no aplica."""
    m = default_sowing_month(crop, irrigated)
    if m is None or not crop["annual"] or not crop_ready(crop):
        return None
    si = suitability_index(daily, crop, m, 1, irrigated)
    if si is None:
        return None
    pr = cycle_completion_probability(daily, crop, m, 1, irrigated)
    p = pr.get("probability")
    risk_score = p if p is not None else si["index"]
    return {"crop_id": crop["id"], "sowing_month": m, "si": si, "prob": pr,
            "criteria": {"climate": si["temperature_score"], "water": si["water_score"],
                         "soil_cover": COVER_SCORE[crop["soil_cover_class"]],
                         "yield_proxy": si["index"], "climate_risk": risk_score},
            "risk_uses_proxy": p is None}


def optimize_rotation(daily, crops, weights, irrigated=False, horizon=3, top_k=3, min_criterion=0.0):
    ev = {}
    for c in crops:
        e = evaluate_crop(daily, c, irrigated)
        if e is not None:
            ev[c["id"]] = (c, e)
    ids = list(ev)
    results = []
    for seq in product(ids, repeat=horizon):
        if any(ev[a][0]["family"] == ev[b][0]["family"] for a, b in zip(seq, seq[1:])):
            continue
        crit = {k: float(np.mean([ev[s][1]["criteria"][k] for s in seq])) for k in weights}
        score = sum(weights[k] * crit[k] for k in weights)
        legumes = sum(1 for a, b in zip(seq, seq[1:]) if ev[b][0]["nitrogen_fixing"] and not ev[a][0]["nitrogen_fixing"])
        score += LEGUME_BONUS * legumes
        results.append({"sequence": list(seq), "score": score, "criteria": crit, "legume_transitions": legumes,
                        "uses_risk_proxy": any(ev[s][1]["risk_uses_proxy"] for s in seq),
                        "details": [ev[s][1] for s in seq]})
    results.sort(key=lambda r: -r["score"])
    return {"top": results[:top_k], "n_evaluated": len(results), "n_candidate_crops": len(ids),
            "excluded": [c["id"] for c in crops if c["id"] not in ids]}
