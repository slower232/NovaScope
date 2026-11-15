from tests.synthetic import synthetic_daily
from algorithms.crop_rotation_optimizer import optimize_rotation
from modules.crop_rotation.crop_catalog import load_crops, load_weights
from modules.simulation.simulator import run_scenario, compare
from modules.crop_rotation.crop_catalog import get_crop


def test_rotation_constraints_and_weights():
    d = synthetic_daily(20)
    crops = load_crops()
    res = optimize_rotation(d, crops, load_weights(), irrigated=True, horizon=3)
    fam = {c["id"]: c["family"] for c in crops}
    assert res["top"], "debe haber alternativas"
    for alt in res["top"]:
        s = alt["sequence"]
        assert all(fam[a] != fam[b] for a, b in zip(s, s[1:]))
    assert res["top"][0]["score"] >= res["top"][-1]["score"]
    assert "manzana" in res["excluded"] and "nogal" in res["excluded"]


def test_changing_weights_changes_ranking_inputs():
    d = synthetic_daily(20); crops = load_crops()
    w1 = load_weights(); w2 = {k: 0.0 for k in w1}; w2["soil_cover"] = 1.0
    a = optimize_rotation(d, crops, w1, True)["top"][0]["sequence"]
    b = optimize_rotation(d, crops, w2, True)["top"][0]["sequence"]
    cover = {c["id"]: c["soil_cover_class"] for c in crops}
    assert sum(cover[x] == "high" for x in b) >= sum(cover[x] == "high" for x in a)


def test_simulator_compare():
    d = synthetic_daily(20); maize = get_crop("maiz")
    base = run_scenario(d, maize, 6, 1, False)
    dry = run_scenario(d, maize, 6, 1, False, p_factor=0.8)
    c = compare(base, dry)
    assert c["suitability"]["delta"] < 0 and c["water_deficit_mm"]["delta"] > 0
