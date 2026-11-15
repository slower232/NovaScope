import streamlit as st
import plotly.graph_objects as go
from algorithms.climate_anomalies import monthly_aggregate, monthly_anomalies, monthly_climatology
from ui.context import T, data_status, trace_caption
from ui.science import basis_expander



def _weather_visual(row):
    def value(key):
        v = row.get(key, 0)
        try:
            return 0.0 if v is None or v != v else float(v)
        except (TypeError, ValueError):
            return 0.0
    rain, probability = value("precip"), value("precip_prob")
    tmax, tmin = value("tmax"), value("tmin")
    wind, solar = value("wind_max"), value("solar")
    if tmax >= 40 or tmin <= 0 or rain >= 25 or wind >= 60:
        level = "red"
    elif tmax >= 35 or tmin <= 5 or rain >= 10 or probability >= 60 or wind >= 40:
        level = "yellow"
    else:
        level = "green"
    if tmin <= 3: icon, condition = "🥶", "cold"
    elif tmax >= 38: icon, condition = "🥵", "heat"
    elif rain >= 1 or probability >= 55: icon, condition = "🌧️", "rain"
    elif wind >= 35: icon, condition = "💨", "wind"
    elif solar >= 18: icon, condition = "☀️", "sun"
    else: icon, condition = "🌤️", "cloud"
    return level, icon, condition


def _forecast_cards(forecast):
    st.markdown(f"#### {T('env.forecast_title')}")
    st.caption(T("env.visual_note"))
    rows = [row for _, row in forecast.head(7).iterrows()]
    for start in range(0, len(rows), 4):
        cols = st.columns(min(4, len(rows) - start))
        for col, row in zip(cols, rows[start:start + 4]):
            level, icon, condition = _weather_visual(row)
            day = row["date"].strftime("%d/%m")
            def numeric(key):
                value = row.get(key, 0)
                try: return 0.0 if value is None or value != value else float(value)
                except (TypeError, ValueError): return 0.0
            precip, tmax, tmin = numeric("precip"), numeric("tmax"), numeric("tmin")
            card = (f'<div class="fs-weather-card fs-weather-{level}">'
                    f'<div class="fs-weather-day">{day}</div><div class="fs-weather-icon">{icon}</div>'
                    f'<strong>{T("env.wx." + condition)}</strong>'
                    f'<div class="fs-weather-temp">{tmax:.0f}° / {tmin:.0f}°</div>'
                    f'<small>💧 {precip:.1f} mm</small>'
                    f'<div class="fs-weather-status">{T("env.status." + level)}</div></div>')
            with col: st.markdown(card, unsafe_allow_html=True)

def render(user, farm, A):
    p = A["power"]; st.subheader(T("env.title")); data_status(A["pmeta"])
    basis_expander("env")
    with st.container(border=True): st.warning(T("clim.warn_res"))
    if A["fc"] is not None: _forecast_cards(A["fc"])
    if p is None:
        with st.container(border=True): st.error(T("dash.no_power"))
        return
    trace_caption(A["pmeta"]); st.caption(T("clim.years", n=p["date"].dt.year.nunique()))
    w = A["water"]
    if w.get("p30_mm") is not None:
        with st.container(border=True):
            c = st.columns(3)
            c[0].metric(T("env.p30"), f"{w['p30_mm']} mm")
            c[1].metric(T("env.tmean"), f"{w['tmean_30d']} °C" if w["tmean_30d"] is not None else "—")
            sol = p["solar"].dropna().tail(30).mean() if "solar" in p else None
            c[2].metric(T("env.solar"), f"{sol:.1f} kWh/m²/día" if sol is not None and sol == sol else "—")
            st.caption(T("water.through", d=w["data_through"]))
    with st.container(border=True): st.info(T("env.vegetation_na"))
    mp = monthly_aggregate(p, "precip", "sum"); clim = monthly_climatology(mp); last = mp.dropna().tail(24)
    with st.container(border=True):
        st.plotly_chart(go.Figure([go.Bar(x=last.index, y=last.values, name="mm", marker_color="#cf9a48"),
                                   go.Scatter(x=last.index, y=clim["mean"].reindex(last.index.month).values, name="Ø", line=dict(color="#557b52", dash="dash"))])
                        .update_layout(title=T("clim.precip"), height=320, yaxis_title="mm", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"), use_container_width=True)
    ta = monthly_anomalies(monthly_aggregate(p, "tmean", "mean")).dropna().tail(36)
    with st.container(border=True):
        st.plotly_chart(go.Figure(go.Bar(x=ta.index, y=ta["anomaly"], marker_color=["#be6251" if v > 0 else "#668eaa" for v in ta["anomaly"]]))
                        .update_layout(title=T("clim.temp"), height=290, yaxis_title="°C", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"), use_container_width=True)
    series = A["spi_series"]
    if series is not None and series.notna().any():
        with st.container(border=True):
            st.caption(T("clim.spi_help"))
            if A["spi_warn"]: st.warning(T("clim.spi_warn"))
            s2 = series.dropna().tail(48)
            st.plotly_chart(go.Figure(go.Bar(x=s2.index, y=s2.values, marker_color=["#be6251" if v < -1 else "#668e66" for v in s2.values]))
                            .update_layout(title=T("clim.spi"), height=290, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"), use_container_width=True)
