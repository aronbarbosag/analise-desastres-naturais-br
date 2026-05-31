from __future__ import annotations

from html import escape

import streamlit as st

from .formatters import format_currency, format_int
from .styles import build_styles

BOOTSTRAP_ICON_CDN = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons"


def apply_global_styles() -> None:
    if hasattr(st, "html"):
        st.html(build_styles())
        return
    st.markdown(build_styles(), unsafe_allow_html=True)


def chart_container(
    fig, title: str | None = None, use_container_width: bool = True
) -> None:
    with st.container(border=True):
        if title:
            st.markdown(f"### {title}")
        st.plotly_chart(
            fig,
            use_container_width=use_container_width,
            config={"displayModeBar": False, "responsive": True},
        )


def _icon_url(icon: str) -> str:
    icon_name = icon.strip()
    if icon_name.startswith("bi "):
        icon_name = icon_name.split()[-1]
    icon_name = icon_name.removeprefix("bi-")
    safe_icon_name = "".join(
        char for char in icon_name if char.isalnum() or char == "-"
    )
    return f"{BOOTSTRAP_ICON_CDN}/{safe_icon_name or 'circle-square'}.svg"


def kpi_card(
    label: str, value: str, help_text: str = "", icon: str = "bi-circle-square"
) -> None:
    icon_src = _icon_url(icon)
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-header">
            <div class="kpi-label">{escape(label)}</div>
            <div class="kpi-icon">
              <img class="kpi-icon-img" src="{escape(icon_src)}" alt="" loading="lazy">
            </div>
          </div>
          <div class="kpi-value">{escape(value)}</div>
          <div class="kpi-help">{escape(help_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_kpis(
    kpis: dict[str, object], cards: list[tuple[str, str, str, str | None]]
) -> None:
    cols = st.columns(len(cards), gap="small")
    for col, (label, key, kind, icon) in zip(cols, cards, strict=False):
        with col:
            raw = kpis.get(key, 0)
            value = (
                format_currency(raw)
                if kind == "money"
                else format_int(raw)
                if kind == "int"
                else str(raw)
            )
            kpi_card(label, value, icon=icon or "bi-circle-square")


def render_section_selector(sections: list[str]) -> str:
    return st.radio(
        "Seção",
        sections,
        horizontal=True,
        label_visibility="collapsed",
    )
