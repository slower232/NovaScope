"""NovaScope — run with: streamlit run app.py"""
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import streamlit as st
st.set_page_config(page_title="NovaScope", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

from authentication import auth
from database import repositories as repo
from database.initialization import init_db
from ui.context import PAGES, T, analyze, crop_name
from ui.crop_visuals import crop_icon
from ui.pages import alerts, dashboard, environment, farms, recommendations, reports, sources, water
from ui.styles import CSS
from ui.translations import LANGS

st.markdown(CSS, unsafe_allow_html=True)
init_db()
st.session_state.setdefault("lang", "en")
st.session_state.setdefault("page", "dashboard")
st.session_state.setdefault("show_account_modal", False)


def _t(key: str, en: str, es: str, **kw) -> str:
    """Safely resolves translation keys with bilingual fallback."""
    try:
        val = T(key, **kw)
        if val and val != key:
            return val
    except Exception:
        pass
    base = es if st.session_state.get("lang", "en") == "es" else en
    return base.format(**kw) if kw else base


def _ensure_guest_farmer():
    """Automatically creates/logs into a local producer profile so no login wall blocks the user."""
    if "uid" in st.session_state:
        return
    default_u, default_p = "producer", "novascope2026"
    try:
        if repo.count_users() == 0:
            auth.create_first_admin(default_u, default_p)
        user = auth.login(default_u, default_p)
        if not user:
            auth.register(default_u, default_p, "farmer", st.session_state.get("lang", "en"))
            user = auth.login(default_u, default_p)
        if user:
            st.session_state.update(uid=user.id, uname=user.username, role=user.role, is_guest=True)
            return
    except Exception:
        pass
    st.session_state.update(uid=1, uname="Producer", role="farmer", is_guest=True)


def header():
    brand, spacer, lang_col, acct_col = st.columns([3.8, 4.4, 1.3, 1.3], vertical_alignment="center")
    with brand:
        mark, title_box = st.columns([0.45, 2.2], vertical_alignment="center")
        mark.image("assets/novascope-emblem.png", width=44)
        title_box.markdown(
            f'<div class="fs-brand">NovaScope</div>'
            f'<div class="fs-tagline">{_t("app.tagline", "Simple satellite guidance for your fields", "Guía satelital sencilla para tus parcelas")}</div>',
            unsafe_allow_html=True,
        )
    with lang_col:
        st.selectbox(T("lang"), list(LANGS), format_func=LANGS.get, key="lang", label_visibility="collapsed")
    with acct_col:
        btn_label = _t("ui.account", "👤 Account", "👤 Cuenta") if not st.session_state.get("show_account_modal") else _t("ui.close", "✕ Close", "✕ Cerrar")
        if st.button(btn_label, use_container_width=True, key="toggle_account"):
            st.session_state["show_account_modal"] = not st.session_state["show_account_modal"]
            st.rerun()


def optional_account_panel():
    with st.container(border=True):
        st.markdown(f"#### 👤 {_t('ui.account_title', 'Optional Producer Account', 'Cuenta opcional de productor')}")
        st.caption(_t("ui.account_note", "You can use NovaScope immediately without an account. Sign in only if you want to switch profiles.", "Puedes usar NovaScope de inmediato sin crear cuenta. Inicia sesión solo si deseas cambiar de perfil."))
        tab_in, tab_reg = st.tabs([T("login"), T("register")])
        with tab_in, st.form("login_opt"):
            u = st.text_input(T("username"))
            p = st.text_input(T("password"), type="password")
            if st.form_submit_button(T("login"), type="primary"):
                user = auth.login(u, p)
                if user:
                    st.session_state.update(uid=user.id, uname=user.username, role=user.role, is_guest=False, show_account_modal=False)
                    st.rerun()
                st.error(T("err.login"))
        with tab_reg, st.form("register_opt"):
            u = st.text_input(T("username"), key="ru")
            p = st.text_input(T("password"), type="password", key="rp")
            role = st.selectbox(T("role"), ["farmer", "advisor"], format_func=lambda r: T("role." + r))
            if st.form_submit_button(T("register")):
                try:
                    auth.register(u, p, role, st.session_state["lang"])
                    st.success("OK")
                except Exception as e:
                    st.error(T("err.generic", e=e))


def render_step_bar(current_page: str, has_farms: bool):
    """Visual 4-step workflow bar tailored to the farmer's journey."""
    step_map = {
        "farms": 1,
        "dashboard": 2,
        "water": 2,
        "alerts": 2,
        "environment": 2,
        "recommendations": 3,
        "rotation": 3,
        "reports": 4,
    }
    active_step = step_map.get(current_page, 2 if has_farms else 1)
    steps = [
        (1, _t("flow.step1", "1. Register Parcel", "1. Registrar Parcela")),
        (2, _t("flow.step2", "2. Field Diagnosis", "2. Diagnóstico")),
        (3, _t("flow.step3", "3. Crop Rotation & Advice", "3. Rotación y Consejos")),
        (4, _t("flow.step4", "4. PDF Report", "4. Reporte PDF")),
    ]
    parts = []
    for idx, (num, label) in enumerate(steps):
        cls = "fs-step fs-step-active" if num == active_step else ("fs-step fs-step-done" if num < active_step and has_farms else "fs-step")
        parts.append(f'<span class="{cls}">{label}</span>')
        if idx < len(steps) - 1:
            parts.append('<span class="fs-step-arrow">→</span>')
    st.markdown(f'<div class="fs-flow-wrap">{"".join(parts)}</div>', unsafe_allow_html=True)


_ensure_guest_farmer()
header()

if st.session_state.get("show_account_modal"):
    optional_account_panel()

page = st.session_state.get("page", "dashboard")
if page == "rotation":
    st.session_state["page"] = page = "recommendations"
    st.session_state["recommendation_view"] = "rotation"

user = type("U", (), {"id": st.session_state["uid"], "role": st.session_state["role"]})()
farm_list = repo.list_farms(user)

# Si el productor aún no tiene parcelas, lo llevamos directo al paso 1 (Registrar Parcela)
if not farm_list and page not in ("farms", "sources"):
    st.session_state["page"] = page = "farms"
    st.session_state["farms_view"] = "new"

render_step_bar(page, bool(farm_list))

# Navegación principal limpia + Selector de Parcela
active_parent = {"farms": "dashboard", "water": "dashboard", "alerts": "dashboard", "reports": None, "sources": None}.get(page, page)
nav_icons = {"dashboard": "🏠", "recommendations": "🧭", "environment": "🌤️"}

nav_cols = st.columns([1.15, 1.25, 1.25, 2.35] if farm_list else [1, 1, 1], gap="small", vertical_alignment="center")
for col, nav_page in zip(nav_cols[:3], PAGES):
    with col:
        st.button(
            f"{nav_icons[nav_page]}  {T('nav.' + nav_page)}",
            key=f"nav_{nav_page}",
            type="primary" if active_parent == nav_page else "secondary",
            use_container_width=True,
            on_click=lambda p=nav_page: st.session_state.update(page=p),
        )

if farm_list:
    with nav_cols[3]:
        by_id = {f.id: f for f in farm_list}
        default_id = st.session_state.get("farm_id", farm_list[0].id)
        if default_id not in by_id:
            default_id = farm_list[0].id
        fid = st.selectbox(
            T("farm.select"),
            list(by_id),
            index=list(by_id).index(default_id),
            key="farm_id",
            format_func=lambda i: f"{crop_icon(by_id[i].crop_id)} {by_id[i].name} · {crop_name(by_id[i].crop_id)}",
            label_visibility="collapsed",
        )
else:
    fid = None

page = st.session_state.get("page", "dashboard")

if page == "sources":
    sources.render()
elif page == "farms":
    farms.render(user, farm_list)
elif not farm_list:
    farms.render(user, farm_list)
else:
    by_id = {f.id: f for f in farm_list}
    farm = by_id[fid]
    with st.spinner(T("loading")):
        A = analyze(farm)
    if page == "dashboard":
        dashboard.render(user, farm_list, farm, A)
    elif page == "recommendations":
        recommendations.render(user, farm, A)
    elif page == "environment":
        environment.render(user, farm, A)
    elif page == "water":
        water.render(user, farm, A)
    elif page == "alerts":
        alerts.render(user, farm, A)
    elif page == "reports":
        reports.render(user, farm, A)

st.divider()
foot_reports, foot_sources, _ = st.columns([1.4, 2.2, 8.4], vertical_alignment="center")
with foot_reports:
    st.button(
        T("nav.reports"),
        icon="📄",
        key="footer_reports",
        type="primary" if page == "reports" else "secondary",
        on_click=lambda: st.session_state.update(page="reports"),
    )
with foot_sources:
    st.button(
        T("nav.sources"),
        icon="🔬",
        key="footer_sources",
        type="primary" if page == "sources" else "secondary",
        on_click=lambda: st.session_state.update(page="sources"),
    )
st.caption(T("limits"))