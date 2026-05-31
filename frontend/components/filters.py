from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from .constants import MONTHS_ORDER

ROOT_DIR = Path(__file__).resolve().parents[2]
APP_ICON = ROOT_DIR / "assets" / "brand" / "dashboard-icon.svg"


def reset_filters() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("filter_"):
            del st.session_state[key]


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.image(str(APP_ICON), width=64)
    st.sidebar.markdown(
        "<h2 class='sidebar-brand'>Desastres Naturais no Brasil</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.header("Filtros")
    st.sidebar.button(
        "Limpar filtros", on_click=reset_filters, use_container_width=True
    )

    min_year = int(df["ano_evento"].min())
    max_year = int(df["ano_evento"].max())
    year_range = st.sidebar.slider(
        "Intervalo de anos",
        min_year,
        max_year,
        (min_year, max_year),
        key="filter_year_range",
    )

    selected_regions = _select_regions(df)
    selected_ufs, base_for_uf = _select_ufs(df, selected_regions)
    selected_cities = _select_cities(base_for_uf, selected_ufs)

    months = st.sidebar.multiselect("Mês", MONTHS_ORDER, key="filter_months")
    groups = st.sidebar.multiselect(
        "Grupo de desastre",
        sorted(df["grupo_de_desastre"].dropna().astype(str).unique()),
        key="filter_groups",
    )
    tipologies = st.sidebar.multiselect(
        "Tipologia",
        sorted(df["descricao_tipologia"].dropna().astype(str).unique()),
        key="filter_tipologies",
    )
    statuses = st.sidebar.multiselect(
        "Status",
        sorted(df["Status"].dropna().astype(str).unique()),
        key="filter_status",
    )
    phenomena = st.sidebar.multiselect(
        "Fenômeno ENSO",
        sorted(df["fenomeno_enso"].dropna().astype(str).unique()),
        key="filter_phenomena",
    )

    filtered = df[df["ano_evento"].between(year_range[0], year_range[1])].copy()
    return _filter_dataframe(
        filtered=filtered,
        selected_regions=selected_regions,
        selected_ufs=selected_ufs,
        selected_cities=selected_cities,
        months=months,
        groups=groups,
        tipologies=tipologies,
        statuses=statuses,
        phenomena=phenomena,
    )


def _select_regions(df: pd.DataFrame) -> list[str]:
    regions = sorted(df["regiao"].dropna().astype(str).unique())
    return st.sidebar.multiselect(
        "Região",
        regions,
        key="filter_regions",
    )


def _select_ufs(
    df: pd.DataFrame, selected_regions: list[str]
) -> tuple[list[str], pd.DataFrame]:
    base_for_uf = (
        df[df["regiao"].astype(str).isin(selected_regions)] if selected_regions else df
    )
    ufs = sorted(base_for_uf["Sigla_UF"].dropna().astype(str).unique())
    selected_ufs = st.sidebar.multiselect(
        "UF",
        ufs,
        key="filter_ufs",
    )
    return selected_ufs, base_for_uf


def _select_cities(base_for_uf: pd.DataFrame, selected_ufs: list[str]) -> list[str]:
    base_for_city = (
        base_for_uf[base_for_uf["Sigla_UF"].astype(str).isin(selected_ufs)]
        if selected_ufs
        else base_for_uf
    )
    cities = sorted(base_for_city["municipio_uf"].dropna().astype(str).unique())
    return st.sidebar.multiselect("Município", cities, key="filter_cities")


def _filter_dataframe(
    filtered: pd.DataFrame,
    selected_regions: list[str],
    selected_ufs: list[str],
    selected_cities: list[str],
    months: list[str],
    groups: list[str],
    tipologies: list[str],
    statuses: list[str],
    phenomena: list[str],
) -> pd.DataFrame:
    if selected_regions:
        filtered = filtered[filtered["regiao"].astype(str).isin(selected_regions)]
    if selected_ufs:
        filtered = filtered[filtered["Sigla_UF"].astype(str).isin(selected_ufs)]
    if selected_cities:
        filtered = filtered[filtered["municipio_uf"].astype(str).isin(selected_cities)]
    if months:
        filtered = filtered[filtered["mes_nome"].astype(str).isin(months)]
    if groups:
        filtered = filtered[filtered["grupo_de_desastre"].astype(str).isin(groups)]
    if tipologies:
        filtered = filtered[
            filtered["descricao_tipologia"].astype(str).isin(tipologies)
        ]
    if statuses:
        filtered = filtered[filtered["Status"].astype(str).isin(statuses)]
    if phenomena:
        filtered = filtered[filtered["fenomeno_enso"].astype(str).isin(phenomena)]
    return filtered
