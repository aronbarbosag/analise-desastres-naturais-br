from __future__ import annotations

from typing import Any

import pandas as pd

from .formatters import format_currency, format_int, format_percent
from .metrics import (
    annual_extremes,
    enso_impact_by_phenomenon,
    enso_phenomenon_impact_summary,
    phenomenon_dominance_by_recorte,
    enso_regional_pattern_summary,
    ranking,
    top_share,
)


def chart_insight(fig: Any) -> str:
    title = _figure_title(fig)
    lower_title = title.lower()
    top_label, top_value = _top_point(fig)

    if "por ano" in lower_title or "série anual" in lower_title:
        trend = _trend_sentence(fig)
        if trend:
            return trend
        return f"Observa-se a evolução de {title.lower()} ao longo dos anos, destacando períodos de maior e menor intensidade."

    if "por mês" in lower_title:
        if top_label and top_value is not None:
            return f"Observa-se concentração mensal em {top_label}, com {format_int(top_value)} registros no recorte selecionado."
        return f"Observa-se a distribuição mensal de {title.lower()}, útil para identificar possíveis padrões sazonais."

    if "distribuição" in lower_title:
        if top_label and top_value is not None:
            return f"Observa-se que {top_label} possui a maior participação na distribuição, com {format_int(top_value)} registros."
        return f"Observa-se como os registros se distribuem entre as categorias de {title.lower()}."

    if "prejuízo" in lower_title or "prejuizo" in lower_title:
        if top_label and top_value is not None:
            value = format_currency(top_value)
            if "tipologia" in lower_title:
                return f"A concentração em {top_label} sugere perdas econômicas recorrentes ou territorialmente amplas, somando {value} no recorte."
            if "município" in lower_title or "municipio" in lower_title:
                return f"O pico em {top_label} indica impacto econômico localizado relevante, com {value} em perdas privadas/públicas no recorte."
            if "uf" in lower_title:
                return f"O destaque de {top_label} aponta concentração territorial dos prejuízos, com {value} no recorte selecionado."
        return f"Observa-se concentração econômica em {title.lower()}, sugerindo que poucos eventos ou territórios podem responder por grande parte das perdas."

    if "ranking" in lower_title or "ufs por" in lower_title:
        if top_label and top_value is not None:
            return f"Observa-se que {top_label} lidera o ranking, com {format_value_for_title(top_value, lower_title)}."
        return f"Observa-se concentração nos primeiros itens do ranking de {title.lower()}."

    if "municípios" in lower_title or "município" in lower_title:
        if top_label and top_value is not None:
            return f"Observa-se que {top_label} se destaca entre os municípios, com {format_value_for_title(top_value, lower_title)}."
        return f"Observa-se quais municípios concentram os maiores valores em {title.lower()}."

    if "tipologia" in lower_title or "tipologias" in lower_title:
        if top_label and top_value is not None:
            return f"Observa-se que {top_label} é a tipologia de maior destaque, com {format_value_for_title(top_value, lower_title)}."
        return "Observa-se quais tipologias aparecem com maior peso no recorte selecionado."

    if "enso" in lower_title:
        if top_label and top_value is not None:
            return f"Observa-se, de forma exploratória, que {top_label} aparece com maior destaque neste cruzamento ENSO, com {format_value_for_title(top_value, lower_title)}."
        return "Observa-se uma comparação exploratória entre classificações ENSO; a leitura indica associação temporal, não causalidade."

    if "heatmap" in lower_title or " x " in lower_title:
        return f"Observa-se o cruzamento entre dimensões em {title.lower()}, facilitando a identificação de combinações mais intensas."

    if top_label and top_value is not None:
        return f"Observa-se maior destaque em {top_label}, com {format_value_for_title(top_value, lower_title)}."

    return f"Observa-se o comportamento de {title.lower()} para apoiar a leitura do recorte selecionado."


