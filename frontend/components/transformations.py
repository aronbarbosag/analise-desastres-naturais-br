from __future__ import annotations

from pathlib import Path

import pandas as pd

from .cleaning import clean_disasters_data
from .constants import (
    ATLAS_FILENAME,
    DATA_PROCESSED,
    DATA_RAW,
    ENSO_FILENAME,
    SHEET_ATLAS_CORRIGIDO,
)
from .data_loader import load_disasters_data, load_enso_data
from .enso import attach_enso_classification

PROCESSED_PARQUET = DATA_PROCESSED / "desastres_atlas_corrigidos_enso.parquet"


def build_dataset(
    atlas_path: str | Path | None = None,
    enso_path: str | Path | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """Processa o dataset nacional e salva parquet para acelerar o Streamlit."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    atlas = Path(atlas_path) if atlas_path else DATA_RAW / ATLAS_FILENAME
    enso = Path(enso_path) if enso_path else DATA_RAW / ENSO_FILENAME
    if (
        PROCESSED_PARQUET.exists()
        and not force
        and _processed_is_current(PROCESSED_PARQUET, [atlas, enso])
    ):
        return pd.read_parquet(PROCESSED_PARQUET)

    raw = load_disasters_data(atlas, sheet_name=SHEET_ATLAS_CORRIGIDO)
    enso_raw = load_enso_data(enso)
    clean = clean_disasters_data(raw)
    enriched = attach_enso_classification(clean, enso_raw)
    enriched.to_parquet(PROCESSED_PARQUET, index=False)
    return enriched


def _processed_is_current(processed: Path, sources: list[Path]) -> bool:
    """Evita usar parquet antigo quando os arquivos raw foram atualizados."""
    if not processed.exists():
        return False
    existing_sources = [source for source in sources if source.exists()]
    if not existing_sources:
        return True
    processed_mtime = processed.stat().st_mtime
    return all(source.stat().st_mtime <= processed_mtime for source in existing_sources)


def validate_reference_values(df: pd.DataFrame) -> dict[str, object]:
    """Checks leves para conferir consistência com a base observada na spec."""
    checks = {
        "linhas": len(df),
        "ufs": int(df["Sigla_UF"].nunique()),
        "municipios_uf": int(df["municipio_uf"].nunique()),
        "ano_min": int(df["ano_evento"].min()) if not df.empty else None,
        "ano_max": int(df["ano_evento"].max()) if not df.empty else None,
        "obitos": float(df["DH_MORTOS"].sum()),
        "danos_materiais": float(df["DM_total_danos_materiais"].sum()),
        "prejuizo_total": float(df["prejuizo_total"].sum()),
        "uf_uppercase": bool(df["Sigla_UF"].dropna().str.fullmatch(r"[A-Z]{2}").all()),
        "fenomeno_preenchido": bool(df["fenomeno_enso"].notna().all()),
    }
    return checks
