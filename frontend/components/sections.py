from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from . import charts
from .ai_insights import (
    begin_chart_insight_batch,
    flush_chart_insight_batch,
    queue_chart_insight,
)
from .formatters import format_currency, format_int
from .insights import automatic_insights, chart_insight
from .metrics import (
    agg_count,
    annual_extremes,
    annual_summary,
    cross_tab,
    damage_material_categories,
    enso_impact_by_phenomenon,
    enso_phenomenon_impact_summary,
    enso_regional_pattern_peaks,
    enso_regional_pattern_summary,
    monthly_summary,
    phenomenon_dominance_by_recorte,
    private_loss_sectors,
    public_loss_services,
    ranking,
)
from .ui import chart_container, show_kpis

DISASTER_CONTEXTS_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "reference"
    / "disaster_contexts.json"
)


def render_section(section: str, df: pd.DataFrame, kpis: dict[str, object]) -> None:
    renderers = {
        "Visão Geral": lambda: tab_overview(df, kpis),
        "Danos Humanos": lambda: tab_human(df, kpis),
        "Danos Materiais": lambda: tab_material(df, kpis),
        "Prejuízos": lambda: tab_losses(df, kpis),
        "El Niño/La Niña": lambda: tab_enso(df),
        "Conclusões": lambda: tab_conclusions(df),
        "Dados": lambda: tab_data(df),
    }
    begin_chart_insight_batch(df)
    renderers[section]()
    flush_chart_insight_batch()


def tab_overview(df: pd.DataFrame, kpis: dict[str, object]) -> None:
    show_kpis(
        kpis,
        [
            ("Registros", "total_registros", "int", "bi-bar-chart-line"),
            ("UFs afetadas", "ufs", "int", "bi-globe-americas"),
            ("Municípios", "municipios", "int", "bi-buildings"),
            ("Grupo principal", "principal_grupo", "str", "bi-diagram-3"),
            ("Tipologia principal", "principal_tipologia", "str", "bi-cloud-rain"),
            ("Prejuízo total", "prejuizo_total", "money", "bi-cash-stack"),
        ],
    )
    st.divider()
    annual = annual_summary(df)
    monthly = monthly_summary(df)
    col1, col2 = st.columns(2)
    with col1:
        plotly_chart(
            charts.line_or_bar(annual, "ano_evento", "registros", "Registros por ano")
        )
    with col2:
        plotly_chart(charts.bar(monthly, "mes_nome", "registros", "Registros por mês"))

    col1, col2 = st.columns(2)
    with col1:
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "Sigla_UF", "registros", 15),
                "registros",
                "Sigla_UF",
                "Ranking de UFs por registros",
            )
        )
    with col2:
        plotly_chart(
            charts.donut(
                agg_count(df, "grupo_de_desastre"),
                "grupo_de_desastre",
                "registros",
                "Distribuição por grupo",
            )
        )

    col1, col2 = st.columns(2)
    with col1:
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "descricao_tipologia", "registros", 12),
                "registros",
                "descricao_tipologia",
                "Tipologias mais frequentes",
            )
        )
    with col2:
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "municipio_uf", "registros", 15),
                "registros",
                "municipio_uf",
                "Municípios com mais registros",
            )
        )

    st.subheader("Resumo por município")
    st.dataframe(
        ranking(df, "municipio_uf", "registros", 50),
        use_container_width=True,
        hide_index=True,
    )
    peaks = annual_extremes(df)
    if not peaks.empty:
        peaks_display = peaks.copy()
        peaks_display["valor"] = peaks_display.apply(
            lambda row: (
                format_int(row["valor"])
                if row["metrica_original"] != "prejuizo_total"
                else format_currency(row["valor"])
            ),
            axis=1,
        )
        st.subheader("Anos de pico do recorte")
        st.dataframe(peaks_display, use_container_width=True, hide_index=True)