def format_value_for_title(value: float, lower_title: str) -> str:
    if any(term in lower_title for term in ["prejuízo", "danos materiais", "financeiro"]):
        return format_currency(value)
    formatted = format_int(value)
    if "óbito" in lower_title or "óbitos" in lower_title:
        return f"{formatted} óbitos"
    if "desabrig" in lower_title:
        return f"{formatted} desabrigados"
    if "desaloj" in lower_title:
        return f"{formatted} desalojados"
    if "afetados" in lower_title or "pessoas" in lower_title:
        return f"{formatted} pessoas"
    if "registro" in lower_title or "registros" in lower_title:
        return f"{formatted} registros"
    return formatted


def _figure_title(fig: Any) -> str:
    title = getattr(getattr(fig, "layout", None), "title", None)
    text = getattr(title, "text", None)
    return str(text or "este gráfico")


def _trend_sentence(fig: Any) -> str | None:
    points = _ordered_points(fig)
    if len(points) < 2:
        return None

    first_label, first_value = points[0]
    last_label, last_value = points[-1]
    if first_value == 0 and last_value == 0:
        return None

    title = _figure_title(fig).lower()
    metric = title.replace(" por ano", "").replace("série anual do ", "")
    first = format_value_for_title(first_value, title)
    last = format_value_for_title(last_value, title)
    if last_value > first_value:
        direction = "aumento"
    elif last_value < first_value:
        direction = "redução"
    else:
        direction = "estabilidade"

    return (
        f"Observa-se {direction} em {metric} entre {first_label} ({first}) "
        f"e {last_label} ({last}) no recorte selecionado."
    )


def _ordered_points(fig: Any) -> list[tuple[str, float]]:
    values: dict[str, float] = {}
    for trace in getattr(fig, "data", []):
        labels, numbers = _trace_label_value_pairs(trace)
        for label, number in zip(labels, numbers, strict=False):
            numeric_value = _to_float(number)
            if numeric_value is None:
                continue
            values[str(label)] = values.get(str(label), 0.0) + numeric_value

    def sort_key(item: tuple[str, float]) -> tuple[int, str]:
        label = item[0]
        return (int(label), label) if label.isdigit() else (10_000, label)

    return sorted(values.items(), key=sort_key)


def _top_point(fig: Any) -> tuple[str | None, float | None]:
    top_label: str | None = None
    top_value: float | None = None
    for trace in getattr(fig, "data", []):
        labels, values = _trace_label_value_pairs(trace)
        for label, value in zip(labels, values, strict=False):
            numeric_value = _to_float(value)
            if numeric_value is None:
                continue
            if top_value is None or numeric_value > top_value:
                top_label = str(label)
                top_value = numeric_value
    return top_label, top_value


def _trace_label_value_pairs(trace: Any) -> tuple[list[Any], list[Any]]:
    orientation = getattr(trace, "orientation", None)
    labels = _as_list(getattr(trace, "x", []))
    values = _as_list(getattr(trace, "y", []))
    if orientation == "h":
        labels, values = values, labels
    return labels, values


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)


def _top_sentence(
    df: pd.DataFrame, group: str, metric: str, label: str, money: bool = False
) -> str | None:
    top = ranking(df, group, metric, top=1)
    if top.empty or top[metric].sum() == 0:
        return None
    row = top.iloc[0]
    value = format_currency(row[metric]) if money else format_int(row[metric])
    return f"{row[group]} lidera em {label}, com {value}."


