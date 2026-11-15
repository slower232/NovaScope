import html
import streamlit as st
from modules.recommendations.engine import missing_information, recommend_crops
from ui.context import CROPS, T, crop_name, data_status, farm_dict, trace_caption
from ui.crop_visuals import crop_icon, crop_thumb
from ui.science import basis_expander, rec_item_help

CICON = {"high": "▲", "moderate": "●", "low": "▼", "insufficient": "?"}
CROPS_BY_ID = {c["id"]: c for c in CROPS}


def _item(r):
    category = r["category"]
    status_class = "yellow" if r["missing"] else {"high":"green", "moderate":"yellow", "low":"red", "insufficient":"yellow"}.get(category, "gray")
    crop = html.escape(crop_name(r["crop_id"]))
    icon = crop_icon(r["crop_id"])
    status = html.escape(T("rec.badge.missing") if r["missing"] else T("compat." + category))
    with st.container(border=True):
        img_col, name_col, status_col, help_col = st.columns([0.9, 2.6, 2.2, 0.6], vertical_alignment="center")
        img_col.markdown(crop_thumb(r["crop_id"], 72, crop), unsafe_allow_html=True)
        name_col.markdown(f"### {icon} {crop}")
        status_col.markdown(f'<div class="fs-compat fs-compat-{status_class}">{CICON[category]} {status}</div>', unsafe_allow_html=True)
        with help_col:
            rec_item_help(r["index"], r.get("n_years"), bool(CROPS_BY_ID.get(r["crop_id"], {}).get("verified")), f"rec_{r['crop_id']}")
        if r["index"] is not None:
            st.markdown(f'<div class="fs-rec-fact">📊 {html.escape(T("rec.just_text", idx=r["index"], n=r["n_years"]))}</div>', unsafe_allow_html=True)
            q = r["requirements"]
            req = T("rec.req_text", w1=q["water_mm"][0], w2=q["water_mm"][1], c1=q["cycle_days"][0], c2=q["cycle_days"][1], t1=q["t_opt_c"][0], t2=q["t_opt_c"][1])
            st.markdown(f'<div class="fs-rec-requirements">💧 {html.escape(req)}</div>', unsafe_allow_html=True)
        adv, lim = st.columns(2, gap="medium")
        advantages = "<br>".join("• " + html.escape(T("rec." + code, **params)) for code, params in r["advantages"]) or "—"
        limitations = "<br>".join("• " + html.escape(T("rec." + code, **params)) for code, params in r["limitations"]) or "—"
        adv.markdown(f'<div class="fs-rec-good"><strong>✅ {html.escape(T("rec.adv"))}</strong><br><br>{advantages}</div>', unsafe_allow_html=True)
        lim.markdown(f'<div class="fs-rec-limits"><strong>⚠️ {html.escape(T("rec.lim"))}</strong><br><br>{limitations}</div>', unsafe_allow_html=True)
        if r["missing"]:
            missing = ", ".join(T("miss." + m) for m in r["missing"])
            st.markdown(f'<div class="fs-rec-missing">ℹ️ {html.escape(T("rec.missing_intro"))} {html.escape(missing)}</div>', unsafe_allow_html=True)


def render(user, farm, A):
    from ui.pages import rotation
    st.session_state.setdefault("recommendation_view", "crops")
    left, right = st.columns(2)
    left.button("🌱 " + T("rec.crops_link"), key="rec_view_crops",
                type="primary" if st.session_state.recommendation_view == "crops" else "secondary",
                on_click=lambda: st.session_state.update(recommendation_view="crops"), use_container_width=True)
    right.button("🔄 " + T("rec.rotation_link"), key="rec_view_rotation",
                 type="primary" if st.session_state.recommendation_view == "rotation" else "secondary",
                 on_click=lambda: st.session_state.update(recommendation_view="rotation"), use_container_width=True)
    if st.session_state.recommendation_view == "rotation":
        rotation.render(user, farm, A)
        return
    st.subheader(T("rec.title")); st.info(T("rec.note"))
    basis_expander("rec")
    if A["power"] is None:
        st.error(T("dash.no_power")); return
    trace_caption(A["pmeta"]); data_status(A["pmeta"])
    fd = farm_dict(farm)
    miss = missing_information({**fd, "crop_history": fd["past_history"]})
    if miss:
        st.warning(T("rec.reliability") + " " + ", ".join(T("miss." + m) for m in miss))
    recs = recommend_crops(A["power"], CROPS, fd, fd["exclude"])
    main = [r for r in recs if r["category"] in ("high", "moderate")]
    rest = [r for r in recs if r["category"] not in ("high", "moderate")]
    if not main: st.info(T("rec.none_good"))
    for r in main: _item(r)
    with st.expander(T("rec.show_more")):
        for r in rest: _item(r)