def tab_human(df: pd.DataFrame, kpis: dict[str, object]) -> None:
    show_kpis(
        kpis,
        [
            ("Óbitos", "obitos", "int", "bi-heart-pulse"),
            ("Feridos + enfermos", "feridos_enfermos", "int", "bi-bandaid"),
            ("Desabrigados", "desabrigados", "int", "bi-house-exclamation"),
            ("Desalojados", "desalojados", "int", "bi-arrow-left-right"),
            ("Afetados diretos", "afetados_diretos", "int", "bi-people"),
            ("Desaparecidos", "desaparecidos", "int", "bi-question-circle"),
        ],
    )
    st.caption(
        "Desabrigados são pessoas que perderam temporária ou definitivamente suas moradias e precisam de abrigo público. Desalojados são pessoas obrigadas a deixar suas casas por segurança, mas que conseguem se hospedar com familiares, amigos ou por meios próprios."
    )
    st.divider()
    annual = annual_summary(df)
    monthly = monthly_summary(df)
    for metric, title in [
        ("obitos", "Óbitos por ano"),
        ("desabrigados_desalojados", "Desabrigados + desalojados por ano"),
        ("afetados_diretos", "Afetados diretos por ano"),
    ]:
        plotly_chart(
            charts.line_or_bar(
                annual, "ano_evento", metric, title, charts.COLORS["humanos"]
            )
        )

    col1, col2 = st.columns(2)
    with col1:
        plotly_chart(
            charts.bar(
                monthly,
                "mes_nome",
                "obitos",
                "Óbitos por mês",
                charts.COLORS["humanos"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "Sigla_UF", "obitos", 15),
                "obitos",
                "Sigla_UF",
                "UFs por óbitos",
                charts.COLORS["humanos"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "municipio_uf", "afetados_diretos", 15),
                "afetados_diretos",
                "municipio_uf",
                "Municípios por afetados diretos",
                charts.COLORS["humanos"],
            )
        )
    with col2:
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "descricao_tipologia", "obitos", 15),
                "obitos",
                "descricao_tipologia",
                "Óbitos por tipologia",
                charts.COLORS["humanos"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "descricao_tipologia", "desabrigados_desalojados", 15),
                "desabrigados_desalojados",
                "descricao_tipologia",
                "Desabrigados + desalojados por tipologia",
                charts.COLORS["humanos"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "descricao_tipologia", "afetados_diretos", 15),
                "afetados_diretos",
                "descricao_tipologia",
                "Afetados diretos por tipologia",
                charts.COLORS["humanos"],
            )
        )


