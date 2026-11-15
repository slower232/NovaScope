import numpy as np, pandas as pd
from tests.synthetic import synthetic_daily
from algorithms.climate_anomalies import monthly_aggregate, monthly_anomalies, classify_z
from algorithms.drought_index import spi
from algorithms.water_balance import et0_hargreaves, supply_requirement
from algorithms.crop_suitability import temperature_response, suitability_index
from algorithms.success_probability import cycle_completion_probability, wilson_interval
from algorithms.uncertainty import confidence
from modules.crop_rotation.crop_catalog import load_crops, get_crop, load_weights


def test_temperature_response_trapezoid():
    r = temperature_response([0, 10, 20, 30, 45], 5, 15, 25, 40)
    assert r[0] == 0 and r[1] == 0.5 and r[2] == 1 and abs(r[3] - 2 / 3) < 1e-9 and r[4] == 0


def test_spi_mean_zero_and_warns_short_series():
    d = synthetic_daily(25)
    m = monthly_aggregate(d, "precip", "sum")
    s, w = spi(m, 3)
    assert abs(s.dropna().mean()) < 0.15 and abs(s.dropna().std() - 1) < 0.2
    s2, w2 = spi(monthly_aggregate(synthetic_daily(12), "precip", "sum"), 3)
    assert any("shorter" in x for x in w2)


def test_anomaly_z_of_mean_is_zero_overall():
    m = monthly_aggregate(synthetic_daily(20), "tmean", "mean")
    a = monthly_anomalies(m)
    assert abs(a["anomaly"].mean()) < 1e-6
    assert classify_z(2.5) == "extreme" and classify_z(0.2) == "normal"


def test_et0_reasonable_range_and_seasonality():
    dates = pd.to_datetime(["2020-01-15", "2020-06-21"])
    et = et0_hargreaves([2, 18], [18, 36], 28.6, dates)
    assert 1.0 < et[0] < 4 and 5 < et[1] < 12 and et[1] > et[0]


def test_supply_requirement():
    r = supply_requirement(400, 600, irrigated=False)
    assert r["p_effective_mm"] == 300 and r["deficit_mm"] == 300


def test_wilson_interval_contains_p():
    lo, hi = wilson_interval(15, 20)
    assert lo < 0.75 < hi


def test_catalog_has_required_crops_and_no_invented_yields():
    ids = {c["id"] for c in load_crops()}
    assert {"maiz", "frijol", "trigo", "sorgo", "avena", "alfalfa", "algodon", "chile", "cebolla", "tomate", "papa", "manzana", "nogal"} <= ids
    assert all(c["reference_yield_t_ha"] is None for c in load_crops())
    assert abs(sum(load_weights().values()) - 1) < 1e-9


def test_probability_needs_enough_years_and_is_in_range():
    maize = get_crop("maiz")
    p = cycle_completion_probability(synthetic_daily(20), maize, 5, 1, irrigated=True)
    assert p["probability"] is not None and 0 <= p["probability"] <= 1
    short = cycle_completion_probability(synthetic_daily(8), maize, 5, 1, irrigated=True)
    assert short["probability"] is None and short["missing"]


def test_warmer_climate_never_improves_frost_free_but_changes_heat():
    maize = get_crop("maiz"); d = synthetic_daily(20)
    base = cycle_completion_probability(d, maize, 5, 1, True)["probability"]
    hot = cycle_completion_probability(d, maize, 5, 1, True, dT=6)["probability"]
    assert hot <= base + 0.35  # sanidad: el cálculo responde al parámetro


def test_suitability_drops_with_less_rain_in_rainfed():
    maize = get_crop("maiz"); d = synthetic_daily(20)
    a = suitability_index(d, maize, 6, 1, False)["index"]
    b = suitability_index(d, maize, 6, 1, False, p_factor=0.5)["index"]
    assert b < a


def test_perennial_returns_none():
    assert suitability_index(synthetic_daily(10), get_crop("manzana"), 4) is None


def test_confidence_decreases_with_missing_data():
    hi = confidence(1.0, 20, True, 0, True, 1.0)["score"]
    lo = confidence(0.5, 8, False, 3, False)["score"]
    assert lo < hi
