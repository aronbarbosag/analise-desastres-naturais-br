from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path

import pandas as pd
import plotly.io as pio
import streamlit as st
from components.constants import ATLAS_FILENAME, DATA_RAW, ENSO_FILENAME
from components.filters import apply_filters
from components.insights import short_context
from components.metrics import compute_kpis
from components.sections import render_section
from components.transformations import (
    PROCESSED_PARQUET,
    build_dataset,
    validate_reference_values,
)
from components.ui import (
    apply_global_styles,
    render_section_selector,
)

os.environ.setdefault("PYTHONWARNINGS", "ignore")
warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("tornado").setLevel(logging.ERROR)

FRONTEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = FRONTEND_DIR.parent
APP_ICON = ROOT_DIR / "assets" / "brand" / "dashboard-icon.svg"

pio.templates.default = "plotly_white"

SECTIONS = [
    "Visão Geral",
    "Danos Humanos",
    "Danos Materiais",
    "Prejuízos",
    "El Niño/La Niña",
    "Conclusões",
    "Dados",
]

st.set_page_config(
    page_title="Dashboard Desastres Naturais no Brasil",
    page_icon=str(APP_ICON),
    layout="wide",
)


@st.cache_data(show_spinner="Carregando e processando dados...")
def load_data(_data_versions: tuple[tuple[str, float | None], ...]) -> pd.DataFrame:
    return build_dataset()


def data_versions() -> tuple[tuple[str, float | None], ...]:
    paths = [DATA_RAW / ATLAS_FILENAME, DATA_RAW / ENSO_FILENAME, PROCESSED_PARQUET]
    return tuple(
        (str(path), path.stat().st_mtime if path.exists() else None) for path in paths
    )


def require_data_files() -> bool:
    if PROCESSED_PARQUET.exists():
        return True

    missing = [
        str(DATA_RAW / file_name)
        for file_name in [ATLAS_FILENAME, ENSO_FILENAME]
        if not (DATA_RAW / file_name).exists()
    ]
    if not missing:
        return True

    st.error(
        "Arquivos raw não encontrados. Coloque os arquivos abaixo e reinicie o app:"
    )
    st.code("\n".join(missing), language="text")
    st.info(
        "A estrutura de código já está pronta; falta apenas posicionar os datasets originais em data/raw/."
    )
    return False


def render_header(filtered: pd.DataFrame) -> None:
    st.title("Dashboard Desastres Naturais no Brasil")
    st.markdown(
        "<p class='small-muted'>Análise nacional dos registros, impactos humanos e prejuízos econômicos entre 1991 e 2025, com recortes por território, tipologia e fenômenos ENSO.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p class='small-muted'>Fonte: Atlas Digital de Desastres Naturais no Brasil e classificação anual El Niño/La Niña.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<p class='small-muted'>Recorte atual: {short_context(filtered)}</p>",
        unsafe_allow_html=True,
    )


def render_sidebar_checks(df: pd.DataFrame) -> None:
    with st.sidebar.expander("Checks do dataset"):
        st.json(validate_reference_values(df))


def main() -> None:
    apply_global_styles()

    if not require_data_files():
        return

    df = load_data(data_versions())
    filtered = apply_filters(df)
    if filtered.empty:
        st.warning(
            "Nenhum registro encontrado para os filtros aplicados. Ajuste ou limpe os filtros para continuar."
        )
        return

    render_header(filtered)
    selected_section = render_section_selector(SECTIONS)
    render_section(selected_section, filtered, compute_kpis(filtered))
    render_sidebar_checks(df)

    st.caption(
        "Notas: totais dependem dos filtros. Municípios são exibidos com UF para evitar ambiguidade. ENSO é uma comparação exploratória, sem inferência causal."
    )


if __name__ == "__main__":
    main()
