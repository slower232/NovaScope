import json
import streamlit as st
from folium import Map, Rectangle, TileLayer, LayerControl
from folium.plugins import Draw
from streamlit_folium import st_folium

from config.constants import CHIHUAHUA_BBOX
from database import repositories as repo
from modules.geospatial.geometry import area_hectares, centroid, validate_chihuahua, validate_polygon_chihuahua
from ui.context import CROPS, T, crop_name, farm_dict
from ui.crop_visuals import crop_header, crop_icon

AGRI = ["rainfed", "irrigated", "protected", "extensive", "orchard", "mixed"]
WAV = ["sufficient", "limited", "uncertain"]
NONE = "—"

# Zonas agrícolas principales de Chihuahua para acercar el mapa en 1 clic
CHIHUAHUA_ZONES = {
    "all": ("Chihuahua (Estado completo / Full State)", 28.63, -106.07, 7),
    "delicias": ("Delicias / Meoqui", 28.19, -105.47, 11),
    "cuauhtemoc": ("Cuauhtémoc / Anáhuac", 28.41, -106.86, 11),
    "camargo": ("Camargo / La Cruz", 27.68, -105.17, 11),
    "jimenez": ("Jiménez", 27.13, -104.92, 11),
    "ncg": ("Nuevo Casas Grandes / Ascensión", 30.41, -107.91, 10),
    "namiquipa": ("Namiquipa / Bachíniva", 29.25, -107.42, 10),
    "guerrero": ("Guerrero / Madera", 28.55, -107.49, 10),
    "chihuahua": ("Chihuahua Centro / Aldama", 28.68, -105.98, 11),
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


def _err(e: Exception) -> str:
    code = str(e)
    return T("err." + code) if code in ("outside_chihuahua", "self_intersecting", "zero_area") else T("err.generic", e=e)


def _crop_select(label, key, default=None, allow_none=False):
    ids = ([NONE] if allow_none else []) + [c["id"] for c in CROPS]
    idx = ids.index(default) if default in ids else 0
    return st.selectbox(
        label,
        ids,
        index=idx,
        key=key,
        format_func=lambda i: T("farm.none_value") if i == NONE else f"{crop_icon(i)} {crop_name(i)}",
    )


def _map_picker(zone_key: str):
    la0, la1, lo0, lo1 = CHIHUAHUA_BBOX
    _, z_lat, z_lon, z_zoom = CHIHUAHUA_ZONES.get(zone_key, CHIHUAHUA_ZONES["all"])
    m = Map(location=[z_lat, z_lon], zoom_start=z_zoom, min_zoom=6, control_scale=True, tiles="OpenStreetMap")
    TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name=_t("map.satellite", "Satellite View (Find your field)", "Vista Satelital (Ubica tu parcela)"),
        overlay=False,
        control=True,
    ).add_to(m)
    # Delimitación clara de la zona cubierta en Chihuahua
    Rectangle(
        [[la0, lo0], [la1, lo1]],
        color="#2e6f40",
        weight=3,
        dash_array="6",
        fill=True,
        fill_color="#67b982",
        fill_opacity=0.08,
        tooltip=T("farm.cover"),
    ).add_to(m)
    Draw(
        export=False,
        draw_options={
            "polyline": False,
            "circle": False,
            "circlemarker": False,
            "marker": False,
            "rectangle": True,
            "polygon": True,
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(m)
    LayerControl(position="bottomright").add_to(m)
    out = st_folium(m, height=420, width=None, returned_objects=["all_drawings", "last_clicked"], key=f"picker_{zone_key}")
    polys = [d for d in (out or {}).get("all_drawings") or [] if d.get("geometry", {}).get("type") == "Polygon"]
    geo = polys[-1] if polys else None
    click = (out or {}).get("last_clicked")
    return geo, click


def render(user, farms):
    st.session_state.setdefault("farms_view", "new")
    if st.session_state.farms_view == "list":
        head, add_btn = st.columns([4.5, 1.8], vertical_alignment="center")
        head.subheader(f"📋 {T('dash.my_farms')}")
        add_btn.button(
            f"➕ {T('dash.new_farm')}",
            type="primary",
            key="farms_list_add",
            on_click=lambda: st.session_state.update(farms_view="new"),
            use_container_width=True,
        )
        _render_existing_farms(user, farms)
        return

    head, list_link = st.columns([4.5, 1.8], vertical_alignment="center")
    head.subheader(f"🌱 {T('farm.new')}")
    if farms:
        list_link.button(
            f"📋 {T('dash.my_farms')} ({len(farms)})",
            key="farms_new_list",
            on_click=lambda: st.session_state.update(farms_view="list"),
            use_container_width=True,
        )

    # Paso 1: Ubicar parcela en el mapa
    with st.container(border=True):
        m_title, m_zone = st.columns([3, 2], vertical_alignment="center")
        m_title.markdown(f"#### 📍 {_t('farm.step1_map', 'Step 1: Locate your parcel on the map', 'Paso 1: Ubica tu parcela en el mapa')}")
        zone_key = m_zone.selectbox(
            _t("farm.jump_zone", "Zoom to region", "Acercar a municipio"),
            list(CHIHUAHUA_ZONES),
            format_func=lambda k: f"🔎 {CHIHUAHUA_ZONES[k][0]}",
            key="farm_zone_jump",
            label_visibility="collapsed",
        )
        st.caption(_t("farm.map_simple_help", "Switch to Satellite View (bottom right) to see your land, then use the polygon/square tool on the left to outline your parcel or click on it.", "Cambia a Vista Satelital (abajo a la derecha) para ver tu terreno y usa el ícono de polígono/cuadro a la izquierda para marcar tu parcela o haz clic sobre ella."))
        geo, click = _map_picker(zone_key)

        lat = lon = area = None
        if geo:
            try:
                validate_polygon_chihuahua(geo)
                lat, lon = centroid(geo)
                area = area_hectares(geo)
            except Exception as e:
                st.error(T("farm.bad_polygon", e=_err(e)))
                geo = None
        elif click:
            lat, lon = click["lat"], click["lng"]
            st.warning(T("farm.pin_warn"))

        if lat is not None:
            st.success(
                f"📍 {_t('farm.selected_loc', 'Selected location', 'Ubicación seleccionada')}: {lat:.5f}, {lon:.5f}"
                + (f" · **{area:.2f} {T('ha')}** ({area * 10000:,.0f} m²)" if area else "")
            )

    # Paso 2: Datos básicos sencillos
    with st.form("farm_form"):
        st.markdown(f"#### 🌾 {_t('farm.step2_basic', 'Step 2: Basic Parcel Information', 'Paso 2: Datos básicos de tu parcela')}")
        col_a, col_b = st.columns(2, gap="medium")
        with col_a:
            name = st.text_input(T("farm.name"), placeholder=_t("farm.name_ph", "e.g. North Parcel / El Nogal", "ej. Parcela Norte / El Nogal"))
            agri = st.selectbox(T("farm.agri_type"), AGRI, format_func=lambda a: T("agri." + a))
        with col_b:
            crop_id = _crop_select(T("farm.crop"), "n_crop")
            wav = st.selectbox(T("farm.water_av"), WAV, format_func=lambda w: T("wav." + w))
            irrigated = st.checkbox(T("farm.irrigated"), value=False)

        # Vista previa visual del cultivo seleccionado
        st.markdown(
            f'<div class="fs-crop-preview-card">'
            f'{crop_header(crop_id, crop_name(crop_id), _t("farm.crop_selected_hint", "Selected crop for satellite diagnosis", "Cultivo seleccionado para el diagnóstico"), size=58)}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Paso 3: Datos opcionales ocultos por defecto para no abrumar
        with st.expander(f"⚙️ {_t('farm.step3_optional', 'Step 3: Optional details (sowing date, crop history & soil)', 'Paso 3: Datos opcionales (fecha de siembra, historial y suelo)')}", expanded=False):
            opt1, opt2 = st.columns(2, gap="medium")
            with opt1:
                sow = st.date_input(T("farm.sowing_date"), value=None)
                h1 = _crop_select(T("farm.history") + " (1)", "n_h1", None, True)
                h2 = _crop_select(T("farm.history") + " (2)", "n_h2", None, True)
                exclude = st.multiselect(
                    T("farm.exclude"),
                    [c["id"] for c in CROPS if c["annual"]],
                    format_func=lambda i: f"{crop_icon(i)} {crop_name(i)}",
                )
            with opt2:
                irr_sys = st.text_input(T("farm.irr_system"))
                ph = st.number_input(T("farm.ph") + " (0 = " + T("farm.unknown") + ")", 0.0, 14.0, 0.0, 0.1)
                tex = st.text_input(T("farm.texture"))
                om = st.number_input(T("farm.om") + " (0 = " + T("farm.unknown") + ")", 0.0, 100.0, 0.0, 0.1)
                notes = st.text_area(T("farm.notes"), height=80)

        if st.form_submit_button(f"✅ {T('farm.save')}", type="primary", use_container_width=True):
            if lat is None:
                st.error(T("farm.need_loc"))
            else:
                try:
                    validate_chihuahua(lat, lon)
                    hist = [h for h in (h1, h2) if h != NONE]
                    created = repo.create_farm(
                        user.id,
                        dict(
                            name=name.strip() or "Parcela",
                            lat=lat,
                            lon=lon,
                            crop_id=crop_id,
                            irrigated=irrigated,
                            area_ha=area,
                            agri_type=agri,
                            water_availability=wav,
                            irrigation_system=irr_sys.strip() or None,
                            crop_history=json.dumps(hist),
                            soil_ph=ph or None,
                            soil_texture=tex.strip() or None,
                            organic_matter=om or None,
                            sowing_date=sow.isoformat() if sow else None,
                            notes=notes.strip() or None,
                            preferences=json.dumps({"exclude": exclude}),
                        ),
                        geo if area else None,
                    )
                    st.session_state["page"] = "dashboard"
                    st.session_state["farms_view"] = "new"
                    st.session_state["farm_id"] = created.id
                    st.session_state["farm_saved_notice"] = True
                    st.rerun()
                except Exception as e:
                    st.error(T("err.generic", e=_err(e)) if str(e) not in ("outside_chihuahua",) else _err(e))


def _render_existing_farms(user, farms):
    if not farms:
        st.info(T("farm.none"))
        return
    for f in farms:
        with st.container(border=True):
            st.markdown(
                crop_header(
                    f.crop_id,
                    f"{f.name} · {crop_name(f.crop_id)}",
                    f"📍 {f.lat:.4f}, {f.lon:.4f}" + (f" · {f.area_ha:.2f} {T('ha')}" if f.area_ha else ""),
                    size=64,
                ),
                unsafe_allow_html=True,
            )
            with st.expander(f"✏️ {T('farm.edit')} · {f.name}"):
                fd = farm_dict(f)
                n1 = st.text_input(T("farm.name"), f.name, key=f"en{f.id}")
                c1 = _crop_select(T("farm.crop"), f"ec{f.id}", f.crop_id)
                ir = st.checkbox(T("farm.irrigated"), f.irrigated, key=f"ei{f.id}")
                wv = st.selectbox(
                    T("farm.water_av"),
                    WAV,
                    index=WAV.index(f.water_availability) if f.water_availability in WAV else 2,
                    format_func=lambda w: T("wav." + w),
                    key=f"ew{f.id}",
                )
                hp = st.multiselect(
                    T("farm.history"),
                    [c["id"] for c in CROPS],
                    default=fd["past_history"],
                    format_func=lambda i: f"{crop_icon(i)} {crop_name(i)}",
                    key=f"eh{f.id}",
                )
                e1, e2 = st.columns(2)
                if e1.button(T("farm.update"), key=f"eu{f.id}", type="primary", use_container_width=True):
                    ok = repo.update_farm(
                        user,
                        f.id,
                        dict(
                            name=n1.strip() or f.name,
                            crop_id=c1,
                            irrigated=ir,
                            water_availability=wv,
                            crop_history=json.dumps(hp),
                        ),
                    )
                    st.success(T("farm.updated")) if ok else st.error(T("err.generic", e="permiso"))
                if e2.button(T("farm.delete"), key=f"del{f.id}", type="secondary", use_container_width=True) and repo.delete_farm(user, f.id):
                    st.rerun()