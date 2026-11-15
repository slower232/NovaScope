"""On-demand scientific explanations: help popovers and collapsible "how is this calculated?" panels.

All texts live in ui/translations (keys sci.*). Each topic explains what data are used, how the value is
calculated, what it means and its limits, and labels the type of data involved
(observation, estimate, forecast, model, farmer data).
"""
import streamlit as st

from ui.context import T, go

KINDS = ("observation", "estimate", "forecast", "model", "user")
SECTIONS = ("data", "how", "meaning", "limits")
# Types of data that each topic involves (observation is never listed: this version shows no direct observations).
TOPIC_KINDS = {
    "rec": ("estimate", "model", "user"),
    "rot": ("estimate", "model", "user"),
    "alerts": ("forecast", "estimate", "model", "user"),
    "water": ("estimate", "model", "user"),
    "env": ("forecast", "estimate", "model"),
}


def kind_chip(kind: str) -> str:
    return f'<span class="fs-kind fs-kind-{kind}">{T("sci.kind." + kind)}</span>'


def kinds_line(kinds) -> str:
    return " ".join(kind_chip(k) for k in kinds)


def _more_button(key: str):
    st.button("🔬 " + T("sci.more") + "  →", key=key, type="secondary", on_click=go, args=("sources",))


def basis_expander(topic: str):
    """Collapsed panel with the full explanation of a topic; keeps the first view simple."""
    with st.expander("ℹ️ " + T("sci.basis.title")):
        for sec in SECTIONS:
            st.markdown(f"**{T('sci.section.' + sec)}**")
            st.markdown(T(f"sci.{topic}.{sec}"))
        st.markdown(f"**{T('sci.types')}:** " + kinds_line(TOPIC_KINDS[topic]), unsafe_allow_html=True)
        _more_button(f"sci_more_{topic}")


def help_icon(topic: str, key: str):
    """Small ℹ️ button that opens a short explanation (popover)."""
    with st.popover("ℹ️", help=T("sci.help")):
        st.markdown(f"**{T('sci.help')}**")
        st.markdown(T(f"sci.{topic}.short"))
        st.markdown(kinds_line(TOPIC_KINDS[topic]), unsafe_allow_html=True)
        _more_button(f"sci_more_{key}")


def rec_item_help(index, n_years, verified: bool, key: str):
    """Popover for one crop recommendation: what its score is made of and the catalogue status."""
    with st.popover("ℹ️", help=T("sci.help")):
        st.markdown(f"**{T('sci.help')}**")
        if index is not None:
            st.markdown(T("sci.rec.item", idx=index, n=n_years, farmer=T("sci.rec.item.farmer")))
        else:
            st.markdown(T("sci.rec.short"))
        st.caption(T("sci.rec.item.verified") if verified else T("sci.rec.item.unverified"))
        st.markdown(kinds_line(TOPIC_KINDS["rec"]), unsafe_allow_html=True)
        _more_button(f"sci_more_{key}")
