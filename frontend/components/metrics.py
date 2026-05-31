from __future__ import annotations

import pandas as pd

from .constants import DM_CATEGORY_MAP, MONTHS_ORDER, PRIVATE_LOSS_MAP, PUBLIC_LOSS_MAP

HUMAN_IMPACT_METRICS = {
    "obitos": "DH_MORTOS",
    "desabrigados": "DH_DESABRIGADOS",
    "desalojados": "DH_DESALOJADOS",
    "desabrigados_desalojados": "desabrigados_desalojados",
    "afetados_diretos": "DH_total_danos_humanos_diretos",
}

ENSO_ORDER = ["El Niño", "La Niña", "Neutro"]
DRY_TIPOLOGIES = {"Estiagem e Seca"}
RAIN_TIPOLOGIES = {"Chuvas Intensas", "Enxurradas", "Inundações", "Alagamentos"}


def compute_kpis(df: pd.DataFrame) -> dict[str, float | int | str]:
    if df.empty:
        return {
            "total_registros": 0,
            "ufs": 0,
            "municipios": 0,
            "principal_grupo": "Sem dados",
            "principal_tipologia": "Sem dados",
            "obitos": 0,
            "feridos_enfermos": 0,
            "desabrigados": 0,
            "desalojados": 0,
            "desabrigados_desalojados": 0,
            "afetados_diretos": 0,
            "desaparecidos": 0,
            "danos_materiais": 0.0,
            "prejuizo_publico": 0.0,
            "prejuizo_privado": 0.0,
            "prejuizo_total": 0.0,
        }
    return {
        "total_registros": int(len(df)),
        "ufs": int(df["Sigla_UF"].nunique()),
        "municipios": int(df["municipio_uf"].nunique()),
        "principal_grupo": _top_label(df, "grupo_de_desastre"),
        "principal_tipologia": _top_label(df, "descricao_tipologia"),
        "obitos": float(df["DH_MORTOS"].sum()),
        "feridos_enfermos": float(df["feridos_enfermos"].sum()),
        "desabrigados": float(df["DH_DESABRIGADOS"].sum()),
        "desalojados": float(df["DH_DESALOJADOS"].sum()),
        "desabrigados_desalojados": float(df["desabrigados_desalojados"].sum()),
        "afetados_diretos": float(df["DH_total_danos_humanos_diretos"].sum()),
        "desaparecidos": float(df["DH_DESAPARECIDOS"].sum()),
        "danos_materiais": float(df["DM_total_danos_materiais"].sum()),
        "prejuizo_publico": float(df["PEPL_total_publico"].sum()),
        "prejuizo_privado": float(df["PEPR_total_privado"].sum()),
        "prejuizo_total": float(df["prejuizo_total"].sum()),
    }


def _top_label(df: pd.DataFrame, column: str) -> str:
    counts = df[column].dropna().value_counts()
    return "Sem dados" if counts.empty else str(counts.index[0])


def agg_count(
    df: pd.DataFrame, group_cols: str | list[str], name: str = "registros"
) -> pd.DataFrame:
    cols = [group_cols] if isinstance(group_cols, str) else group_cols
    if df.empty:
        return pd.DataFrame(columns=cols + [name])
    return (
        df.groupby(cols, observed=True)
        .size()
        .reset_index(name=name)
        .sort_values(name, ascending=False)
    )


def agg_sum(
    df: pd.DataFrame,
    group_cols: str | list[str],
    value_col: str,
    name: str | None = None,
) -> pd.DataFrame:
    cols = [group_cols] if isinstance(group_cols, str) else group_cols
    out_name = name or value_col
    if df.empty:
        return pd.DataFrame(columns=cols + [out_name])
    return (
        df.groupby(cols, observed=True)[value_col]
        .sum()
        .reset_index(name=out_name)
        .sort_values(out_name, ascending=False)
    )


def annual_summary(df: pd.DataFrame) -> pd.DataFrame:
    return _summary_by(df, "ano_evento").sort_values("ano_evento")


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = _summary_by(df, ["mes_evento", "mes_nome"])
    if out.empty:
        return out
    out["mes_nome"] = pd.Categorical(out["mes_nome"], MONTHS_ORDER, ordered=True)
    return out.sort_values("mes_evento")


