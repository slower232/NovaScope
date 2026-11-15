import streamlit as st
import plotly.graph_objects as go
from algorithms.crop_rotation_optimizer import compare_with_current, optimize_rotation, weight_sensitivity
from algorithms.crop_suitability import crop_ready
from algorithms.uncertainty import confidence
from database import repositories as repo
from modules.crop_rotation.crop_catalog import load_weights
from ui.context import CROPS, MONTHS, T, crop_name, farm_dict, lang
from ui.crop_visuals import crop_icon, crop_thumb
from ui.science import basis_expander


def _seq(alt, label):
    cols = st.columns(len(alt["sequence"]))
    for y, (col, cid, d) in enumerate(zip(cols, alt["sequence"], alt["details"]), 1):
        col.markdown(f"**{T('rot.year', n=y)}**<br>{crop_thumb(cid, 64, crop_name(cid))}<br>{crop_icon(cid)} {crop_name(cid)}<br><span class='fs-small'>{T('rot.sowing', m=MONTHS[lang()][d['sowing_month'] - 1])}</span>",
                     unsafe_allow_html=True)


def render(user, farm, A):
    st.subheader(T("rot.title")); p = A["power"]
    basis_expander("rot")
    if p is None: st.error(T("dash.no_power")); return
    fd = farm_dict(farm); by_id = {c["id"]: c for c in CROPS}
    prev_fam = by_id[farm.crop_id]["family"]
    st.caption(T("rot.prev_note", c=crop_name(farm.crop_id))); st.caption(T("rot.weights_note"))
    w0 = load_weights(); cols = st.columns(5); w = {}
    for col, k in zip(cols, w0): w[k] = col.slider(T("w." + k), 0.0, 1.0, float(round(w0[k], 2)), 0.05)
    horizon = st.slider(T("rot.horizon"), 3, 5, 3)
    st.markdown(f"**{T('rot.current')}** — {T('rot.current_help')}")
    ids = [c["id"] for c in CROPS]; ycols = st.columns(horizon); cur = []
    for i, col in enumerate(ycols):
        cur.append(col.selectbox(T("rot.year", n=i + 1), ids, index=ids.index(farm.crop_id), format_func=lambda cid: f"{crop_icon(cid)} {crop_name(cid)}", key=f"cur{i}"))
    preview = st.columns(horizon)  # pictures of the crops chosen above (selectboxes cannot show images)
    for col, cid in zip(preview, cur):
        col.markdown(crop_thumb(cid, 48, crop_name(cid)), unsafe_allow_html=True)
    if st.button(T("rot.run"), type="primary"):
        if sum(w.values()) == 0: st.error(T("rot.zero_weights")); return
        w = {k: v / sum(w.values()) for k, v in w.items()}
        with st.spinner(T("loading")):
            res = optimize_rotation(p, CROPS, w, farm.irrigated, horizon, prev_family=prev_fam, exclude=fd["exclude"])
            cmp_ = compare_with_current(p, CROPS, w, farm.irrigated, cur, res["top"])
            sens = weight_sensitivity(p, CROPS, w, farm.irrigated, horizon, prev_fam, fd["exclude"])
        repo.save_rotation(farm.id, w, {"top": res["top"], "current": cmp_["current"], "sensitivity": sens})
        if not res["top"]: st.warning(T("rot.none")); return
        st.caption(T("rot.eval", n=res["n_evaluated"], m=res["n_candidate_crops"]))
        # estrategia actual
        with st.container(border=True):
            st.markdown(f"**{T('rot.current')}**")
            if cmp_["current"] is None:
                st.warning(T("rot.not_evaluable", c=", ".join(crop_name(c) for c in cmp_["not_evaluable"])))
            else:
                _seq(cmp_["current"], "cur")
                st.caption(T("rot.score") + f": **{cmp_['current']['score']:.3f}** · " + T("rot.div", n=cmp_["current"]["distinct_families"]))
                if cmp_["current"]["family_repeats"]:
                    st.warning(T("rot.family_repeat", n=cmp_["current"]["family_repeats"]))
        for i, alt in enumerate(res["top"], 1):
            with st.container(border=True):
                st.markdown(f"**#{i}** — {T('rot.score')}: **{alt['score']:.3f}** · " + T("rot.div", n=alt["distinct_families"]))
                _seq(alt, i)
                st.plotly_chart(go.Figure(go.Bar(x=[T("w." + k) for k in alt["criteria"]], y=list(alt["criteria"].values()), marker_color="#43a047"))
                                .update_layout(height=210, margin=dict(t=10, b=10), yaxis_range=[0, 1]), use_container_width=True, key=f"rot{i}")
                if cmp_["current"] is not None and cmp_["comparisons"]:
                    c = cmp_["comparisons"][i - 1]
                    st.caption(T("rot.delta", d=c["score_delta"]))
                    a, b = st.columns(2)
                    a.markdown(f"**✅ {T('rot.adv_label')}**")
                    for k, _ in c["advantages"]: a.write("• " + T("rot.adv." + k))
                    b.markdown(f"**⚠️ {T('rot.dis_label')}**")
                    for k, _ in c["disadvantages"]: b.write("• " + T("rot.dis." + k))
                    if not c["advantages"] and not c["disadvantages"]: st.caption(T("rot.similar"))
                if alt["legume_transitions"]: st.caption("🌱 " + T("rot.legume"))
                if alt["uses_risk_proxy"]: st.caption("ℹ️ " + T("rot.proxy"))
        if sens: st.info(T("rot.sens", a=f"{sens['agreement'] * 100:.0f}", n=sens["n_weight_sets"]))
        if res["excluded"]: st.caption(T("rot.excluded", c=", ".join(crop_name(c) for c in res["excluded"])))
        cov = float(p[["tmean", "precip"]].notna().all(axis=1).mean())
        cf = confidence(cov, p["date"].dt.year.nunique(), False, 0, farm.soil_ph is not None)
        st.caption(f"{T('conf')}: **{T('conf.' + cf['label'])}** ({cf['score']}) — {T('conf.note')}")
        st.warning(T("rot.disclaimer"))
