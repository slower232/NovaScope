import html
import json
import streamlit as st
from folium import Map, Marker, Popup, DivIcon, GeoJson, TileLayer, LayerControl
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from ui.context import T, crop_name, go
from ui.crop_visuals import crop_header, crop_icon, crop_pill, crop_thumb
from ui.science import help_icon
from ui.styles import ICON

LEVEL_CLASS = {"red": "red", "yellow": "yellow", "green": "green", "gray": "gray"}
WATER_GUIDE = {"favorable": 82, "limited": 48, "possible_stress": 24, "insufficient": 38}
CROP_COLORS = {
    "maiz": "#e8a832",
    "cebolla": "#9265c2",
    "frijol": "#2f9b68",
    "trigo": "#d98f42",
    "chile": "#df5548",
    "papa": "#96734a",
    "manzana": "#d94d67",
}


def _t(key: str, en: str, es: str, **kw) -> str:
    try:
        val = T(key, **kw)
        if val and val != key:
            return val
    except Exception:
        pass
    base = es if st.session_state.get("lang", "en") == "es" else en
    return base.format(**kw) if kw else base


def _water_tank(status):
    fill = WATER_GUIDE.get(status, 38)
    return f'<div class="fs-water-tank" aria-label="Illustrative water guide"><div class="fs-water-fill" style="height:{fill}%"></div></div>'


def _field_map(farms, active):
    center = [active.lat, active.lon] if active else [28.6, -106.1]
    m = Map(location=center, zoom_start=12 if active else 7, control_scale=True, tiles="OpenStreetMap")
    TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name=_t("map.satellite", "Satellite View", "Vista Satelital"),
        overlay=False,
        control=True,
    ).add_to(m)
    Fullscreen(position="topright").add_to(m)
    for farm in farms:
        emoji = crop_icon(farm.crop_id)
        label, crop = html.escape(farm.name), html.escape(crop_name(farm.crop_id))
        area = f"<br>{farm.area_ha:.1f} ha" if farm.area_ha else ""
        if farm.boundary and farm.boundary.geojson:
            geometry = json.loads(farm.boundary.geojson)
            color = CROP_COLORS.get(farm.crop_id, "#2e6f40")
            GeoJson(
                geometry,
                name=label,
                tooltip=f"{emoji} {label} · {crop}",
                style_function=lambda _feature, color=color: {
                    "color": color,
                    "weight": 3,
                    "fillColor": color,
                    "fillOpacity": 0.42,
                },
            ).add_to(m)
        Marker(
            [farm.lat, farm.lon],
            tooltip=f"{emoji} {label} · {crop}",
            popup=Popup(
                f"<div style='display:flex;gap:8px;align-items:center'>{crop_thumb(farm.crop_id, 48, crop)}"
                f"<div><b>{emoji} {label}</b><br>{crop}{area}</div></div>",
                max_width=260,
            ),
            icon=DivIcon(
                html=f'<div style="font-size:26px;text-shadow:0 1px 4px white">{emoji}</div>',
                icon_size=(30, 30),
                icon_anchor=(15, 15),
            ),
        ).add_to(m)
    LayerControl(position="bottomright").add_to(m)
    return m


def _alert_panel(r):
    level = LEVEL_CLASS.get(r.level, "gray")
    title = T("risk." + r.key + ".name")
    state = T("level." + r.level).split(" · ")[0]
    content = (
        T("risk." + r.key + ".what", **r.params)
        if r.level in ("red", "yellow")
        else (T("alert.green.what") if r.level == "green" else T("alert.gray.what"))
    )
    st.markdown(
        f'<div class="fs-alert-panel fs-alert-{level}"><strong>{ICON[r.level]} {html.escape(state)} · {html.escape(title)}</strong><br>{html.escape(content)}</div>',
        unsafe_allow_html=True,
    )


def _overall_verdict_badge(overall: dict) -> str:
    n_red = overall.get("n_red", 0)
    n_yel = overall.get("n_yellow", 0)
    if n_red > 0:
        return f'<div class="fs-verdict-badge fs-verdict-red">🔴 {_t("verdict.red", "Action recommended: check alerts below", "Atención recomendada: revisa las alertas abajo")}</div>'
    if n_yel > 0:
        return f'<div class="fs-verdict-badge fs-verdict-yellow">🟡 {_t("verdict.yellow", "Caution: monitor water or weather changes", "Precaución: vigila el agua o cambios de clima")}</div>'
    return f'<div class="fs-verdict-badge fs-verdict-green">🟢 {_t("verdict.green", "Your field looks stable today", "Tu parcela se ve estable hoy")}</div>'


