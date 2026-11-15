import streamlit as st
from ui.pages.dashboard import _water_tank
from ui.context import T, data_status, trace_caption
from ui.science import basis_expander

WICON = {"favorable": "🟢", "limited": "🟡", "possible_stress": "🔴", "insufficient": "⚪"}


def render(user, farm, A):
    w = A["water"]
    st.subheader(T("water.title")); data_status(A["pmeta"])
    basis_expander("water")
    with st.container(border=True):
        tank, summary = st.columns([1, 4], vertical_alignment="center")
        with tank: st.markdown(_water_tank(w["status"]), unsafe_allow_html=True)
        with summary:
            st.markdown(f"## {WICON[w['status']]} {T('water.status.' + w['status'])}")
            st.caption(T("water.visual_only"))
    if w.get("reason") not in (None, "ok"):
        with st.container(border=True): st.info(T("water.reason." + w["reason"]))
    if w.get("p30_mm") is not None:
        with st.container(border=True):
            st.markdown(f"**{T('water.why')}**")
            base = w.get("baseline_mm")
            st.write("• " + T("water.p30", p=w["p30_mm"], b=base if base is not None else "—"))
            st.write("• " + T("water.p7", p=w["p7_mm"]))
            if w.get("tmean_30d") is not None: st.write("• " + T("water.t", t=w["tmean_30d"]))
            if w.get("spi3") is not None: st.write("• " + T("water.spi", s=w["spi3"]))
            st.caption(T("water.through", d=w["data_through"]))
    if w["status"] in ("limited", "possible_stress"):
        with st.container(border=True):
            st.markdown(f"**{T('water.watch')}**")
            for k in (1, 2, 3): st.write("• " + T(f"water.watch.{k}"))
    if farm.irrigated:
        with st.container(border=True): st.info(T("water.irrigated_note"))
    with st.container(border=True):
        st.warning(T("water.limits")); st.caption(T("water.smap_na"))
    if A["power"] is not None: trace_caption(A["pmeta"])