def tab_material(df: pd.DataFrame, kpis: dict[str, object]) -> None:
    show_kpis(
        kpis,
        [
            ("Danos materiais", "danos_materiais", "money", "bi-hammer"),
            ("Registros", "total_registros", "int", "bi-bar-chart-line"),
            ("Municípios", "municipios", "int", "bi-buildings"),
        ],
    )
    st.divider()
    annual = annual_summary(df)
    monthly = monthly_summary(df)
    col1, col2 = st.columns(2)
    with col1:
        plotly_chart(
            charts.line_or_bar(
                annual,
                "ano_evento",
                "danos_materiais",
                "Danos materiais por ano",
                charts.COLORS["materiais"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "Sigla_UF", "danos_materiais", 15),
                "danos_materiais",
                "Sigla_UF",
                "UFs por danos materiais",
                charts.COLORS["materiais"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                damage_material_categories(df),
                "danos_materiais",
                "categoria",
                "Danos materiais por categoria",
                charts.COLORS["materiais"],
            )
        )
    with col2:
        plotly_chart(
            charts.bar(
                monthly,
                "mes_nome",
                "danos_materiais",
                "Danos materiais por mês",
                charts.COLORS["materiais"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "municipio_uf", "danos_materiais", 15),
                "danos_materiais",
                "municipio_uf",
                "Municípios por danos materiais",
                charts.COLORS["materiais"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "descricao_tipologia", "danos_materiais", 15),
                "danos_materiais",
                "descricao_tipologia",
                "Danos materiais por tipologia",
                charts.COLORS["materiais"],
            )
        )


def tab_losses(df: pd.DataFrame, kpis: dict[str, object]) -> None:
    show_kpis(
        kpis,
        [
            ("Prejuízo público", "prejuizo_publico", "money", "bi-bank"),
            ("Prejuízo privado", "prejuizo_privado", "money", "bi-briefcase"),
            ("Prejuízo total", "prejuizo_total", "money", "bi-cash-stack"),
        ],
    )
    st.divider()
    annual = annual_summary(df)
    monthly = monthly_summary(df)
    col1, col2 = st.columns(2)
    with col1:
        plotly_chart(
            charts.line_or_bar(
                annual,
                "ano_evento",
                "prejuizo_publico",
                "Prejuízo público por ano",
                charts.COLORS.get("publico", charts.COLORS["prejuizo_publico"]),
            )
        )
        plotly_chart(
            charts.bar(
                monthly,
                "mes_nome",
                "prejuizo_publico",
                "Prejuízo público por mês",
                charts.COLORS.get("publico", charts.COLORS["prejuizo_publico"]),
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "Sigla_UF", "prejuizo_publico", 15),
                "prejuizo_publico",
                "Sigla_UF",
                "UFs por prejuízo público",
                charts.COLORS.get("publico", charts.COLORS["prejuizo_publico"]),
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "municipio_uf", "prejuizo_publico", 15),
                "prejuizo_publico",
                "municipio_uf",
                "Municípios por prejuízo público",
                charts.COLORS.get("publico", charts.COLORS["prejuizo_publico"]),
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                public_loss_services(df),
                "prejuizo_publico",
                "categoria",
                "Prejuízo público por serviço essencial",
                charts.COLORS.get("publico", charts.COLORS["prejuizo_publico"]),
            )
        )
    with col2:
        plotly_chart(
            charts.line_or_bar(
                annual,
                "ano_evento",
                "prejuizo_privado",
                "Prejuízo privado por ano",
                charts.COLORS.get("privado", charts.COLORS["prejuizo_privado"]),
            )
        )
        plotly_chart(
            charts.bar(
                monthly,
                "mes_nome",
                "prejuizo_privado",
                "Prejuízo privado por mês",
                charts.COLORS.get("privado", charts.COLORS["prejuizo_privado"]),
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "Sigla_UF", "prejuizo_privado", 15),
                "prejuizo_privado",
                "Sigla_UF",
                "UFs por prejuízo privado",
                charts.COLORS.get("privado", charts.COLORS["prejuizo_privado"]),
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                ranking(df, "municipio_uf", "prejuizo_privado", 15),
                "prejuizo_privado",
                "municipio_uf",
                "Municípios por prejuízo privado",
                charts.COLORS.get("privado", charts.COLORS["prejuizo_privado"]),
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                private_loss_sectors(df),
                "prejuizo_privado",
                "categoria",
                "Prejuízo privado por setor econômico",
                charts.COLORS.get("privado", charts.COLORS["prejuizo_privado"]),
            )
        )
    plotly_chart(
        charts.horizontal_bar(
            ranking(df, "descricao_tipologia", "prejuizo_total", 15),
            "prejuizo_total",
            "descricao_tipologia",
            "Prejuízo total por tipologia",
            "#334155",
        )
    )


