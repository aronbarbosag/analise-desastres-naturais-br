from __future__ import annotations

import pandas as pd


def build_enso_year_table(df_enso: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Expande eventos sazonais para anos e resolve sobreposição por rank/intensidade."""
    expanded: list[dict[str, object]] = []
    for _, row in df_enso.iterrows():
        start = int(row["ano_inicio"])
        end = int(row["ano_fim"])
        for year in range(start, end + 1):
            expanded.append(
                {
                    "ano_evento": year,
                    "periodo_enso": row["periodo"],
                    "fenomeno_enso": row["fenomeno"],
                    "intensidade_enso": row["intensidade"],
                    "intensidade_rank_enso": int(row["intensidade_rank"]),
                    "sinal_oni": int(row["sinal_oni"]),
                    "evento_inicia_no_ano": year == start,
                }
            )

    years_df = pd.DataFrame(
        {"ano_evento": sorted(set(int(y) for y in years if pd.notna(y)))}
    )
    if not expanded:
        return _fill_neutral(years_df)

    expanded_df = pd.DataFrame(expanded).sort_values(
        ["ano_evento", "evento_inicia_no_ano", "intensidade_rank_enso"],
        ascending=[True, False, False],
    )
    expanded_df = expanded_df.drop_duplicates("ano_evento", keep="first")
    merged = years_df.merge(
        expanded_df.drop(columns=["evento_inicia_no_ano"]), on="ano_evento", how="left"
    )
    return _fill_neutral(merged)


def _fill_neutral(df: pd.DataFrame) -> pd.DataFrame:
    filled = df.copy()
    filled["periodo_enso"] = filled.get(
        "periodo_enso", pd.Series(index=filled.index)
    ).fillna("Neutro")
    filled["fenomeno_enso"] = filled.get(
        "fenomeno_enso", pd.Series(index=filled.index)
    ).fillna("Neutro")
    filled["intensidade_enso"] = filled.get(
        "intensidade_enso", pd.Series(index=filled.index)
    ).fillna("Neutro")
    filled["intensidade_rank_enso"] = (
        filled.get("intensidade_rank_enso", pd.Series(index=filled.index))
        .fillna(0)
        .astype(int)
    )
    filled["sinal_oni"] = (
        filled.get("sinal_oni", pd.Series(index=filled.index)).fillna(0).astype(int)
    )
    return filled


def attach_enso_classification(
    df_disasters: pd.DataFrame, df_enso: pd.DataFrame
) -> pd.DataFrame:
    """Adiciona classificação ENSO anual sem alterar o número de linhas."""
    original_len = len(df_disasters)
    years = df_disasters["ano_evento"].dropna().astype(int).unique().tolist()
    enso_year = build_enso_year_table(df_enso, years)
    enriched = df_disasters.merge(enso_year, on="ano_evento", how="left")
    if len(enriched) != original_len:
        raise RuntimeError("Integração ENSO alterou a quantidade de linhas.")
    for col, value in {
        "periodo_enso": "Neutro",
        "fenomeno_enso": "Neutro",
        "intensidade_enso": "Neutro",
        "intensidade_rank_enso": 0,
        "sinal_oni": 0,
    }.items():
        enriched[col] = enriched[col].fillna(value)
    return enriched