def _summary_by(df: pd.DataFrame, group_cols: str | list[str]) -> pd.DataFrame:
    cols = [group_cols] if isinstance(group_cols, str) else group_cols
    if df.empty:
        return pd.DataFrame(columns=cols)
    return (
        df.groupby(cols, observed=True)
        .agg(
            registros=("Protocolo_S2iD", "count")
            if "Protocolo_S2iD" in df.columns
            else ("ano_evento", "count"),
            obitos=("DH_MORTOS", "sum"),
            feridos_enfermos=("feridos_enfermos", "sum"),
            desabrigados=("DH_DESABRIGADOS", "sum"),
            desalojados=("DH_DESALOJADOS", "sum"),
            desabrigados_desalojados=("desabrigados_desalojados", "sum"),
            afetados_diretos=("DH_total_danos_humanos_diretos", "sum"),
            danos_materiais=("DM_total_danos_materiais", "sum"),
            prejuizo_publico=("PEPL_total_publico", "sum"),
            prejuizo_privado=("PEPR_total_privado", "sum"),
            prejuizo_total=("prejuizo_total", "sum"),
        )
        .reset_index()
    )


def ranking(
    df: pd.DataFrame,
    group_col: str | list[str],
    metric: str = "registros",
    top: int = 15,
) -> pd.DataFrame:
    if metric == "registros":
        out = agg_count(df, group_col, metric)
    else:
        source = _metric_source(metric)
        out = agg_sum(df, group_col, source, metric)
    return out.head(top)


def _metric_source(metric: str) -> str:
    mapping = {
        "obitos": "DH_MORTOS",
        "desabrigados": "DH_DESABRIGADOS",
        "desalojados": "DH_DESALOJADOS",
        "afetados_diretos": "DH_total_danos_humanos_diretos",
        "desabrigados_desalojados": "desabrigados_desalojados",
        "danos_materiais": "DM_total_danos_materiais",
        "prejuizo_publico": "PEPL_total_publico",
        "prejuizo_privado": "PEPR_total_privado",
        "prejuizo_total": "prejuizo_total",
    }
    return mapping.get(metric, metric)


def distribution_from_columns(
    df: pd.DataFrame, mapping: dict[str, str], value_name: str
) -> pd.DataFrame:
    rows = []
    for col, label in mapping.items():
        if col in df.columns:
            rows.append({"categoria": label, value_name: float(df[col].sum())})
    return (
        pd.DataFrame(rows).sort_values(value_name, ascending=False)
        if rows
        else pd.DataFrame(columns=["categoria", value_name])
    )


def damage_material_categories(df: pd.DataFrame) -> pd.DataFrame:
    return distribution_from_columns(df, DM_CATEGORY_MAP, "danos_materiais")


def public_loss_services(df: pd.DataFrame) -> pd.DataFrame:
    return distribution_from_columns(df, PUBLIC_LOSS_MAP, "prejuizo_publico")


def private_loss_sectors(df: pd.DataFrame) -> pd.DataFrame:
    return distribution_from_columns(df, PRIVATE_LOSS_MAP, "prejuizo_privado")


def enso_comparison(df: pd.DataFrame, by: str = "fenomeno_enso") -> pd.DataFrame:
    out = _summary_by(df, by)
    if out.empty:
        return out
    annual_by = _summary_by(df, ["ano_evento", by])
    mean_records = (
        annual_by.groupby(by, observed=True)["registros"]
        .mean()
        .reset_index(name="media_anual_registros")
    )
    return out.merge(mean_records, on=by, how="left").sort_values(
        "registros", ascending=False
    )


