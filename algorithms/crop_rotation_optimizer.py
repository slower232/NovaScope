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


def _build_eval(daily, crops, irrigated, exclude=None):
    ev = {}
    for c in crops:
        if exclude and c["id"] in exclude:
            continue
        e = evaluate_crop(daily, c, irrigated)
        if e is not None:
            ev[c["id"]] = (c, e)
    return ev


def score_sequence(seq, ev, weights, check_family=False):
    crit = {k: float(np.mean([ev[s][1]["criteria"][k] for s in seq])) for k in weights}
    legumes = sum(1 for a, b in zip(seq, seq[1:]) if ev[b][0]["nitrogen_fixing"] and not ev[a][0]["nitrogen_fixing"])
    score = sum(weights[k] * crit[k] for k in weights) + LEGUME_BONUS * legumes
    fams = [ev[s][0]["family"] for s in seq]
    return {"sequence": list(seq), "score": score, "criteria": crit, "legume_transitions": legumes,
            "family_repeats": sum(a == b for a, b in zip(fams, fams[1:])), "distinct_families": len(set(fams)),
            "uses_risk_proxy": any(ev[s][1]["risk_uses_proxy"] for s in seq),
            "details": [ev[s][1] for s in seq]}


def _valid_sequences(ev, horizon, prev_family=None):
    ids = list(ev)
    for seq in product(ids, repeat=horizon):
        fam = [ev[x][0]["family"] for x in seq]
        if any(a == b for a, b in zip(fam, fam[1:])):
            continue
        if prev_family and fam[0] == prev_family:
            continue
        yield seq


def optimize_rotation(daily, crops, weights, irrigated=False, horizon=3, top_k=3, min_criterion=0.0,
                      prev_family=None, exclude=None):
    """prev_family: familia del último cultivo (el primer cultivo del plan no puede repetirla).
    exclude: ids de cultivos que el agricultor prefiere no sembrar."""
    ev = _build_eval(daily, crops, irrigated, exclude)
    results = [score_sequence(seq, ev, weights) for seq in _valid_sequences(ev, horizon, prev_family)]
    results.sort(key=lambda r: -r["score"])
    return {"top": results[:top_k], "n_evaluated": len(results), "n_candidate_crops": len(ev),
            "excluded": [c["id"] for c in crops if c["id"] not in ev]}


def weight_sensitivity(daily, crops, weights, irrigated=False, horizon=3, prev_family=None, exclude=None):
    """¿Cambia la mejor secuencia si cambian los pesos? Prueba: pesos iguales y énfasis (60 %) en cada criterio.
    Devuelve la mejor secuencia por conjunto de pesos y la fracción de conjuntos que coincide con la secuencia base."""
    ev = _build_eval(daily, crops, irrigated, exclude)
    seqs = list(_valid_sequences(ev, horizon, prev_family))
    if not seqs:
        return None
    keys = list(weights)
    sets = {"base": weights, "equal": {k: 1 / len(keys) for k in keys}}
    for k in keys:
        sets[f"focus_{k}"] = {j: (0.6 if j == k else 0.4 / (len(keys) - 1)) for j in keys}
    best = {}
    for name, w in sets.items():
        best[name] = list(max(seqs, key=lambda q: score_sequence(q, ev, w)["score"]))
    same = sum(best[n] == best["base"] for n in best if n != "base")
    return {"best_by_weights": best, "agreement": same / (len(sets) - 1), "n_weight_sets": len(sets) - 1}


def compare_with_current(daily, crops, weights, irrigated, current_seq, alternatives, exclude=None):
    """Evalúa la estrategia actual del agricultor con los mismos criterios y la contrasta con las alternativas.
    No aplica restricción dura de familia a la estrategia actual: la reporta como limitación."""
    ev = _build_eval(daily, crops, irrigated)
    missing = [c for c in current_seq if c not in ev]
    if missing:
        return {"current": None, "not_evaluable": missing, "comparisons": []}
    cur = score_sequence(current_seq, ev, weights)
    comps = []
    for alt in alternatives:
        adv, dis = [], []
        for k in weights:
            d = alt["criteria"][k] - cur["criteria"][k]
            if d >= 0.05: adv.append((k, round(d, 2)))
            elif d <= -0.05: dis.append((k, round(d, 2)))
        if alt["distinct_families"] > cur["distinct_families"]: adv.append(("diversity", alt["distinct_families"] - cur["distinct_families"]))
        if alt["legume_transitions"] > cur["legume_transitions"]: adv.append(("legume", alt["legume_transitions"]))
        if alt["distinct_families"] < cur["distinct_families"]: dis.append(("diversity", alt["distinct_families"] - cur["distinct_families"]))
        comps.append({"sequence": alt["sequence"], "score_delta": alt["score"] - cur["score"], "advantages": adv, "disadvantages": dis})
    return {"current": cur, "not_evaluable": [], "comparisons": comps}
