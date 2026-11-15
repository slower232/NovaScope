"""Sources & scientific basis: the data sources the app actually uses, with official links."""
import streamlit as st

from ui.context import T, go
from ui.science import KINDS, kind_chip

# Only sources used by the code (services/nasa_power.py, services/weather_forecast.py, Folium base map)
# and methods implemented/referenced in the project (algorithms/drought_index.py, algorithms/water_balance.py, data/crops/crops.json).
# Links: official pages of NASA POWER, Open-Meteo, OpenStreetMap and FAO; the SPI overview from droughtmanagement.info (Integrated Drought Management Programme); the DOI of the Hargreaves and Samani paper.
SOURCES = [
    dict(id="power", kind="estimate", fields=("provides", "use", "limits", "license"), links=[
        ("lnk.home", "https://power.larc.nasa.gov/"),
        ("lnk.daily", "https://power.larc.nasa.gov/docs/services/api/temporal/daily/"),
        ("lnk.cite", "https://power.larc.nasa.gov/docs/referencing/")]),
    dict(id="openmeteo", kind="forecast", fields=("provides", "use", "limits", "license"), links=[
        ("lnk.home", "https://open-meteo.com/"),
        ("lnk.docs", "https://open-meteo.com/en/docs"),
        ("lnk.license", "https://open-meteo.com/en/licence"),
        ("lnk.terms", "https://open-meteo.com/en/terms")]),
    dict(id="osm", kind=None, fields=("provides", "use", "limits", "license"), links=[
        ("lnk.copyright", "https://www.openstreetmap.org/copyright")]),
]
METHODS = [
    dict(id="spi", kind="estimate", fields=("use", "limits"), links=[
        ("lnk.spi", "https://droughtmanagement.info/standardized-precipitation-index-spi/")]),
    dict(id="hargreaves", kind="estimate", fields=("use", "limits"), links=[
        ("lnk.doi", "https://doi.org/10.13031/2013.26773")]),
    dict(id="fao", kind=None, fields=("use", "limits"), links=[
        ("lnk.ecocrop", "https://ecocrop.apps.fao.org/ecocrop/srv/en/home"),
        ("lnk.cropwat", "https://www.fao.org/land-water/databases-and-software/cropwat")]),
]


def _card(item):
    sid = item["id"]
    with st.container(border=True):
        chip = " " + kind_chip(item["kind"]) if item["kind"] else ""
        st.markdown(f"#### {T(f'src.{sid}.name')}{chip}", unsafe_allow_html=True)
        for field in item["fields"]:
            st.markdown(f"**{T('sources.l.' + field)}:** {T(f'src.{sid}.{field}')}")
        st.markdown(f"**{T('sources.l.links')}**")
        links = item["links"]
        cols = st.columns(len(links) + 1)
        for col, (label, url) in zip(cols, links):
            col.link_button(T(label) + " ↗", url)  # opens the official page in a new tab


def render():
    st.button("← " + T("sources.back"), key="sources_back", on_click=go, args=("dashboard",))
    st.subheader("🔬 " + T("sources.title"))
    st.caption(T("sources.intro"))
    with st.container(border=True):
        st.markdown(f"**⚠️ {T('sources.status.title')}**")
        st.markdown(T("sources.status.body"))
    with st.container(border=True):
        st.markdown(f"**{T('sci.types.title')}**")
        for kind in KINDS:
            st.markdown(f"{kind_chip(kind)} {T('sci.kind.' + kind + '.desc')}", unsafe_allow_html=True)
    st.markdown(f"### 🛰️ {T('sources.used.title')}")
    for item in SOURCES:
        _card(item)
    st.markdown(f"### 📐 {T('sources.methods.title')}")
    st.caption(T("sources.methods.note"))
    for item in METHODS:
        _card(item)
    with st.container(border=True):
        st.markdown(f"**{T('sources.notint.title')}**")
        st.caption(T("sources.notint.body"))
    with st.container(border=True):
        st.markdown(f"**{T('sources.attr.title')}**")
        st.markdown(T("sources.attr.body"))
