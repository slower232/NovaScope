"""Simulador de escenarios: recalcula idoneidad y probabilidad empírica con la climatología
perturbada (ΔT, factor de precipitación, cultivo, fecha, riego). Solo procesos modelados:
temperatura y agua. No simula plagas, nutrientes ni manejo."""
from algorithms.crop_suitability import suitability_index
from algorithms.success_probability import cycle_completion_probability
from algorithms.water_balance import supply_requirement
from algorithms.crop_suitability import cycle_days, season_window
import numpy as np


def run_scenario(daily, crop, month, day=1, irrigated=False, dT=0.0, p_factor=1.0):
    si = suitability_index(daily, crop, month, day, irrigated, dT, p_factor)
    pr = cycle_completion_probability(daily, crop, month, day, irrigated, dT, p_factor)
    water = None
    if si is not None:
        n = cycle_days(crop)
        totals = []
        for y in sorted(set(daily["date"].dt.year)):
            w = season_window(daily, y, month, day, n, dT, p_factor)
            if w is not None:
                totals.append(float(w["precip"].sum()))
        if totals:
            req = (crop["water_mm_min"] + crop["water_mm_max"]) / 2
            water = supply_requirement(float(np.mean(totals)), req, irrigated)
    return {"suitability": si, "probability": pr, "water": water,
            "params": {"month": month, "day": day, "irrigated": irrigated, "dT": dT, "p_factor": p_factor}}


def compare(baseline: dict, scenario: dict) -> dict:
    def g(d, *path):
        for p in path:
            if d is None: return None
            d = d.get(p) if isinstance(d, dict) else None
        return d
    out = {}
    for name, path in {"suitability": ("suitability", "index"), "probability": ("probability", "probability"),
                       "water_deficit_mm": ("water", "deficit_mm")}.items():
        a, b = g(baseline, *path), g(scenario, *path)
        out[name] = {"baseline": a, "scenario": b, "delta": (b - a) if a is not None and b is not None else None}
    return out