def enso_phenomenon_impact_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Resume impactos humanos por tipo de ENSO."""
    columns = [
        "fenomeno_enso",
        "anos_observados",
        "registros",
        "obitos",
        "desabrigados",
        "desalojados",
        "afetados_diretos",
        "media_anual_obitos",
        "media_anual_desabrigados",
        "media_anual_desalojados",
        "media_anual_afetados_diretos",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)
    summary = (
        df.groupby("fenomeno_enso", observed=True)
        .agg(
            anos_observados=("ano_evento", "nunique"),
            registros=("ano_evento", "count"),
            obitos=("DH_MORTOS", "sum"),
            desabrigados=("DH_DESABRIGADOS", "sum"),
            desalojados=("DH_DESALOJADOS", "sum"),
            afetados_diretos=("DH_total_danos_humanos_diretos", "sum"),
        )
        .reset_index()
    )
    for metric in ["obitos", "desabrigados", "desalojados", "afetados_diretos"]:
        summary[f"media_anual_{metric}"] = summary[metric] / summary[
            "anos_observados"
        ].clip(lower=1)
    summary["fenomeno_enso"] = pd.Categorical(
        summary["fenomeno_enso"], ENSO_ORDER, ordered=True
    )
    return summary.sort_values("fenomeno_enso").reset_index(drop=True)


def enso_impact_by_phenomenon(
    df: pd.DataFrame, dimension: str, metric: str, top: int = 20
) -> pd.DataFrame:
    """Ranking de dimensão por fenômeno ENSO para um indicador."""
    if df.empty:
        return pd.DataFrame(columns=["fenomeno_enso", dimension, metric])
    source = _metric_source(metric)
    grouped = (
        df.groupby(["fenomeno_enso", dimension], observed=True)[source]
        .sum()
        .reset_index(name=metric)
    )
    grouped = grouped[grouped[metric] > 0]
    if grouped.empty:
        return grouped
    return (
        grouped.sort_values(["fenomeno_enso", metric], ascending=[True, False])
        .groupby("fenomeno_enso", observed=True)
        .head(top)
        .reset_index(drop=True)
    )


def enso_regional_pattern_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compara seca/estiagem e chuva/enchentes em regiões-chave por tipo de ENSO."""
    if df.empty:
        return pd.DataFrame(
            columns=[
                "fenomeno_enso",
                "regiao",
                "padrao_climatico",
                "anos_observados",
                "registros",
                "obitos",
                "desabrigados",
                "desalojados",
                "afetados_diretos",
                "media_anual_registros",
                "media_anual_afetados_diretos",
                "recorte",
            ]
        )

    pattern_df = df[
        df["regiao"].isin(["Norte", "Nordeste", "Sul"])
        & df["descricao_tipologia"].isin(DRY_TIPOLOGIES | RAIN_TIPOLOGIES)
    ].copy()
    if pattern_df.empty:
        return pd.DataFrame()

    pattern_df["padrao_climatico"] = pattern_df["descricao_tipologia"].astype(str)
    pattern_df.loc[
        pattern_df["descricao_tipologia"].isin(DRY_TIPOLOGIES), "padrao_climatico"
    ] = "Seca/estiagem"
    pattern_df.loc[
        pattern_df["descricao_tipologia"].isin(RAIN_TIPOLOGIES), "padrao_climatico"
    ] = "Chuva/enchentes"

    summary = (
        pattern_df.groupby(
            ["fenomeno_enso", "regiao", "padrao_climatico"], observed=True
        )
        .agg(
            anos_observados=("ano_evento", "nunique"),
            registros=("ano_evento", "count"),
            obitos=("DH_MORTOS", "sum"),
            desabrigados=("DH_DESABRIGADOS", "sum"),
            desalojados=("DH_DESALOJADOS", "sum"),
            afetados_diretos=("DH_total_danos_humanos_diretos", "sum"),
        )
        .reset_index()
    )
    summary["media_anual_registros"] = summary["registros"] / summary[
        "anos_observados"
    ].clip(lower=1)
    summary["media_anual_afetados_diretos"] = summary["afetados_diretos"] / summary[
        "anos_observados"
    ].clip(lower=1)
    summary["recorte"] = (
        summary["padrao_climatico"].astype(str) + " - " + summary["regiao"].astype(str)
    )
    return summary.sort_values(["recorte", "fenomeno_enso"]).reset_index(drop=True)