def tab_enso(df: pd.DataFrame) -> None:
    impact = enso_phenomenon_impact_summary(df)
    if impact.empty:
        st.info("Sem dados ENSO para o recorte atual.")
        return

    st.markdown(
        "A classificação ENSO disponível neste projeto é anual. Portanto, as leituras abaixo comparam anos classificados como El Niño, La Niña ou Neutro, não dias específicos."
    )
    st.divider()

    impact_long = impact.melt(
        id_vars=["fenomeno_enso"],
        value_vars=["obitos", "desabrigados", "desalojados"],
        var_name="indicador",
        value_name="pessoas",
    )
    impact_long["indicador"] = impact_long["indicador"].replace(
        {
            "obitos": "Óbitos",
            "desabrigados": "Desabrigados",
            "desalojados": "Desalojados",
        }
    )
    plotly_chart(
        charts.grouped_bar(
            impact_long,
            "fenomeno_enso",
            "pessoas",
            "indicador",
            "Impactos humanos por tipo de ENSO",
        )
    )

    col1, col2 = st.columns(2)
    with col1:
        plotly_chart(
            charts.bar(
                impact,
                "fenomeno_enso",
                "media_anual_obitos",
                "Média anual de óbitos por tipo de ENSO",
                charts.COLORS["humanos"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                add_phenomenon_label(
                    enso_impact_by_phenomenon(df, "regiao", "obitos", 8), "regiao"
                ),
                "obitos",
                "regiao_fenomeno",
                "Combinações região/ENSO com mais óbitos",
                charts.COLORS["humanos"],
            )
        )
    with col2:
        plotly_chart(
            charts.bar(
                impact,
                "fenomeno_enso",
                "media_anual_desabrigados",
                "Média anual de desabrigados por tipo de ENSO",
                charts.COLORS["humanos"],
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                add_phenomenon_label(
                    enso_impact_by_phenomenon(df, "Sigla_UF", "desabrigados", 10),
                    "Sigla_UF",
                ),
                "desabrigados",
                "Sigla_UF_fenomeno",
                "Combinações UF/ENSO com mais desabrigados",
                charts.COLORS["humanos"],
            )
        )

    st.subheader("El Niño: seca no Norte/Nordeste e chuva no Sul")
    pattern = enso_regional_pattern_summary(df)
    if not pattern.empty:
        question_pattern = pattern[
            (
                pattern["regiao"].isin(["Norte", "Nordeste"])
                & (pattern["padrao_climatico"] == "Seca/estiagem")
            )
            | (
                (pattern["regiao"] == "Sul")
                & (pattern["padrao_climatico"] == "Chuva/enchentes")
            )
        ]
        plotly_chart(
            charts.grouped_bar(
                question_pattern,
                "recorte",
                "media_anual_registros",
                "fenomeno_enso",
                "Média anual de eventos-alvo por tipo de ENSO",
            )
        )
        plotly_chart(
            charts.grouped_bar(
                question_pattern,
                "recorte",
                "media_anual_afetados_diretos",
                "fenomeno_enso",
                "Média anual de afetados diretos nos eventos-alvo",
            )
        )

        dominance = phenomenon_dominance_by_recorte(df)
        focus_recortes = dominance[
            dominance["recorte"].isin(
                [
                    "Seca/estiagem - Norte",
                    "Seca/estiagem - Nordeste",
                    "Chuva/enchentes - Sul",
                ]
            )
        ]
        if not focus_recortes.empty:
            st.subheader("Leitura direta dos padrões")
            for _, row in focus_recortes.iterrows():
                phenomenon_runner_up = (
                    row["fenomeno_segundo"]
                    if pd.notna(row["fenomeno_segundo"])
                    else "os demais cenários"
                )
                st.markdown(
                    f"- `{row['recorte']}`: {row['fenomeno_lider']} lidera com média anual de {format_int(row['media_anual_registros_lider'])} registros, "
                    f"vantagem de {format_int(row['vantagem_media_anual'])} sobre {phenomenon_runner_up}."
                )

        peaks = enso_regional_pattern_peaks(df)
        st.subheader("Anos de pico nos eventos-alvo")
        st.dataframe(
            peaks[
                [
                    "fenomeno_enso",
                    "regiao",
                    "padrao_climatico",
                    "ano_evento",
                    "registros",
                    "afetados_diretos",
                    "desabrigados",
                    "desalojados",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Não há eventos de seca/estiagem ou chuva/enchentes para o recorte atual."
        )

    selected_metric = st.selectbox(
        "Indicador para cruzamentos ENSO",
        ["obitos", "desabrigados", "desalojados"],
        format_func={
            "obitos": "Óbitos",
            "desabrigados": "Desabrigados",
            "desalojados": "Desalojados",
        }.get,
    )

    col1, col2 = st.columns(2)
    with col1:
        plotly_chart(
            charts.heatmap(
                cross_tab(
                    df, "descricao_tipologia", "fenomeno_enso", selected_metric
                ).head(25),
                "Tipologia x tipo de ENSO",
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                add_phenomenon_label(
                    enso_impact_by_phenomenon(df, "municipio_uf", selected_metric, 12),
                    "municipio_uf",
                ),
                selected_metric,
                "municipio_uf_fenomeno",
                "Combinações município/ENSO com maior impacto",
                charts.COLORS["humanos"],
            )
        )
    with col2:
        plotly_chart(
            charts.heatmap(
                cross_tab(df, "regiao", "fenomeno_enso", selected_metric),
                "Região x tipo de ENSO",
            )
        )
        plotly_chart(
            charts.horizontal_bar(
                add_phenomenon_label(
                    enso_impact_by_phenomenon(df, "Sigla_UF", selected_metric, 12),
                    "Sigla_UF",
                ),
                selected_metric,
                "Sigla_UF_fenomeno",
                "Combinações UF/ENSO com maior impacto",
                charts.COLORS["humanos"],
            )
        )

    annual_by_enso = (
        df.groupby(["ano_evento", "fenomeno_enso"], observed=True)
        .agg(
            obitos=("DH_MORTOS", "sum"),
            desabrigados=("DH_DESABRIGADOS", "sum"),
            desalojados=("DH_DESALOJADOS", "sum"),
            afetados_diretos=("DH_total_danos_humanos_diretos", "sum"),
        )
        .reset_index()
    )
    plotly_chart(
        charts.stacked_bar(
            annual_by_enso,
            "ano_evento",
            selected_metric,
            "fenomeno_enso",
            "Série anual do indicador selecionado por tipo de ENSO",
        )
    )

    st.subheader("Resumo por tipo de ENSO")
    st.dataframe(impact, use_container_width=True, hide_index=True)

    st.subheader("Tabela anual ENSO por impacto humano")
    st.dataframe(
        annual_by_enso.sort_values(["ano_evento", "fenomeno_enso"]),
        use_container_width=True,
        hide_index=True,
    )


def tab_conclusions(df: pd.DataFrame) -> None:
    st.subheader("Conclusões gerais do recorte atual")
    for insight in automatic_insights(df):
        st.markdown(f"- {insight}")

    historical_notes = historical_context_notes(df)
    if historical_notes:
        st.subheader("Contexto histórico dos picos")
        for note in historical_notes:
            st.markdown(f"- {note}")

    st.info(
        "A leitura dos resultados deve considerar que El Niño, La Niña e anos neutros não aparecem com a mesma frequência no período analisado. Por isso, médias anuais, picos e proporções ajudam a comparar os padrões com mais equilíbrio do que apenas os totais acumulados. As notas históricas indicam contexto provável para os picos, mas não substituem uma investigação causal evento a evento."
    )


def tab_data(df: pd.DataFrame) -> None:
    st.subheader("Dados filtrados")
    st.download_button(
        "Baixar dados filtrados em CSV",
        df.to_csv(index=False).encode("utf-8-sig"),
        "desastres_filtrados.csv",
        "text/csv",
        use_container_width=True,
    )
    st.dataframe(df.head(1000), use_container_width=True, hide_index=True)

    tables = {
        "Ano": annual_summary(df),
        "UF": ranking(df, "Sigla_UF", "registros", 100),
        "Município": ranking(df, "municipio_uf", "registros", 500),
        "ENSO impactos": enso_phenomenon_impact_summary(df),
        "ENSO eventos-alvo": enso_regional_pattern_summary(df),
    }
    selected = st.selectbox("Agregação", list(tables))
    st.dataframe(tables[selected], use_container_width=True, hide_index=True)
    st.download_button(
        "Baixar agregação selecionada em CSV",
        tables[selected].to_csv(index=False).encode("utf-8-sig"),
        f"agregacao_{selected.lower()}.csv",
        "text/csv",
        use_container_width=True,
    )

    with st.expander("Dicionário resumido"):
        st.markdown(
            """
            - `Data_Evento`: data de ocorrência do desastre.
            - `Sigla_UF`, `Nome_Municipio`, `municipio_uf`: recortes territoriais.
            - `grupo_de_desastre`, `descricao_tipologia`: classificação do desastre.
            - `DH_*`: danos humanos.
            - `DM_total_danos_materiais`: danos materiais corrigidos.
            - `PEPL_total_publico`: prejuízo público corrigido.
            - `PEPR_total_privado`: prejuízo privado corrigido.
            - `fenomeno_enso`: classificação anual ENSO derivada do CSV local.
            """
        )


def plotly_chart(fig) -> None:
    chart_container(fig)
    fallback = chart_insight(fig)
    placeholder = st.empty()
    queue_chart_insight(placeholder, fig, fallback)


def add_phenomenon_label(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    labeled = df.copy()
    label = f"{dimension}_fenomeno"
    labeled[label] = (
        labeled[dimension].astype(str)
        + " ("
        + labeled["fenomeno_enso"].astype(str)
        + ")"
    )
    return labeled


def historical_context_notes(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return []

    contexts = _load_disaster_contexts()
    if not contexts:
        return []

    top_locations = _top_context_locations(df)
    if not top_locations:
        return []

    year_min = int(df["ano_evento"].min())
    year_max = int(df["ano_evento"].max())
    notes: list[str] = []
    seen: set[str] = set()
    used_locations: set[str] = set()
    for location in top_locations:
        if location in used_locations:
            continue
        for item in contexts.get(location, []):
            if not isinstance(item, dict) or not _context_intersects_years(
                item, year_min, year_max
            ):
                continue
            summary = str(item.get("summary", "")).strip()
            if not summary or summary in seen:
                continue
            notes.append(_compact_note(summary))
            seen.add(summary)
            used_locations.add(location)
            if len(notes) >= 6:
                return notes
            break
    return notes


def _top_context_locations(df: pd.DataFrame) -> list[str]:
    candidates: list[str] = []
    metric_specs = [
        ("Sigla_UF", "prejuizo_total"),
        ("Sigla_UF", "obitos"),
        ("municipio_uf", "prejuizo_total"),
        ("municipio_uf", "danos_materiais"),
        ("municipio_uf", "obitos"),
        ("Sigla_UF", "danos_materiais"),
    ]
    for group, metric in metric_specs:
        if group not in df.columns:
            continue
        top = ranking(df, group, metric, top=3)
        if top.empty or top[metric].sum() <= 0:
            continue
        candidates.extend(str(value) for value in top[group].dropna().tolist())
    return list(dict.fromkeys(candidates))


def _context_intersects_years(
    item: dict[str, Any], year_min: int, year_max: int
) -> bool:
    years = item.get("years", [])
    if not years:
        return True
    return any(year_min <= int(year) <= year_max for year in years)


def _compact_note(summary: str) -> str:
    compact = " ".join(summary.split())
    if len(compact) <= 360:
        return compact
    truncated = compact[:359].rstrip()
    last_period = truncated.rfind(".")
    if last_period > 180:
        return truncated[: last_period + 1]
    return f"{truncated}."


def _load_disaster_contexts() -> dict[str, Any]:
    if not DISASTER_CONTEXTS_PATH.exists():
        return {}
    try:
        return json.loads(DISASTER_CONTEXTS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
