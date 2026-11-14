"""Field Shift – interfaz Streamlit. Ejecutar: streamlit run app.py"""
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from algorithms.climate_anomalies import monthly_aggregate, monthly_anomalies, monthly_climatology
from algorithms.crop_rotation_optimizer import optimize_rotation
from algorithms.crop_suitability import crop_ready
from algorithms.drought_index import spi
from algorithms.uncertainty import confidence
from authentication import auth
from authentication.permissions import can
from config.settings import settings
from database import repositories as repo
from database.initialization import init_db
from modules.crop_rotation.crop_catalog import get_crop, load_crops, load_weights
from modules.geospatial.geometry import area_hectares, centroid, validate_point
from modules.reporting.pdf_report import diagnosis_pdf
from modules.risk_engine.engine import evaluate_risks, overall_level
from modules.simulation.simulator import compare, run_scenario
from services.nasa_power import fetch_daily
from services.weather_forecast import fetch_forecast
from ui.styles import CSS, ICON
from ui.translations import LANGS, t

st.set_page_config(page_title="Field Shift", page_icon="🌾", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
init_db()
CROPS = load_crops()
CROP_NAMES = {"es": {c["id"]: c["name_es"] for c in CROPS}, "en": {c["id"]: c["name_en"] for c in CROPS}}
MONTHS = {"es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
          "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}

lang = st.session_state.get("lang", "es")


def T(k, **kw):
    return t(k, lang, **kw)


def badge(level):
    return f'<span class="fs-badge fs-{level}">{ICON[level]} {T("level." + level)}</span>'


def data_status(meta):
    if meta.get("fetched_at") is None:
        st.error(T("status.unavailable", e=meta.get("error")))
    elif meta.get("is_stale"):
        st.warning(T("status.stale", t=meta["fetched_at"].strftime("%Y-%m-%d %H:%M UTC")))
    elif meta.get("is_cached"):
        st.caption("💾 " + T("status.cached", t=meta["fetched_at"].strftime("%Y-%m-%d %H:%M UTC")))
    else:
        st.caption("🛰️ " + T("status.fresh"))


@st.cache_data(ttl=3600, show_spinner=False)
def load_power(lat, lon):
    return fetch_daily(lat, lon)


@st.cache_data(ttl=900, show_spinner=False)
def load_forecast(lat, lon):
    return fetch_forecast(lat, lon, 7)


def analyze(farm):
    """Reúne datos reales y corre el motor de riesgos. Todo fallo se refleja como GRIS, nunca se inventa."""
    crop = get_crop(farm.crop_id, CROPS)
    power, pmeta = load_power(farm.lat, farm.lon)
    fc, fmeta = load_forecast(farm.lat, farm.lon)
    spi_val, spi_warn, p90, recent, series = None, [], None, None, None
    if power is not None:
        monthly = monthly_aggregate(power, "precip", "sum")
        series, spi_warn = spi(monthly, 3)
        v = series.dropna()
        spi_val = float(v.iloc[-1]) if len(v) else None
        p90 = power.groupby(power["date"].dt.month)["tmax"].quantile(0.9).to_dict()
        recent = power.dropna(subset=["tmax", "tmin", "precip"]).tail(40)
    risks = evaluate_risks(crop, fc, recent, spi_val, p90, farm.irrigated, farm.lat)
    return dict(crop=crop, power=power, pmeta=pmeta, fc=fc, fmeta=fmeta, risks=risks,
                overall=overall_level(risks), spi_series=series, spi_warn=spi_warn)


def risk_card(r):
    with st.container(border=True):
        c1, c2 = st.columns([3, 2])
        c1.markdown(f"**{T('risk.' + r.key + '.name')}**")
        c2.markdown(badge(r.level), unsafe_allow_html=True)
        if r.level in ("yellow", "red"):
            st.write(f"**{T('alert.what')}:** {T('risk.' + r.key + '.what', **r.params)}")
            st.write(f"**{T('alert.why')}:** {T('risk.' + r.key + '.why')}")
            st.write(f"**{T('alert.do')}:** {T('risk.' + r.key + '.' + r.level)}")
            st.caption(f"{T('alert.imp')}: {T('imp.' + r.importance)} · {T('alert.src')}: {r.source}")
        elif r.level == "green":
            st.write(T("alert.green.what")); st.caption(f"{T('alert.src')}: {r.source}")
        else:
            st.write(T("alert.gray.what"))


# ---------------------------------------------------------------- AUTH
def auth_screen():
    st.markdown(f'<div class="fs-hero"><h1>🌾 {T("app.title")}</h1><p>{T("app.tagline")}</p></div>', unsafe_allow_html=True)
    if repo.count_users() == 0:
        st.subheader(T("setup.title")); st.info(T("setup.note"))
        with st.form("setup"):
            u = st.text_input(T("username")); p = st.text_input(T("password"), type="password")
            if st.form_submit_button(T("setup.create")):
                try:
                    auth.create_first_admin(u, p); st.success("OK"); st.rerun()
                except Exception as e:
                    st.error(T("err.generic", e=e))
        return
    tab_in, tab_reg = st.tabs([T("login"), T("register")])
    with tab_in, st.form("login"):
        u = st.text_input(T("username")); p = st.text_input(T("password"), type="password")
        if st.form_submit_button(T("login")):
            user = auth.login(u, p)
            if user:
                st.session_state["uid"] = user.id; st.session_state["uname"] = user.username
                st.session_state["role"] = user.role; st.rerun()
            st.error(T("err.login"))
    with tab_reg, st.form("register"):
        u = st.text_input(T("username"), key="ru"); p = st.text_input(T("password"), type="password", key="rp")
        role = st.selectbox(T("role"), ["farmer", "advisor"], format_func=lambda r: T("role." + r))
        if st.form_submit_button(T("register")):
            try:
                auth.register(u, p, role, lang); st.success("OK")
            except Exception as e:
                st.error(T("err.generic", e=e))


# ---------------------------------------------------------------- PAGES
def page_farms(user):
    from folium import Map, Marker
    from folium.plugins import Draw
    from streamlit_folium import st_folium
    st.subheader(T("farm.new"))
    st.caption(T("farm.map_help"))
    m = Map(location=[28.6353, -106.0889], zoom_start=7, tiles="OpenStreetMap")
    Draw(export=True, draw_options={"polyline": False, "circle": False, "rectangle": True, "marker": False,
                                    "circlemarker": False, "polygon": True}).add_to(m)
    out = st_folium(m, height=420, width=None, returned_objects=["last_active_drawing", "last_clicked"])
    geo = (out or {}).get("last_active_drawing"); click = (out or {}).get("last_clicked")
    lat = lon = area = None
    if geo and geo.get("geometry", {}).get("type") == "Polygon":
        lat, lon = centroid(geo); area = area_hectares(geo)
    elif click:
        lat, lon = click["lat"], click["lng"]; st.warning(T("farm.pin_warn"))
    if lat is not None:
        st.write(f"📍 {T('farm.coords')}: {lat:.5f}, {lon:.5f}" + (f" · {T('farm.area')}: {area:.2f} {T('ha')}" if area else ""))
    with st.form("farm_form"):
        name = st.text_input(T("farm.name"), value="")
        crop_id = st.selectbox(T("farm.crop"), [c["id"] for c in CROPS], format_func=lambda i: CROP_NAMES[lang][i])
        irrigated = st.checkbox(T("farm.irrigated"))
        with st.expander(T("farm.optional")):
            ph = st.number_input(T("farm.ph"), 0.0, 14.0, 0.0, 0.1)
            tex = st.text_input(T("farm.texture"))
        if st.form_submit_button(T("farm.save")):
            if lat is None:
                st.error(T("farm.need_loc"))
            else:
                try:
                    validate_point(lat, lon)
                    repo.create_farm(user.id, dict(name=name.strip() or "Parcela", lat=lat, lon=lon, crop_id=crop_id,
                                                   irrigated=irrigated, area_ha=area, soil_ph=ph or None,
                                                   soil_texture=tex.strip() or None), geo if area else None)
                    st.success(T("farm.saved"))
                except Exception as e:
                    st.error(T("err.generic", e=e))
    for f in repo.list_farms(user):
        c1, c2 = st.columns([5, 1])
        c1.write(f"**{f.name}** · {CROP_NAMES[lang][f.crop_id]} · {f.lat:.4f}, {f.lon:.4f}")
        if c2.button(T("farm.delete"), key=f"del{f.id}") and repo.delete_farm(user, f.id):
            st.rerun()


def page_dashboard(farm, A):
    c = st.columns(4)
    c[0].metric(T("dash.crop"), CROP_NAMES[lang][farm.crop_id]); c[1].metric(T("dash.loc"), f"{farm.lat:.3f}, {farm.lon:.3f}")
    if farm.area_ha: c[2].metric(T("farm.area"), f"{farm.area_ha:.2f} {T('ha')}")
    o = A["overall"]
    c[3].markdown(f"**{T('overall')}**<br>{badge(o['level'])}", unsafe_allow_html=True)
    st.caption(T("overall.note"))
    if o["n_gray"]: st.info(T("gray.note", n=o["n_gray"]))
    if A["fc"] is None: st.warning(T("dash.no_forecast"))
    else:
        st.caption(T("forecast.not_nasa")); st.warning(T("forecast.warn"))
        d = A["fc"].rename(columns={"tmax": T("dash.tmax"), "tmin": T("dash.tmin"), "precip": T("dash.rain"), "wind_max": T("dash.wind")})
        st.markdown(f"**{T('dash.forecast')}**")
        st.dataframe(d[["date", T("dash.tmax"), T("dash.tmin"), T("dash.rain"), T("dash.wind")]], hide_index=True, use_container_width=True)
    data_status(A["pmeta"]); data_status(A["fmeta"])
    if not crop_ready(A["crop"]): st.caption(T("sim.not_ready"))
    with st.expander(T("dash.map")):
        from folium import Map, Marker
        from streamlit_folium import st_folium
        m = Map(location=[farm.lat, farm.lon], zoom_start=13); Marker([farm.lat, farm.lon], tooltip=farm.name).add_to(m)
        st_folium(m, height=320, width=None, returned_objects=[])


def page_alerts(farm, A):
    st.warning(T("forecast.warn")); data_status(A["fmeta"])
    hz = st.radio(T("horizon"), ["hnow", "h24", "h7"], format_func=T, horizontal=True, index=2)
    days = {"hnow": 1, "h24": 3, "h7": 7}[hz]
    A2 = evaluate_risks(A["crop"], A["fc"], A["power"].dropna(subset=["tmax", "tmin", "precip"]).tail(40) if A["power"] is not None else None,
                        next((r.params.get("spi") for r in A["risks"] if r.key == "meteorological_drought" and r.params), None),
                        A["power"].groupby(A["power"]["date"].dt.month)["tmax"].quantile(0.9).to_dict() if A["power"] is not None else None,
                        farm.irrigated, farm.lat, horizon_days=days)
    st.markdown(badge(overall_level(A2)["level"]), unsafe_allow_html=True)
    for r in sorted(A2, key=lambda x: -{"red": 3, "yellow": 2, "gray": 1, "green": 0}[x.level]):
        risk_card(r)


def page_climate(farm, A):
    p = A["power"]; st.subheader(T("clim.title")); data_status(A["pmeta"]); st.caption(T("clim.warn_res"))
    if p is None: st.error(T("dash.no_power")); return
    n_years = p["date"].dt.year.nunique(); st.caption(T("clim.years", n=n_years))
    mp = monthly_aggregate(p, "precip", "sum"); clim = monthly_climatology(mp)
    last = mp.dropna().tail(24)
    fig = go.Figure([go.Bar(x=last.index, y=last.values, name=T("mm"), marker_color="#43a047"),
                     go.Scatter(x=last.index, y=clim["mean"].reindex(last.index.month).values, name="Ø", line=dict(color="#6d4c41", dash="dash"))])
    fig.update_layout(title=T("clim.precip"), height=330, yaxis_title="mm"); st.plotly_chart(fig, use_container_width=True)
    ta = monthly_anomalies(monthly_aggregate(p, "tmean", "mean")).dropna().tail(36)
    st.plotly_chart(go.Figure(go.Bar(x=ta.index, y=ta["anomaly"], marker_color=["#c62828" if v > 0 else "#1565c0" for v in ta["anomaly"]]))
                    .update_layout(title=T("clim.temp"), height=300, yaxis_title="°C"), use_container_width=True)
    s = A["spi_series"]
    if s is not None and s.notna().any():
        st.caption(T("clim.spi_help"))
        if A["spi_warn"]: st.warning(T("clim.spi_warn"))
        s2 = s.dropna().tail(48)
        st.plotly_chart(go.Figure(go.Bar(x=s2.index, y=s2.values, marker_color=["#c62828" if v < -1 else "#2e7d32" for v in s2.values]))
                        .update_layout(title=T("clim.spi"), height=300), use_container_width=True)


def conf_line(A, n_years):
    cov = float(A["power"][["tmean", "precip"]].notna().all(axis=1).mean()) if A["power"] is not None else 0
    c = confidence(cov, n_years, bool(A["crop"].get("verified")), 0, bool(A.get("has_soil")))
    st.caption(f"{T('conf')}: **{T('conf.' + c['label'])}** ({c['score']}) — {T('conf.note')}")


def page_rotation(farm, A):
    st.subheader(T("rot.title")); p = A["power"]
    if p is None: st.error(T("dash.no_power")); return
    w0 = load_weights(); cols = st.columns(5); w = {}
    for col, k in zip(cols, w0): w[k] = col.slider(T("w." + k), 0.0, 1.0, float(round(w0[k], 2)), 0.05)
    horizon = st.slider(T("rot.horizon"), 3, 5, 3)
    if st.button(T("rot.run")):
        if sum(w.values()) == 0: st.error("Σ pesos = 0"); return
        w = {k: v / sum(w.values()) for k, v in w.items()}
        with st.spinner(T("loading")):
            res = optimize_rotation(p, CROPS, w, farm.irrigated, horizon)
        repo.save_rotation(farm.id, w, res)
        st.caption(T("rot.eval", n=res["n_evaluated"], m=res["n_candidate_crops"]))
        for i, alt in enumerate(res["top"], 1):
            with st.container(border=True):
                st.markdown(f"**#{i}** — {T('rot.score')}: **{alt['score']:.3f}**")
                cc = st.columns(len(alt["sequence"]))
                for y, (col, cid, d) in enumerate(zip(cc, alt["sequence"], alt["details"]), 1):
                    col.markdown(f"**{T('rot.year', n=y)}**<br>{CROP_NAMES[lang][cid]}<br><span class='fs-small'>{T('rot.sowing', m=MONTHS[lang][d['sowing_month'] - 1])}</span>", unsafe_allow_html=True)
                st.plotly_chart(go.Figure(go.Bar(x=[T("w." + k) for k in alt["criteria"]], y=list(alt["criteria"].values()), marker_color="#43a047"))
                                .update_layout(height=220, margin=dict(t=10, b=10), yaxis_range=[0, 1]), use_container_width=True, key=f"rot{i}")
                if alt["legume_transitions"]: st.caption("🌱 " + T("rot.legume"))
                if alt["uses_risk_proxy"]: st.caption("ℹ️ " + T("rot.proxy"))
        if res["excluded"]: st.caption(T("rot.excluded", c=", ".join(CROP_NAMES[lang][c] for c in res["excluded"])))
        conf_line(A, p["date"].dt.year.nunique()); st.info(T("rot.disclaimer"))


def page_simulator(farm, A):
    st.subheader(T("sim.title")); p = A["power"]
    if p is None: st.error(T("dash.no_power")); return
    annual = [c for c in CROPS if c["annual"] and crop_ready(c)]
    c1, c2, c3 = st.columns(3)
    cid = c1.selectbox(T("sim.crop"), [c["id"] for c in annual], format_func=lambda i: CROP_NAMES[lang][i],
                       index=next((i for i, c in enumerate(annual) if c["id"] == farm.crop_id), 0))
    month = c2.selectbox(T("sim.month"), list(range(1, 13)), format_func=lambda m: MONTHS[lang][m - 1], index=5)
    irr = c3.checkbox(T("sim.irr"), value=farm.irrigated)
    dT = st.slider(T("sim.dT"), -3.0, 5.0, 0.0, 0.5); dp = st.slider(T("sim.p"), -50, 50, 0, 5)
    if st.button(T("sim.run")):
        crop = get_crop(cid, CROPS)
        base = run_scenario(p, crop, month, 1, irr); scn = run_scenario(p, crop, month, 1, irr, dT, 1 + dp / 100)
        cmp_ = compare(base, scn)
        repo.save_simulation(farm.id, scn["params"], cmp_)
        cols = st.columns(3)
        for col, (k, lab) in zip(cols, [("suitability", "sim.suit"), ("probability", "sim.prob"), ("water_deficit_mm", "sim.def")]):
            b, s = cmp_[k]["baseline"], cmp_[k]["scenario"]
            fmt = (lambda v: f"{v * 100:.0f} %") if k == "probability" else (lambda v: f"{v:.2f}" if k == "suitability" else f"{v:.0f}")
            if b is None or s is None: col.metric(T(lab), "—"); continue
            col.metric(T(lab), fmt(s), delta=(fmt(s - b) if k != "probability" else f"{(s - b) * 100:+.0f} pp"), delta_color="inverse" if k == "water_deficit_mm" else "normal")
        pr = scn["probability"]
        if pr.get("probability") is None: st.caption(T("sim.prob_na", m=", ".join(pr.get("missing", []))))
        else: st.caption(T("sim.ci", lo=f"{pr['ci95'][0] * 100:.0f}", hi=f"{pr['ci95'][1] * 100:.0f}", n=pr["n_years"]))
        conf_line({**A, "crop": crop}, p["date"].dt.year.nunique()); st.info(T("sim.disclaimer"))


def page_reports(farm, A):
    st.subheader(T("rep.title"))
    srcs = ["NASA POWER (" + A["pmeta"]["resolution"] + ")" if A["power"] is not None else "NASA POWER: n/d",
            "Open-Meteo (CC BY 4.0)" if A["fc"] is not None else "Open-Meteo: n/d"]
    notes = [T("clim.warn_res")] + [T("clim.spi_warn")] * bool(A["spi_warn"])
    pdf = diagnosis_pdf(lang, dict(name=farm.name, lat=farm.lat, lon=farm.lon), CROP_NAMES[lang][farm.crop_id],
                        A["risks"], A["overall"], srcs, notes)
    st.download_button(T("rep.diag"), pdf, file_name=f"field_shift_{farm.id}.pdf", mime="application/pdf")
    st.caption(T("demo.none") + " · " + T("ai.title") + ": " + T("ai.na"))


# ---------------------------------------------------------------- MAIN
head = st.columns([6, 1, 1])
lang = head[1].selectbox(T("lang"), list(LANGS), format_func=LANGS.get, key="lang", label_visibility="collapsed")
if "uid" not in st.session_state:
    auth_screen(); st.stop()
user = type("U", (), {"id": st.session_state["uid"], "role": st.session_state["role"]})()
if head[2].button(T("logout")):
    st.session_state.clear(); st.rerun()
st.markdown(f'<div class="fs-hero"><h1>🌾 {T("app.title")}</h1><p>{T("app.tagline")} · {st.session_state["uname"]}</p></div>', unsafe_allow_html=True)
pages = ["dashboard", "farms", "alerts", "climate", "rotation", "simulator", "reports"]
page = st.radio("nav", pages, format_func=lambda p: T("nav." + p), horizontal=True, label_visibility="collapsed")
if page == "farms":
    page_farms(user)
else:
    farms = repo.list_farms(user)
    if not farms:
        st.info(T("farm.none")); st.stop()
    by_id = {f.id: f for f in farms}
    fid = st.selectbox(T("farm.select"), list(by_id), format_func=lambda i: f"{by_id[i].name} · {CROP_NAMES[lang][by_id[i].crop_id]}")
    farm = by_id[fid]
    with st.spinner(T("loading")):
        A = analyze(farm)
    {"dashboard": page_dashboard, "alerts": page_alerts, "climate": page_climate, "rotation": page_rotation,
     "simulator": page_simulator, "reports": page_reports}[page](farm, A)
st.caption(T("limits"))