def enso_regional_pattern_peaks(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica anos de pico para seca/estiagem e chuva/enchentes por região."""
    if df.empty:
        return pd.DataFrame()
    pattern_df = df[
        df["regiao"].isin(["Norte", "Nordeste", "Sul"])
        & df["descricao_tipologia"].isin(DRY_TIPOLOGIES | RAIN_TIPOLOGIES)
    ].copy()
    if pattern_df.empty:
        return pd.DataFrame()
    pattern_df["padrao_climatico"] = pattern_df["descricao_tipologia"].astype(str)
    pattern_df.loc[
        pattern_df["descricao_tipologia"].isin(DRY_TIPOLOGIES), "padrao_climatico"
    ] = "Seca/estiagem"
    pattern_df.loc[
        pattern_df["descricao_tipologia"].isin(RAIN_TIPOLOGIES), "padrao_climatico"
    ] = "Chuva/enchentes"
    annual = (
        pattern_df.groupby(
            ["fenomeno_enso", "regiao", "padrao_climatico", "ano_evento"],
            observed=True,
        )
        .agg(
            registros=("ano_evento", "count"),
            obitos=("DH_MORTOS", "sum"),
            desabrigados=("DH_DESABRIGADOS", "sum"),
            desalojados=("DH_DESALOJADOS", "sum"),
            afetados_diretos=("DH_total_danos_humanos_diretos", "sum"),
        )
        .reset_index()
    )
    return (
        annual.sort_values("registros", ascending=False)
        .groupby(["fenomeno_enso", "regiao", "padrao_climatico"], observed=True)
        .head(1)
        .sort_values(["padrao_climatico", "regiao", "fenomeno_enso"])
        .reset_index(drop=True)
    )


def annual_extremes(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna os anos de maior intensidade para indicadores centrais do recorte."""
    annual = annual_summary(df)
    if annual.empty:
        return pd.DataFrame(
            columns=["indicador", "ano_evento", "valor", "metrica_original"]
        )

    rows = []
    metric_labels = {
        "registros": "Mais registros",
        "obitos": "Mais óbitos",
        "afetados_diretos": "Mais afetados diretos",
        "prejuizo_total": "Maior prejuízo total",
    }
    for metric, label in metric_labels.items():
        peak = annual.sort_values(metric, ascending=False).iloc[0]
        rows.append(
            {
                "indicador": label,
                "ano_evento": int(peak["ano_evento"]),
                "valor": float(peak[metric]),
                "metrica_original": metric,
            }
        )
    return pd.DataFrame(rows)


def phenomenon_dominance_by_recorte(df: pd.DataFrame) -> pd.DataFrame:
    """Resume qual fenômeno ENSO lidera cada recorte-chave de seca e chuva."""
    pattern = enso_regional_pattern_summary(df)
    if pattern.empty:
        return pd.DataFrame()

    dominant = (
        pattern.sort_values("media_anual_registros", ascending=False)
        .groupby("recorte", observed=True)
        .head(1)
        .copy()
    )
    dominant = dominant.rename(
        columns={
            "fenomeno_enso": "fenomeno_lider",
            "media_anual_registros": "media_anual_registros_lider",
            "media_anual_afetados_diretos": "media_anual_afetados_lider",
        }
    )

    runner_up = (
        pattern.sort_values("media_anual_registros", ascending=False)
        .groupby("recorte", observed=True)
        .nth(1)
        .reset_index()[["recorte", "fenomeno_enso", "media_anual_registros"]]
        .rename(
            columns={
                "fenomeno_enso": "fenomeno_segundo",
                "media_anual_registros": "media_anual_registros_segundo",
            }
        )
    )
    out = dominant.merge(runner_up, on="recorte", how="left")
    out["vantagem_media_anual"] = out["media_anual_registros_lider"] - out[
        "media_anual_registros_segundo"
    ].fillna(0)
    return out.sort_values("recorte").reset_index(drop=True)


def enso_intensity_impact_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Resume impactos humanos por intensidade ENSO, com totais e médias anuais."""
    columns = [
        "intensidade_enso",
        "anos_observados",
        "obitos",
        "desabrigados",
        "desalojados",
        "afetados_diretos",
        "intensidade_rank_enso",
        "media_anual_obitos",
        "media_anual_desabrigados",
        "media_anual_desalojados",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)

    summary = (
        df.groupby("intensidade_enso", observed=True)
        .agg(
            anos_observados=("ano_evento", "nunique"),
            obitos=("DH_MORTOS", "sum"),
            desabrigados=("DH_DESABRIGADOS", "sum"),
            desalojados=("DH_DESALOJADOS", "sum"),
            afetados_diretos=("DH_total_danos_humanos_diretos", "sum"),
            intensidade_rank_enso=("intensidade_rank_enso", "max"),
        )
        .reset_index()
    )
    for metric in ["obitos", "desabrigados", "desalojados"]:
        summary[f"media_anual_{metric}"] = summary[metric] / summary[
            "anos_observados"
        ].clip(lower=1)
    return summary.sort_values("intensidade_rank_enso").reset_index(drop=True)


def enso_impact_by(
    df: pd.DataFrame, dimension: str, metric: str, top: int = 20
) -> pd.DataFrame:
    """Ranking de uma dimensão por intensidade ENSO para um indicador humano."""
    if df.empty:
        return pd.DataFrame(columns=["intensidade_enso", dimension, metric])
    source = _metric_source(metric)
    grouped = (
        df.groupby(["intensidade_enso", dimension], observed=True)[source]
        .sum()
        .reset_index(name=metric)
    )
    grouped = grouped[grouped[metric] > 0]
    if grouped.empty:
        return grouped
    return (
        grouped.sort_values(["intensidade_enso", metric], ascending=[True, False])
        .groupby("intensidade_enso", observed=True)
        .head(top)
        .reset_index(drop=True)
    )


def cross_tab(
    df: pd.DataFrame, index: str, columns: str, values: str = "registros"
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    if values == "registros":
        table = pd.pivot_table(
            df,
            index=index,
            columns=columns,
            values="ano_evento",
            aggfunc="count",
            fill_value=0,
            observed=True,
        )
    else:
        table = pd.pivot_table(
            df,
            index=index,
            columns=columns,
            values=_metric_source(values),
            aggfunc="sum",
            fill_value=0,
            observed=True,
        )
    return table.reset_index()


def top_share(df: pd.DataFrame, group_col: str, metric: str, top: int = 5) -> float:
    out = ranking(df, group_col, metric, top=10_000)
    if out.empty or out[metric].sum() == 0:
        return 0.0
    return float(out.head(top)[metric].sum() / out[metric].sum())
