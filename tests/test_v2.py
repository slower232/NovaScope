import sqlite3
import pandas as pd
import pytest
from tests.synthetic import synthetic_daily
from tests.test_geospatial import square
from modules.geospatial.geometry import validate_chihuahua, validate_polygon_chihuahua, in_chihuahua
from database.migrations import ensure_columns
from algorithms.water_summary import water_summary
from algorithms.crop_rotation_optimizer import optimize_rotation, weight_sensitivity, compare_with_current, _build_eval
from modules.crop_rotation.crop_catalog import load_crops, load_weights, get_crop
from modules.recommendations.engine import recommend_crops, category, missing_information


def test_chihuahua_scope():
    assert in_chihuahua(28.63, -106.08)
    for lat, lon in [(19.4, -99.1), (36.1, -115.1), (32.5, -117.0)]:
        with pytest.raises(ValueError):
            validate_chihuahua(lat, lon)


def test_polygon_validation():
    assert validate_polygon_chihuahua(square(28.6, -106.1, 200))
    bowtie = {"type": "Polygon", "coordinates": [[[-106.1, 28.6], [-106.09, 28.61], [-106.09, 28.6], [-106.1, 28.61], [-106.1, 28.6]]]}
    with pytest.raises(ValueError):
        validate_polygon_chihuahua(bowtie)
    with pytest.raises(ValueError):
        validate_polygon_chihuahua(square(19.4, -99.1, 200))


def test_migration_adds_columns_without_losing_data():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE farms (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("INSERT INTO farms (name) VALUES ('vieja')")
    added = ensure_columns(c)
    assert "crop_history" in added and "preferences" in added
    assert c.execute("SELECT name FROM farms").fetchone()[0] == "vieja"
    assert ensure_columns(c) == []  # idempotente


def test_water_summary_states_and_honesty():
    d = synthetic_daily(20)
    s = water_summary(d, irrigated=False, spi_value=0.2)
    assert s["status"] in ("favorable", "limited", "possible_stress", "insufficient") and "Sin humedad de suelo" in s["basis"]
    assert water_summary(d.head(10), False)["status"] == "insufficient"
    assert water_summary(synthetic_daily(5), False)["status"] == "insufficient"  # historia corta -> no concluye


def test_water_summary_detects_drought():
    d = synthetic_daily(20)
    end = d["date"].max()
    d.loc[d["date"] > end - pd.Timedelta(days=60), "precip"] = 0.0
    # forzar un periodo reciente normalmente lluvioso
    shift = pd.Timestamp("2025-08-31") - end
    d["date"] = d["date"] + shift
    s = water_summary(d, False, spi_value=-1.4)
    assert s["status"] == "possible_stress"
    assert water_summary(d, True, spi_value=-1.4)["status"] == "limited"  # en riego no se afirma estrés


def test_recommendations_categories_and_limits():
    d = synthetic_daily(20); crops = load_crops()
    recs = recommend_crops(d, crops, {"irrigated": True, "soil_ph": 4.0, "crop_history": ["maiz"]})
    by = {r["crop_id"]: r for r in recs}
    assert by["manzana"]["category"] == "insufficient"
    assert any(k == "same_family_as_previous" for k, _ in by["sorgo"]["limitations"])
    assert any(k == "ph_out_of_range" for k, _ in by["frijol"]["limitations"])
    assert category(0.8) == "high" and category(0.5) == "moderate" and category(0.1) == "low" and category(None) == "insufficient"
    assert "soil_ph" in missing_information({})


def test_rotation_respects_history_and_exclusions():
    d = synthetic_daily(20); crops = load_crops(); w = load_weights()
    res = optimize_rotation(d, crops, w, True, 3, prev_family="Poaceae", exclude=["chile"])
    fam = {c["id"]: c["family"] for c in crops}
    for alt in res["top"]:
        assert fam[alt["sequence"][0]] != "Poaceae" and "chile" not in alt["sequence"]


def test_current_strategy_comparison_and_sensitivity():
    d = synthetic_daily(20); crops = load_crops(); w = load_weights()
    res = optimize_rotation(d, crops, w, True, 3)
    cmp_ = compare_with_current(d, crops, w, True, ["maiz", "maiz", "maiz"], res["top"])
    assert cmp_["current"]["family_repeats"] == 2 and cmp_["comparisons"]
    assert any(cmp_["comparisons"][0][k] for k in ("advantages", "disadvantages"))
    bad = compare_with_current(d, crops, w, True, ["maiz", "manzana", "maiz"], res["top"])
    assert bad["current"] is None and bad["not_evaluable"] == ["manzana"]
    sens = weight_sensitivity(d, crops, w, True, 3)
    assert 0 <= sens["agreement"] <= 1 and sens["n_weight_sets"] == 1 + len(w)
