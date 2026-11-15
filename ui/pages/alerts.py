import json
import streamlit as st
from database import repositories as repo
from modules.risk_engine.engine import evaluate_risks, overall_level
from ui.context import T, badge, data_status, trace_caption
from ui.science import basis_expander

ORDER = {"red": 3, "yellow": 2, "gray": 1, "green": 0}


def _card(r):
    with st.container(border=True):
        c1, c2 = st.columns([3, 2])
        c1.markdown(f"**{T('risk.' + r.key + '.name')}**"); c2.markdown(badge(r.level), unsafe_allow_html=True)
        if r.level in ("yellow", "red"):
            st.write(f"**{T('alert.what')}:** {T('risk.' + r.key + '.what', **r.params)}")
            st.write(f"**{T('alert.why')}:** {T('risk.' + r.key + '.why')}")
            st.write(f"**{T('alert.do')}:** {T('risk.' + r.key + '.' + r.level)}")
            st.caption(f"{T('alerts.type')}: {T('kind.' + r.kind)} · {T('alert.imp')}: {T('imp.' + r.importance)} · {T('alert.src')}: {r.source}")
        elif r.level == "green":
            st.write(T("alert.green.what")); st.caption(f"{T('alert.src')}: {r.source}")
        else:
            st.write(T("alert.gray.what"))


def render(user, farm, A):
    st.subheader(T("alerts.title")); st.warning(T("forecast.warn")); data_status(A["fmeta"])
    basis_expander("alerts")
    hz = st.radio(T("horizon"), ["hnow", "h24", "h7"], format_func=T, horizontal=True, index=2)
    days = {"hnow": 1, "h24": 3, "h7": 7}[hz]
    risks = evaluate_risks(A["crop"], A["fc"], A["recent"], A["spi_value"], A["p90"], farm.irrigated, farm.lat, horizon_days=days)
    st.markdown(badge(overall_level(risks)["level"]), unsafe_allow_html=True); st.caption(T("overall.note"))
    if repo.get_farm(user, farm.id) is not None and hz == "h7":
        repo.save_alerts(farm.id, risks)
    for r in sorted(risks, key=lambda x: -ORDER[x.level]): _card(r)
    st.divider(); st.markdown(f"**{T('alerts.history')}**")
    hist = repo.list_alerts(farm.id)
    if not hist: st.caption(T("alerts.none"))
    for a in hist:
        p = json.loads(a.params_json); kind = p.pop("kind", "forecast")
        with st.container(border=True):
            st.write(f"{T('level.' + a.level).split(' · ')[0]} · {a.created_at:%Y-%m-%d} · {farm.name} · {T('risk.' + a.risk_key + '.name')}")
            st.caption(f"{T('kind.' + kind)} · {T('alerts.data')}: {p}")
