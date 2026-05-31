from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"

ATLAS_FILENAME = "desastres-naturais-atlas-digital.xlsx"
ENSO_FILENAME = "el_nino_la_nina_eventos_1990_2025.csv"
SHEET_ATLAS_CORRIGIDO = "Atlas Valores Corrigidos"
SHEET_GRUPOS = "Grupos de Desastres"


APP_COLORS = {
    "background": "#f7fbfc",
    "surface": "#ffffff",
    "surface_soft": "#f1f7fa",
    "border": "#d7e5ec",
    "text": "#020618",
    "muted": "#5b6c78",
    "blue": "#0f5f7f",
    "teal": "#007a55",
    "amber": "#d96a1b",
    "rose": "#c2415d",
    "violet": "#5b6ea6",
    "slate": "#536879",
    "cyan": "#2f7f9f",
    "green": "#4f7f42",
}

CHART_PALETTE = [
    APP_COLORS["blue"],
    APP_COLORS["teal"],
    APP_COLORS["amber"],
    APP_COLORS["rose"],
    APP_COLORS["violet"],
    APP_COLORS["slate"],
    APP_COLORS["cyan"],
    APP_COLORS["green"],
]

ENSO_COLORS = {
    "El Niño": APP_COLORS["rose"],
    "La Niña": APP_COLORS["blue"],
    "Neutro": APP_COLORS["slate"],
}

ENSO_INTENSITY_LABELS = {
    "Neutro": "Neutro",
    "Weak": "Fraca",
    "Moderate": "Moderada",
    "Strong": "Forte",
    "Very Strong": "Muito forte",
}

DOMAIN_COLORS = {
    "registros": APP_COLORS["blue"],
    "danos_humanos": APP_COLORS["rose"],
    "danos_materiais": APP_COLORS["teal"],
    "prejuizo_publico": APP_COLORS["green"],
    "prejuizo_privado": APP_COLORS["violet"],
    "prejuizo_total": APP_COLORS["slate"],
}


MONTHS_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}
MONTHS_ORDER = list(MONTHS_PT.values())

REQUIRED_ATLAS_COLUMNS = {
    "Data_Evento",
    "Nome_Municipio",
    "Sigla_UF",
    "regiao",
    "Status",
    "grupo_de_desastre",
    "descricao_tipologia",
    "DH_MORTOS",
    "DH_FERIDOS",
    "DH_ENFERMOS",
    "DH_DESABRIGADOS",
    "DH_DESALOJADOS",
    "DH_DESAPARECIDOS",
    "DH_total_danos_humanos_diretos",
    "DM_total_danos_materiais",
    "PEPL_total_publico",
    "PEPR_total_privado",
}

REQUIRED_ENSO_COLUMNS = {
    "periodo",
    "ano_inicio",
    "ano_fim",
    "fenomeno",
    "intensidade",
    "intensidade_rank",
    "sinal_oni",
}

HUMAN_METRICS = [
    "DH_MORTOS",
    "feridos_enfermos",
    "desabrigados_desalojados",
    "DH_total_danos_humanos_diretos",
    "DH_DESAPARECIDOS",
]

MONEY_METRICS = [
    "DM_total_danos_materiais",
    "PEPL_total_publico",
    "PEPR_total_privado",
    "prejuizo_total",
]

DM_CATEGORY_MAP = {
    "DM_Uni Habita Valor": "Habitações",
    "DM_Inst Saúde Valor": "Saúde",
    "DM_Inst Ensino Valor": "Ensino",
    "DM_Inst Serviços Valor": "Serviços",
    "DM_Inst Comuni Valor": "Comunicações",
    "DM_Obras de Infra Valor": "Infraestrutura",
}

PUBLIC_LOSS_MAP = {
    "PEPL_Assis_méd e emergên(R$)": "Assistência médica e emergencial",
    "PEPL_Abast de água pot(R$)": "Abastecimento de água",
    "PEPL_sist de esgotos sanit(R$)": "Esgotamento sanitário",
    "PEPL_Sis limp e rec lixo (R$)": "Limpeza urbana e resíduos",
    "PEPL_Sis cont pragas (R$)": "Controle de pragas",
    "PEPL_distrib energia (R$)": "Distribuição de energia",
    "PEPL_Telecomunicações (R$)": "Telecomunicações",
    "PEPL_Tran loc/reg/l_curso (R$)": "Transporte",
    "PEPL_Distrib combustíveis(R$)": "Combustíveis",
    "PEPL_Segurança pública (R$)": "Segurança pública",
    "PEPL_Ensino (R$)": "Ensino",
}

PRIVATE_LOSS_MAP = {
    "PEPR_Agricultura (R$)": "Agricultura",
    "PEPR_Pecuária (R$)": "Pecuária",
    "PEPR_Indústria (R$)": "Indústria",
    "PEPR_Comércio (R$)": "Comércio",
    "PEPR_Serviços (R$)": "Serviços",
}