def render(user, farms, farm, A):
    if not farms:
        with st.container(border=True):
            st.info(T("farm.none"))
            st.button(
                T("dash.new_farm"),
                type="primary",
                key="empty_add_farm",
                on_click=lambda: st.session_state.update(page="farms", farms_view="new"),
            )
        return

    if st.session_state.pop("farm_saved_notice", False):
        st.markdown(f'<div class="fs-toast">✅ {html.escape(T("farm.saved"))}</div>', unsafe_allow_html=True)

    total_ha = sum(f.area_ha or 0 for f in farms)

    # 1. Hero Banner visual con diagnóstico rápido en palabras simples
    banner_left, banner_right = st.columns([3.2, 1.5], vertical_alignment="center")
    with banner_left:
        hero_html = (
            f'<div class="fs-hero-banner">'
            f'{crop_header(farm.crop_id, f"{farm.name} · {crop_name(farm.crop_id)}", f"🌱 {len(farms)} {_t("ui.parcels_word", "parcel(s)", "parcela(s)")} · {total_ha:.1f} ha", size=72)}'
            f'{_overall_verdict_badge(A["overall"])}'
            f'</div>'
        )
        st.markdown(hero_html, unsafe_allow_html=True)
    with banner_right:
        st.button(
            f"➕ {T('dash.new_farm')}",
            type="primary",
            use_container_width=True,
            key="new_farm_top",
            on_click=lambda: st.session_state.update(page="farms", farms_view="new"),
        )
        st.button(
            f"📋 {T('dash.my_farms')}",
            type="secondary",
            use_container_width=True,
            key="my_farms_top",
            on_click=lambda: st.session_state.update(page="farms", farms_view="list"),
        )

    # 2. Contenido principal en 2 columnas limpias
    left, right = st.columns([1.05, 1.2], gap="large")
    with left:
        with st.container(border=True):
            alert_head, alert_link = st.columns([4.2, 1.3], vertical_alignment="center")
            alert_head.markdown(f"#### 🔔 {_t('ui.simple_alerts', 'What to watch today', 'Qué vigilar hoy')}")
            alert_link.button(
                _t("ui.more", "Details →", "Detalle →"),
                key="overview_alert_link",
                type="secondary",
                use_container_width=True,
                on_click=go,
                args=("alerts",),
            )
            risks = sorted(A["risks"], key=lambda r: {"red": 3, "yellow": 2, "gray": 1, "green": 0}[r.level])
            for r in risks[:3]:
                _alert_panel(r)
            if not risks:
                st.info(T("alert.green.what"))

        with st.container(border=True):
            st.markdown(f"#### 💧 {_t('ui.simple_water', 'Water & Moisture', 'Agua y Humedad')}")
            tank, summary = st.columns([1, 2.3], vertical_alignment="center")
            with tank:
                st.markdown(_water_tank(A["water"]["status"]), unsafe_allow_html=True)
            with summary:
                st.markdown(f"**{T('water.status.' + A['water']['status'])}**")
                st.caption(T("water.visual_only"))
                st.button(
                    f"💧 {T('dash.open')} →",
                    on_click=go,
                    args=("water",),
                    key="dash_water",
                    type="secondary",
                )

    with right:
        with st.container(border=True):
            st.markdown(f"#### 🗺️ {T('dash.map')}")
            st_folium(_field_map(farms, farm), height=410, width=None, returned_objects=[], key="overview_fields")
            st.markdown(
                "<div class='fs-map-caption'>" + "".join(crop_pill(f.crop_id, f.name, 28) for f in farms) + "</div>",
                unsafe_allow_html=True,
            )

    # 3. Siguiente paso recomendado en el flujo del agricultor
    next_c1, next_c2 = st.columns([2, 1], gap="medium")
    with next_c1:
        st.button(
            f"🧭 {_t('ui.next_rotation', 'Next Step: See Crop Rotation & Field Advice →', 'Siguiente paso: Ver Rotación de Cultivos y Consejos →')}",
            type="primary",
            use_container_width=True,
            key="cta_next_rotation",
            on_click=go,
            args=("recommendations",),
        )
    with next_c2:
        st.button(
            f"📄 {_t('ui.download_pdf', 'Download Producer PDF Report →', 'Descargar Reporte PDF →')}",
            type="secondary",
            use_container_width=True,
            key="cta_next_report",
            on_click=go,
            args=("reports",),
        )

    # 4. Detalles técnicos ocultos por defecto (para técnicos o jueces)
    with st.expander(f"🔬 {_t('ui.tech_expander', 'Show technical & NASA satellite metrics (optional)', 'Ver datos técnicos y satelitales de NASA (opcional)')}", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric(T("card.farms.title"), f"{len(farms)}", f"{total_ha:.1f} ha")
        c2.metric(T("card.env.title"), f"{A['water'].get('p30_mm', '—')} mm" if A["power"] is not None else "—", T("card.env.cap"))
        c3.metric(T("card.alerts.title"), f"{A['overall']['n_red']} 🔴 · {A['overall']['n_yellow']} 🟡")
        h1, h2 = st.columns(2)
        with h1:
            help_icon("alerts", "overview_alerts")
        with h2:
            help_icon("water", "overview_water")
        if A["fc"] is None:
            st.caption(T("dash.no_forecast"))