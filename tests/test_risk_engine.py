import pandas as pd
from modules.risk_engine.engine import evaluate_risks, overall_level
from modules.crop_rotation.crop_catalog import get_crop


def fc(tmax, tmin, precip, wind):
    n = len(tmax)
    return pd.DataFrame({"date": pd.date_range("2026-07-01", periods=n), "tmax": tmax, "tmin": tmin,
                         "precip": precip, "wind_max": wind})


def by_key(res): return {r.key: r for r in res}


def test_no_data_is_gray_not_green():
    res = by_key(evaluate_risks(get_crop("maiz"), None, None, None, None, False, 28.6))
    assert all(r.level == "gray" for r in res.values())
    assert overall_level(list(res.values()))["level"] == "gray"


def test_frost_depends_on_crop_sensitivity():
    f = fc([20] * 3, [-1.0] * 3, [0] * 3, [10] * 3)
    maize = by_key(evaluate_risks(get_crop("maiz"), f, None, None, None, True, 28.6))["frost"]   # alta
    wheat = by_key(evaluate_risks(get_crop("trigo"), f, None, None, None, True, 28.6))["frost"]  # baja
    assert maize.level == "red" and wheat.level == "green"


def test_critical_risk_not_hidden_by_average():
    f = fc([25] * 7, [10] * 7, [0, 0, 80, 0, 0, 0, 0], [10] * 7)
    res = evaluate_risks(get_crop("maiz"), f, None, -0.2, {7: 30}, True, 28.6)
    o = overall_level(res)
    assert o["level"] == "red" and "heavy_rain" in o["critical"]


def test_spi_thresholds():
    r = lambda v: by_key(evaluate_risks(get_crop("maiz"), None, None, v, None, False, 28.6))["meteorological_drought"].level
    assert r(-1.6) == "red" and r(-1.1) == "yellow" and r(0.3) == "green"