def automatic_insights(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["Nenhum registro foi encontrado para o recorte atual."]

    years = f"{int(df['ano_evento'].min())}–{int(df['ano_evento'].max())}"
    insights = [
        f"O recorte atual contém {format_int(len(df))} registros no período {years}.",
    ]

    priority_candidates = [
        _top_sentence(df, "Sigla_UF", "registros", "registros"),
        _top_sentence(df, "municipio_uf", "registros", "registros municipais"),
        _top_sentence(
            df, "descricao_tipologia", "registros", "tipologias por frequência"
        ),
        _top_sentence(df, "Sigla_UF", "obitos", "óbitos"),
        _top_sentence(df, "Sigla_UF", "desabrigados", "desabrigados"),
        _top_sentence(df, "Sigla_UF", "desalojados", "desalojados"),
    ]
    insights.extend([item for item in priority_candidates if item])

    annual_peaks = annual_extremes(df)
    if not annual_peaks.empty:
        row = annual_peaks[annual_peaks["metrica_original"] == "prejuizo_total"].iloc[0]
        insights.append(
            f"O maior pico financeiro ocorreu em {int(row['ano_evento'])}, com {format_currency(row['valor'])} em prejuízo total."
        )

    enso = enso_phenomenon_impact_summary(df)
    if not enso.empty:
        top_deaths = enso.sort_values("obitos", ascending=False).iloc[0]
        insights.append(
            "Na comparação exploratória por tipo de ENSO, "
            f"{top_deaths['fenomeno_enso']} concentra o maior total de óbitos "
            f"({format_int(top_deaths['obitos'])}) no recorte. Isso não indica causalidade."
        )
        top_displaced = enso.sort_values("desabrigados", ascending=False).iloc[0]
        insights.append(
            f"Para desabrigados, {top_displaced['fenomeno_enso']} aparece no topo "
            f"com {format_int(top_displaced['desabrigados'])} pessoas."
        )

    enso_tipology = enso_impact_by_phenomenon(
        df, "descricao_tipologia", "obitos", top=1
    )
    if not enso_tipology.empty:
        top = enso_tipology.sort_values("obitos", ascending=False).iloc[0]
        insights.append(
            f"A combinação tipologia/ENSO com mais óbitos é {top['descricao_tipologia']} "
            f"em anos de {top['fenomeno_enso']}, com {format_int(top['obitos'])}."
        )

    enso_uf = enso_impact_by_phenomenon(df, "Sigla_UF", "desabrigados", top=1)
    if not enso_uf.empty:
        top = enso_uf.sort_values("desabrigados", ascending=False).iloc[0]
        insights.append(
            f"Em desabrigados, o maior cruzamento UF/ENSO é {top['Sigla_UF']} "
            f"em anos de {top['fenomeno_enso']}, com {format_int(top['desabrigados'])}."
        )

    pattern = enso_regional_pattern_summary(df)
    if not pattern.empty:
        target = pattern[
            (
                pattern["regiao"].isin(["Norte", "Nordeste"])
                & (pattern["padrao_climatico"] == "Seca/estiagem")
            )
            | (
                (pattern["regiao"] == "Sul")
                & (pattern["padrao_climatico"] == "Chuva/enchentes")
            )
        ]
        el_nino_target = target[target["fenomeno_enso"] == "El Niño"]
        if not el_nino_target.empty:
            top = el_nino_target.sort_values(
                "media_anual_registros", ascending=False
            ).iloc[0]
            insights.append(
                f"Nos eventos-alvo de El Niño, o maior pico médio anual aparece em {top['recorte']}, "
                f"com {format_int(top['media_anual_registros'])} registros por ano observado."
            )

    dominance = phenomenon_dominance_by_recorte(df)
    if not dominance.empty:
        sul_rain = dominance[dominance["recorte"] == "Chuva/enchentes - Sul"]
        if not sul_rain.empty:
            row = sul_rain.iloc[0]
            insights.append(
                f"No Sul, o padrão de chuva/enchentes é mais associado a {row['fenomeno_lider']}, "
                f"com vantagem média anual de {format_int(row['vantagem_media_anual'])} registros sobre o segundo colocado."
            )

    secondary_candidates = [
        _top_sentence(df, "municipio_uf", "afetados_diretos", "afetados diretos"),
        _top_sentence(df, "Sigla_UF", "danos_materiais", "danos materiais", money=True),
        _top_sentence(df, "Sigla_UF", "prejuizo_total", "prejuízo total", money=True),
    ]
    insights.extend([item for item in secondary_candidates if item])

    share = top_share(df, "Sigla_UF", "prejuizo_total", top=5)
    if share >= 0.5:
        insights.append(
            f"As 5 UFs com maior prejuízo total concentram {format_percent(share)} do valor no recorte, indicando alta concentração territorial."
        )

    return insights[:12]


def short_context(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sem dados para os filtros aplicados."
    return (
        f"{format_int(len(df))} registros, {format_int(df['Sigla_UF'].nunique())} UFs e "
        f"{format_int(df['municipio_uf'].nunique())} municípios."
    )
