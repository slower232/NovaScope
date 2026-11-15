"""Recomendaciones de cultivos con categorías de compatibilidad (NO son probabilidades).

Categoría a partir del índice de idoneidad (clima+agua sobre años históricos):
  alta >= COMPAT_HIGH, moderada >= COMPAT_MODERATE, baja en otro caso, 'insufficient' si no se puede evaluar.
Ajustes que NO alteran el índice, solo agregan limitaciones explícitas: pH fuera de rango (si el agricultor lo dio),
repetición de la familia del cultivo anterior y falta de ventana de siembra documentada para Chihuahua.
"""
from algorithms.crop_rotation_optimizer import default_sowing_month, evaluate_crop
from algorithms.crop_suitability import crop_ready
from config.constants import COMPAT_HIGH, COMPAT_MODERATE


def category(si_index):
    if si_index is None:
        return "insufficient"
    return "high" if si_index >= COMPAT_HIGH else "moderate" if si_index >= COMPAT_MODERATE else "low"


def missing_information(farm: dict) -> list[str]:
    m = []
    if farm.get("soil_ph") is None: m.append("soil_ph")
    if not farm.get("soil_texture"): m.append("soil_texture")
    if farm.get("organic_matter") is None: m.append("organic_matter")
    if not farm.get("crop_history"): m.append("crop_history")
    if not farm.get("water_availability"): m.append("water_availability")
    return m


def recommend_crops(daily, crops, farm: dict, exclude=None):
    """farm: dict con irrigated, soil_ph, crop_history (lista, más reciente primero)."""
    irrigated = bool(farm.get("irrigated"))
    history = farm.get("crop_history") or []
    by_id = {c["id"]: c for c in crops}
    prev_family = by_id[history[0]]["family"] if history and history[0] in by_id else None
    out = []
    for c in crops:
        if exclude and c["id"] in exclude:
            continue
        item = {"crop_id": c["id"], "advantages": [], "limitations": [], "requirements": {}, "category": "insufficient",
                "index": None, "missing": []}
        if not c["annual"]:
            item["limitations"].append(("perennial_not_modeled", {}))
        elif not crop_ready(c):
            item["limitations"].append(("crop_params_missing", {}))
        elif default_sowing_month(c, irrigated) is None:
            item["limitations"].append(("no_sowing_window", {"mode": "irrigated" if irrigated else "rainfed"}))
        else:
            e = evaluate_crop(daily, c, irrigated)
            if e is None:
                item["limitations"].append(("not_enough_climate_years", {}))
            else:
                si = e["si"]; item["index"] = round(si["index"], 2); item["category"] = category(si["index"])
                item["sowing_month"] = e["sowing_month"]; item["n_years"] = si["n_years"]
                item["requirements"] = {"water_mm": (c["water_mm_min"], c["water_mm_max"]),
                                        "cycle_days": (c["cycle_days_min"], c["cycle_days_max"]),
                                        "t_opt_c": (c["t_opt_low_c"], c["t_opt_high_c"])}
                (item["advantages"] if si["temperature_score"] >= 0.7 else item["limitations"]).append(
                    ("temperature_ok" if si["temperature_score"] >= 0.7 else "temperature_limiting", {"score": round(si["temperature_score"], 2)}))
                if irrigated:
                    item["advantages"].append(("water_assumed_irrigation", {}))
                else:
                    (item["advantages"] if si["water_score"] >= 0.7 else item["limitations"]).append(
                        ("rain_covers_demand" if si["water_score"] >= 0.7 else "rain_short", {"score": round(si["water_score"], 2)}))
                if c["nitrogen_fixing"]:
                    item["advantages"].append(("legume_potential", {}))
        ph = farm.get("soil_ph")
        if ph is not None and c.get("ph_min") is not None:
            if c["ph_min"] <= ph <= c["ph_max"]:
                item["advantages"].append(("ph_in_range", {"ph": ph}))
            else:
                item["limitations"].append(("ph_out_of_range", {"ph": ph, "min": c["ph_min"], "max": c["ph_max"]}))
        elif ph is None:
            item["missing"].append("soil_ph")
        if prev_family and c["family"] == prev_family:
            item["limitations"].append(("same_family_as_previous", {}))
        elif prev_family:
            item["advantages"].append(("family_change", {}))
        if not c.get("verified"):
            item["limitations"].append(("catalog_unverified", {}))
        out.append(item)
    order = {"high": 0, "moderate": 1, "low": 2, "insufficient": 3}
    out.sort(key=lambda x: (order[x["category"]], -(x["index"] or 0)))
    return out
