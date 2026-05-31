from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import (
    REQUIRED_ATLAS_COLUMNS,
    REQUIRED_ENSO_COLUMNS,
    SHEET_ATLAS_CORRIGIDO,
)


def _ensure_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {resolved}. Coloque o arquivo em data/raw ou ajuste o caminho."
        )
    return resolved


def load_disasters_data(
    path: str | Path,
    sheet_name: str = SHEET_ATLAS_CORRIGIDO,
) -> pd.DataFrame:
    """Carrega a aba principal do Atlas preservando nomes originais."""
    resolved = _ensure_path(path)
    try:
        excel = pd.ExcelFile(resolved)
    except Exception as exc:
        raise RuntimeError(f"Não foi possível abrir o Excel {resolved}: {exc}") from exc

    if sheet_name not in excel.sheet_names:
        available = ", ".join(excel.sheet_names)
        raise ValueError(
            f"Aba '{sheet_name}' não encontrada. Abas disponíveis: {available}"
        )

    df = pd.read_excel(resolved, sheet_name=sheet_name)
    missing = REQUIRED_ATLAS_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(
            "Colunas obrigatórias ausentes no Atlas: " + ", ".join(sorted(missing))
        )
    return df


def load_enso_data(path: str | Path) -> pd.DataFrame:
    """Carrega e valida o CSV de eventos ENSO."""
    resolved = _ensure_path(path)
    df = pd.read_csv(resolved)
    missing = REQUIRED_ENSO_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(
            "Colunas obrigatórias ausentes no ENSO: " + ", ".join(sorted(missing))
        )

    invalid_signal = set(df["sinal_oni"].dropna().astype(int).unique()) - {-1, 1}
    if invalid_signal:
        raise ValueError(f"sinal_oni inválido no dado bruto: {sorted(invalid_signal)}")

    ranks = pd.to_numeric(df["intensidade_rank"], errors="coerce")
    if ranks.isna().any() or not ranks.between(1, 4).all():
        raise ValueError("intensidade_rank deve estar entre 1 e 4 no dado bruto.")

    return df
