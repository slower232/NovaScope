import streamlit as st
from algorithms.crop_suitability import crop_ready
from algorithms.uncertainty import confidence
from database import repositories as repo
from modules.crop_rotation.crop_catalog import get_crop
from modules.simulation.simulator import compare, run_scenario
from ui.crop_visuals import crop_icon
from ui.context import CROPS, MONTHS, T, crop_name, lang


def render(user, farm, A):
    st.subheader(T("sim.title")); p = A["power"]
    if p is None: st.error(T("dash.no_power")); return
    annual = [c for c in CROPS if c["annual"] and crop_ready(c)]
    c1, c2, c3 = st.columns(3)
    cid = c1.selectbox(T("sim.crop"), [c["id"] for c in annual], format_func=lambda cid: f"{crop_icon(cid)} {crop_name(cid)}",
                       index=next((i for i, c in enumerate(annual) if c["id"] == farm.crop_id), 0))
    month = c2.selectbox(T("sim.month"), list(range(1, 13)), format_func=lambda m: MONTHS[lang()][m - 1], index=5)
    irr = c3.checkbox(T("sim.irr"), value=farm.irrigated)
    dT = st.slider(T("sim.dT"), -3.0, 5.0, 0.0, 0.5); dp = st.slider(T("sim.p"), -50, 50, 0, 5)
    if st.button(T("sim.run")):
        crop = get_crop(cid, CROPS)
        base = run_scenario(p, crop, month, 1, irr); scn = run_scenario(p, crop, month, 1, irr, dT, 1 + dp / 100)
        cmp_ = compare(base, scn); repo.save_simulation(farm.id, scn["params"], cmp_)
        cols = st.columns(3)
        for col, (k, lab) in zip(cols, [("suitability", "sim.suit"), ("probability", "sim.prob"), ("water_deficit_mm", "sim.def")]):
            b, s = cmp_[k]["baseline"], cmp_[k]["scenario"]
            fmt = (lambda v: f"{v * 100:.0f} %") if k == "probability" else (lambda v: f"{v:.2f}" if k == "suitability" else f"{v:.0f}")
            if b is None or s is None: col.metric(T(lab), "—"); continue
            col.metric(T(lab), fmt(s), delta=(fmt(s - b) if k != "probability" else f"{(s - b) * 100:+.0f} pp"),
                       delta_color="inverse" if k == "water_deficit_mm" else "normal")
        pr = scn["probability"]
        if pr.get("probability") is None: st.caption(T("sim.prob_na", m=", ".join(pr.get("missing", []))))
        else: st.caption(T("sim.ci", lo=f"{pr['ci95'][0] * 100:.0f}", hi=f"{pr['ci95'][1] * 100:.0f}", n=pr["n_years"]))
        cf = confidence(float(p[["tmean", "precip"]].notna().all(axis=1).mean()), p["date"].dt.year.nunique(), False, 0, farm.soil_ph is not None)
        st.caption(f"{T('conf')}: **{T('conf.' + cf['label'])}** ({cf['score']}) — {T('conf.note')}"); st.info(T("sim.disclaimer"))
