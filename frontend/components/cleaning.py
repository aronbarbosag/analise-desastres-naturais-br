from __future__ import annotations

import pandas as pd

from .constants import MONTHS_PT


def clean_disasters_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Limpa dados do Atlas sem remover linhas por padrão."""
    df = df_raw.copy()

    for column in ["Data_Registro", "Data_Evento"]:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")

    string_cols = df.select_dtypes(include=["object", "string"]).columns
    for column in string_cols:
        df[column] = df[column].astype("string").str.strip()

    if "Sigla_UF" in df.columns:
        df["Sigla_UF"] = df["Sigla_UF"].astype("string").str.upper().str.strip()
    if "Nome_Municipio" in df.columns:
        df["Nome_Municipio"] = df["Nome_Municipio"].astype("string").str.strip()

    df["ano_evento"] = df["Data_Evento"].dt.year.astype("Int64")
    df["mes_evento"] = df["Data_Evento"].dt.month.astype("Int64")
    df["mes_nome"] = df["mes_evento"].map(MONTHS_PT)
    df["ano_mes_evento"] = df["Data_Evento"].dt.to_period("M").astype("string")
    df["trimestre_evento"] = "T" + df["Data_Evento"].dt.quarter.astype("Int64").astype(
        "string"
    )
    df["municipio_uf"] = (
        df["Nome_Municipio"].astype("string") + "-" + df["Sigla_UF"].astype("string")
    )

    numeric_prefixes = ("DH_", "DM_", "PEPL_", "PEPR_", "DA_")
    numeric_cols = [
        column
        for column in df.columns
        if column.startswith(numeric_prefixes) or column == "PE_PLePR"
    ]
    for column in numeric_cols:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    for column in [
        "regiao",
        "Status",
        "grupo_de_desastre",
        "descricao_tipologia",
        "tipologia",
    ]:
        if column in df.columns:
            df[column] = df[column].fillna("Sem descrição").astype("category")

    df["feridos_enfermos"] = df.get("DH_FERIDOS", 0) + df.get("DH_ENFERMOS", 0)
    df["desabrigados_desalojados"] = df.get("DH_DESABRIGADOS", 0) + df.get(
        "DH_DESALOJADOS", 0
    )
    df["prejuizo_total"] = df.get("PEPL_total_publico", 0) + df.get(
        "PEPR_total_privado", 0
    )
    df["danos_e_prejuizos_total"] = (
        df.get("DM_total_danos_materiais", 0)
        + df.get("PEPL_total_publico", 0)
        + df.get("PEPR_total_privado", 0)
    )

    return df
