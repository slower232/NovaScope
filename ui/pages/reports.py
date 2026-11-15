import streamlit as st
from modules.reporting.pdf_report import diagnosis_pdf
from ui.context import T, crop_name, lang


def render(user, farm, A):
    st.subheader(T("rep.title"))
    with st.container(border=True):
        srcs = [("NASA POWER (" + A["pmeta"]["resolution"] + ")") if A["power"] is not None else "NASA POWER: n/d",
                "Open-Meteo (CC BY 4.0)" if A["fc"] is not None else "Open-Meteo: n/d"]
        notes = [T("clim.warn_res"), T("water.limits")] + ([T("clim.spi_warn")] if A["spi_warn"] else [])
        pdf = diagnosis_pdf(lang(), dict(name=farm.name, lat=farm.lat, lon=farm.lon), crop_name(farm.crop_id),
                            A["risks"], A["overall"], srcs, notes)
        st.download_button(T("rep.diag"), pdf, file_name=f"novascope_{farm.id}.pdf", mime="application/pdf")
        st.caption(T("demo.none") + " · " + T("ai.title") + ": " + T("ai.na"))
