from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from pydantic import BaseModel, Field, ValidationError, field_validator

from .formatters import format_currency, format_int

try:
    from pydantic_ai import Agent
    from pydantic_ai.exceptions import UsageLimitExceeded
    from pydantic_ai.models.google import GoogleModel
    from pydantic_ai.providers.google import GoogleProvider
    from pydantic_ai.usage import UsageLimits
except ImportError:
    Agent = None
    GoogleModel = None
    GoogleProvider = None
    UsageLimits = None

    class UsageLimitExceeded(Exception):
        pass


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
MAX_BATCH_CHARTS = 12
MAX_PROMPT_CHARS = 13_500
GEMINI_COOLDOWN_SECONDS = 300
INSIGHTS_CACHE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "processed" / "chart_insights.json"
)
DISASTER_CONTEXTS_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "reference" / "disaster_contexts.json"
)
INSIGHT_TEXT_VERSION = "v6-richer-gemini-rationale"


@dataclass(frozen=True)
class PendingChartInsight:
    placeholder: Any
    title: str
    fallback: str
    summary: str
    historical_context: str
    signature: str


class ChartInsightItem(BaseModel):
    index: int = Field(ge=0)
    insight: str = Field(min_length=60, max_length=380)


class ChartInsightBatch(BaseModel):
    insights: list[ChartInsightItem] = Field(default_factory=list)

    @field_validator("insights")
    @classmethod
    def limit_items(cls, insights: list[ChartInsightItem]) -> list[ChartInsightItem]:
        return insights[:MAX_BATCH_CHARTS]


def begin_chart_insight_batch(df: pd.DataFrame) -> None:
    st.session_state["_pending_chart_insights"] = []
    st.session_state["_chart_insight_context"] = _dataset_context(df)


def queue_chart_insight(placeholder: Any, fig: Any, fallback: str) -> None:
    pending = st.session_state.setdefault("_pending_chart_insights", [])
    context = st.session_state.get("_chart_insight_context", "")
    title = _figure_title(fig)
    summary = _chart_summary(fig)
    historical_context = _match_disaster_context(title, summary, context) or ""
    pending.append(
        PendingChartInsight(
            placeholder=placeholder,
            title=title,
            fallback=_enhance_fallback(fallback, context, historical_context),
            summary=summary,
            historical_context=historical_context,
            signature=_signature(title, summary, context, historical_context),
        )
    )


def flush_chart_insight_batch() -> None:
    pending: list[PendingChartInsight] = st.session_state.pop(
        "_pending_chart_insights", []
    )
    if not pending:
        return

    fallbacks = [item.fallback for item in pending]
    insights = generate_batch_chart_insights(pending, fallbacks)
    for item, insight in zip(pending, insights, strict=False):
        item.placeholder.markdown(
            f"<p class='chart-insight'>{insight}</p>",
            unsafe_allow_html=True,
        )


def generate_batch_chart_insights(
    charts: list[PendingChartInsight], fallbacks: list[str]
) -> list[str]:
    cached = _read_cached_insights(charts)
    missing_indexes = [index for index, insight in enumerate(cached) if not insight]
    if not missing_indexes:
        return [str(insight) for insight in cached]

    if not _can_use_gemini():
        return [
            insight or fallback for insight, fallback in zip(cached, fallbacks, strict=False)
        ]

    selected_indexes = missing_indexes[:MAX_BATCH_CHARTS]
    selected_charts = [charts[index] for index in selected_indexes]
    selected_fallbacks = [fallbacks[index] for index in selected_indexes]
    prompt = _batch_prompt(selected_charts, selected_fallbacks, selected_indexes)
    model_name = _setting("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    prompt_key = _prompt_key(prompt)

    exhausted_quota = False
    for api_key in _gemini_api_keys()[:2]:
        try:
            batch = _run_gemini_batch(prompt_key, prompt, model_name, api_key)
            results = _merge_batch_with_fallbacks(batch, charts, cached, fallbacks)
            _write_cached_insights(charts, results, fallbacks, model_name)
            return results
        except UsageLimitExceeded:
            exhausted_quota = True
        except ValidationError:
            continue
        except Exception as exc:
            if _is_rate_limit_error(exc):
                exhausted_quota = True
            continue

    if exhausted_quota:
        _cooldown_gemini("all_keys_rate_limited")
    return [
        insight or fallback for insight, fallback in zip(cached, fallbacks, strict=False)
    ]


@lru_cache(maxsize=128)
def _run_gemini_batch(
    prompt_key: str, prompt: str, model_name: str, api_key: str
) -> ChartInsightBatch:
    del prompt_key
    if (
        Agent is None
        or GoogleModel is None
        or GoogleProvider is None
        or UsageLimits is None
    ):
        raise RuntimeError("PydanticAI com provider Google não está disponível.")

    provider = GoogleProvider(api_key=api_key)
    model = GoogleModel(model_name, provider=provider)
    agent = Agent(
        model,
        output_type=ChartInsightBatch,
        instructions=(
            "Você é um analista de dados escrevendo insights para um dashboard "
            "acadêmico sobre desastres naturais no Brasil. Gere insights em "
            "português do Brasil, com uma frase por gráfico, sem markdown. "
            "Vá além de repetir o maior valor do gráfico: responda por que a "
            "observação chama atenção usando concentração, diferença para o "
            "segundo colocado, mudança temporal, sazonalidade ou contexto local "
            "curado. Use apenas os dados resumidos fornecidos. Nunca cite anos, "
            "municípios, UFs ou tragédias que não apareçam no resumo do gráfico "
            "ou no contexto histórico específico. Não afirme causalidade em "
            "cruzamentos ENSO; use leitura exploratória ou associação temporal."
        ),
        retries=1,
    )
    result = agent.run_sync(
        prompt,
        usage_limits=UsageLimits(
            request_limit=1,
            input_tokens_limit=3_800,
            output_tokens_limit=1_400,
            total_tokens_limit=5_200,
        ),
    )
    return result.output


def _batch_prompt(
    charts: list[PendingChartInsight], fallbacks: list[str], indexes: list[int]
) -> str:
    blocks: list[str] = []
    used_chars = 0
    context = st.session_state.get("_chart_insight_context", "")
    for original_index, chart, fallback in zip(indexes, charts, fallbacks, strict=False):
        block = (
            f"Gráfico {original_index}\n"
            f"{chart.summary}\n"
            f"Contexto histórico específico: {chart.historical_context or 'Sem contexto histórico específico curado para este gráfico.'}\n"
            f"Fallback local: {fallback}\n"
        )
        if used_chars + len(block) > MAX_PROMPT_CHARS:
            break
        used_chars += len(block)
        blocks.append(block)

    return (
        "Crie insights analíticos para os gráficos listados.\n"
        "Regras:\n"
        "- Retorne um objeto estruturado com a lista `insights`.\n"
        "- Cada item deve ter `index` igual ao número do gráfico e `insight`.\n"
        "- Escreva uma ou duas frases curtas, com densidade analítica.\n"
        "- Não repita apenas o dado que já está evidente no gráfico; acrescente uma hipótese explicativa segura.\n"
        "- Responda 'por que isso chama atenção?' usando apenas concentração, distância para o segundo, tendência, sazonalidade, composição territorial ou contexto histórico específico.\n"
        "- Cite no máximo um valor principal, quando ele for essencial.\n"
        "- Baseie a frase principalmente em 'Primeiro/último', 'Top valores' e 'Leitura estatística' do próprio gráfico.\n"
        "- O contexto do recorte serve para período e volume geral; não use o evento de referência do recorte para explicar um gráfico diferente.\n"
        "- Só cite tragédia, desastre histórico ou evento externo quando houver 'Contexto histórico específico' para aquele gráfico.\n"
        "- Nunca cite ano fora do período do recorte.\n"
        "- Se o fallback local ou o contexto histórico conflitar com os Top valores, siga os Top valores.\n"
        "- Não invente fatos externos; use apenas o contexto do dataset.\n"
        "- Não ultrapasse 380 caracteres por insight.\n"
        "- Se um gráfico não tiver dados suficientes, use uma observação cautelosa.\n\n"
        f"Contexto do recorte:\n{context}\n\n"
        + "\n".join(blocks)
    )


def _merge_batch_with_fallbacks(
    batch: ChartInsightBatch,
    charts: list[PendingChartInsight],
    cached: list[str | None],
    fallbacks: list[str],
) -> list[str]:
    results = [
        insight or fallback for insight, fallback in zip(cached, fallbacks, strict=False)
    ]
    for item in batch.insights:
        if 0 <= item.index < len(results):
            results[item.index] = _validate_generated_insight(
                item.insight.strip(),
                charts[item.index],
                fallbacks[item.index],
            )
    return results


def _read_cached_insights(charts: list[PendingChartInsight]) -> list[str | None]:
    cache = _load_cache()
    results: list[str | None] = []
    for chart in charts:
        entry = cache.get(chart.title)
        if (
            isinstance(entry, dict)
            and entry.get("version") == INSIGHT_TEXT_VERSION
            and entry.get("signature") == chart.signature
            and isinstance(entry.get("insight"), str)
        ):
            results.append(entry["insight"])
        else:
            results.append(None)
    return results


def _write_cached_insights(
    charts: list[PendingChartInsight],
    results: list[str],
    fallbacks: list[str],
    model_name: str,
) -> None:
    cache = _load_cache()
    wrote = False
    for chart, insight, fallback in zip(charts, results, fallbacks, strict=False):
        if insight == fallback:
            continue
        cache[chart.title] = {
            "signature": chart.signature,
            "insight": insight,
            "model": model_name,
            "version": INSIGHT_TEXT_VERSION,
            "updated_at": int(time.time()),
        }
        wrote = True
    if not wrote:
        return

    INSIGHTS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    INSIGHTS_CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _load_cache() -> dict[str, Any]:
    if not INSIGHTS_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(INSIGHTS_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _chart_summary(fig: Any) -> str:
    title = _figure_title(fig)
    points = _top_points(fig, limit=3)
    first_last = _first_last_points(fig)
    stats = _distribution_stats(fig)
    trace_names = [
        str(name)
        for trace in getattr(fig, "data", [])
        if (name := getattr(trace, "name", None))
    ][:4]

    lines = [f"Título: {title}"]
    if trace_names:
        lines.append(f"Séries/categorias: {', '.join(trace_names)}")
    if first_last:
        first_label, first_value, last_label, last_value = first_last
        lines.append(
            "Primeiro/último: "
            f"{first_label}={_format_number(first_value)}; "
            f"{last_label}={_format_number(last_value)}"
        )
    if points:
        formatted_points = "; ".join(
            f"{label}={_format_number(value)}" for label, value in points
        )
        lines.append(f"Top valores: {formatted_points}")
    if stats:
        lines.append(f"Leitura estatística: {stats}")
    return "\n".join(lines)


def _distribution_stats(fig: Any) -> str:
    points = _top_points(fig, limit=5)
    if not points:
        return ""

    values = _aggregated_points(fig)
    positive_total = sum(value for value in values.values() if value > 0)
    if positive_total <= 0:
        return ""

    leader_label, leader_value = points[0]
    parts = [
        f"{leader_label} representa {_format_percent(leader_value / positive_total)} do total visível"
    ]
    if len(points) >= 2 and points[1][1] > 0:
        second_label, second_value = points[1]
        ratio = leader_value / second_value
        gap = leader_value - second_value
        parts.append(
            f"lidera sobre {second_label} por {_format_number(gap)} "
            f"({_format_ratio(ratio)}x)"
        )
    if len(points) >= 3:
        top_three_share = sum(value for _, value in points[:3]) / positive_total
        parts.append(f"top 3 somam {_format_percent(top_three_share)}")
    return "; ".join(parts)


def _dataset_context(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sem dados para o recorte atual."

    year_min = int(df["ano_evento"].min())
    year_max = int(df["ano_evento"].max())
    records = format_int(len(df))
    municipalities = format_int(df["municipio_uf"].nunique())
    top_municipality = df["municipio_uf"].value_counts().head(1).index[0]
    top_tipology = df["descricao_tipologia"].value_counts().head(1).index[0]
    return (
        f"{year_min}-{year_max}; {records} registros em {municipalities} municípios; "
        f"município recorrente: {top_municipality}; tipologia frequente: {top_tipology}. "
        f"{_notable_event_context(df)}"
    )


def _notable_event_context(df: pd.DataFrame) -> str:
    value_columns = [
        "prejuizo_total",
        "DM_total_danos_materiais",
        "DH_total_danos_humanos_diretos",
        "DH_DESABRIGADOS",
        "DH_DESALOJADOS",
        "DH_MORTOS",
    ]
    available = [column for column in value_columns if column in df.columns]
    if not available:
        return ""

    ranked = df.assign(_event_score=df[available].fillna(0).sum(axis=1))
    row = (
        ranked.sort_values("_event_score", ascending=False).iloc[0]
        if ranked["_event_score"].max() > 0
        else df.sort_values("ano_evento").iloc[0]
    )
    value = row.get("prejuizo_total", 0)
    value_text = (
        f", com prejuízo total de {format_currency(value)}"
        if pd.notna(value) and float(value) > 0
        else ""
    )
    return (
        "Evento de referência: "
        f"{row.get('descricao_tipologia', 'evento não identificado')} "
        f"em {row.get('municipio_uf', 'município não identificado')} "
        f"no ano de {int(row.get('ano_evento', 0))}{value_text}."
    )


def _enhance_fallback(
    fallback: str, context: str, historical_context: str
) -> str:
    brief_context = _brief_context(context)
    if historical_context:
        return _limit_sentences(
            f"{fallback} Contexto provável: {_limit_sentences(historical_context, max_chars=250)}",
            max_chars=360,
        )
    context_parts = [brief_context]
    joined_context = " ".join(part for part in context_parts if part)
    if not joined_context:
        return fallback
    return _limit_sentences(f"{fallback} {joined_context}", max_chars=300)


def _match_disaster_context(title: str, summary: str, dataset_context: str) -> str | None:
    haystack = _normalize_text(f"{title} {summary}")
    year_min, year_max = _dataset_year_range(dataset_context)
    contexts = _load_disaster_contexts()
    chart_metric = _chart_metric(title)
    if chart_metric not in {
        "obitos",
        "danos",
        "prejuizo",
        "desabrigados",
        "desalojados",
        "afetados",
    }:
        return None

    matches: list[tuple[int, int, str]] = []
    for location, items in contexts.items():
        normalized_location = _normalize_text(location)
        location_score = _location_score(normalized_location, haystack)
        location_position = haystack.find(normalized_location)
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            years = [int(year) for year in item.get("years", []) if str(year).isdigit()]
            if not _years_overlap(years, year_min, year_max):
                continue
            keywords = item.get("keywords", [])
            keyword_score = sum(
                1 for keyword in keywords if _normalize_text(str(keyword)) in haystack
            )
            if not _metric_matches_keywords(chart_metric, keywords):
                continue
            year_score = sum(1 for year in years if str(year) in haystack)
            score = location_score + keyword_score + min(year_score, 2)
            summary = item.get("summary")
            if location_score == 0:
                continue
            if score >= 4 and isinstance(summary, str):
                matches.append((score, -location_position, summary))
    if not matches:
        return None
    return sorted(matches, key=lambda item: (item[0], item[1]), reverse=True)[0][2]


def _dataset_year_range(context: str) -> tuple[int | None, int | None]:
    match = re.search(r"\b(19\d{2}|20\d{2})-(19\d{2}|20\d{2})\b", context)
    if not match:
        return None, None
    year_min = int(match.group(1))
    year_max = int(match.group(2))
    return min(year_min, year_max), max(year_min, year_max)


def _years_overlap(
    years: list[int], year_min: int | None, year_max: int | None
) -> bool:
    if year_min is None or year_max is None or not years:
        return True
    return any(year_min <= year <= year_max for year in years)


def _chart_metric(title: str) -> str:
    normalized = _normalize_text(title)
    if "obito" in normalized or "morte" in normalized:
        return "obitos"
    if "dano" in normalized:
        return "danos"
    if "prejuizo" in normalized:
        return "prejuizo"
    if "desabrig" in normalized:
        return "desabrigados"
    if "desaloj" in normalized:
        return "desalojados"
    if "afetado" in normalized or "pessoas" in normalized:
        return "afetados"
    if "registro" in normalized:
        return "registros"
    return "outros"


def _metric_matches_keywords(chart_metric: str, keywords: list[Any]) -> bool:
    normalized_keywords = " ".join(_normalize_text(str(keyword)) for keyword in keywords)
    metric_terms = {
        "obitos": ["obito", "obitos", "morte", "mortes"],
        "danos": ["dano", "danos", "materiais"],
        "prejuizo": ["prejuizo", "prejuizos"],
        "desabrigados": ["desabrig"],
        "desalojados": ["desaloj"],
        "afetados": ["afetado", "afetados", "pessoas"],
    }
    return any(term in normalized_keywords for term in metric_terms.get(chart_metric, []))


def _validate_generated_insight(
    insight: str, chart: PendingChartInsight, fallback: str
) -> str:
    year_min, year_max = _dataset_year_range(
        st.session_state.get("_chart_insight_context", "")
    )
    if year_min is not None and year_max is not None:
        years = [int(year) for year in re.findall(r"\b(19\d{2}|20\d{2})\b", insight)]
        if any(year < year_min or year > year_max for year in years):
            return fallback

    normalized_insight = _normalize_text(insight)
    normalized_allowed = _normalize_text(
        f"{chart.title} {chart.summary} {chart.historical_context}"
    )
    event_terms = [
        "regiao serrana",
        "morro do bumba",
        "petropolis",
        "nova friburgo",
        "teresopolis",
        "sao sebastiao",
        "maceio",
        "rio grande do sul",
        "grande recife",
    ]
    if any(
        term in normalized_insight and term not in normalized_allowed
        for term in event_terms
    ):
        return fallback

    return insight


def _location_score(normalized_location: str, haystack: str) -> int:
    if not normalized_location:
        return 0
    if "-" in normalized_location and normalized_location in haystack:
        return 12
    if len(normalized_location) <= 2:
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_location)}(?![a-z0-9])"
        return 8 if re.search(pattern, haystack) else 0
    return 5 if normalized_location in haystack else 0


def _load_disaster_contexts() -> dict[str, Any]:
    if not DISASTER_CONTEXTS_PATH.exists():
        return {}
    try:
        return json.loads(DISASTER_CONTEXTS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _normalize_text(value: str) -> str:
    return (
        value.lower()
        .replace("í", "i")
        .replace("ó", "o")
        .replace("á", "a")
        .replace("é", "e")
        .replace("ú", "u")
        .replace("ã", "a")
        .replace("õ", "o")
        .replace("ç", "c")
    )


def _brief_context(context: str) -> str:
    if not context:
        return ""
    parts = [part.strip() for part in context.split(";") if part.strip()]
    if len(parts) >= 2:
        return f"Recorte: {parts[0]}, {parts[1]}."
    return f"Recorte: {parts[0]}." if parts else ""


def _limit_sentences(text: str, max_chars: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    truncated = compact[: max_chars - 1].rstrip()
    last_period = truncated.rfind(".")
    if last_period > 120:
        return truncated[: last_period + 1]
    return f"{truncated}."


def _top_points(fig: Any, limit: int) -> list[tuple[str, float]]:
    values = _aggregated_points(fig)
    return sorted(values.items(), key=lambda item: item[1], reverse=True)[:limit]


def _first_last_points(fig: Any) -> tuple[str, float, str, float] | None:
    points = _aggregated_points(fig)
    if len(points) < 2:
        return None
    if not all(label.isdigit() for label in points):
        return None

    def sort_key(item: tuple[str, float]) -> tuple[int, str]:
        label = item[0]
        return (int(label), label)

    ordered = sorted(points.items(), key=sort_key)
    first_label, first_value = ordered[0]
    last_label, last_value = ordered[-1]
    return first_label, first_value, last_label, last_value


def _aggregated_points(fig: Any) -> dict[str, float]:
    values: dict[str, float] = {}
    for trace in getattr(fig, "data", []):
        labels, numbers = _trace_label_value_pairs(trace)
        for label, number in zip(labels, numbers, strict=False):
            if number is None:
                continue
            try:
                numeric = float(number)
            except (TypeError, ValueError):
                continue
            label_text = str(label)
            values[label_text] = values.get(label_text, 0.0) + numeric
    return values


def _trace_label_value_pairs(trace: Any) -> tuple[list[Any], list[Any]]:
    orientation = getattr(trace, "orientation", None)
    labels = _as_list(getattr(trace, "x", []))
    values = _as_list(getattr(trace, "y", []))
    if orientation == "h":
        labels, values = values, labels
    return labels, values


def _figure_title(fig: Any) -> str:
    title = getattr(getattr(fig, "layout", None), "title", None)
    text = getattr(title, "text", None)
    return str(text or "Gráfico sem título")


def _format_number(value: float) -> str:
    return format_int(value)


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%".replace(".", ",")


def _format_ratio(value: float) -> str:
    if value >= 10:
        return format_int(value)
    return f"{value:.1f}".replace(".", ",")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)


def _can_use_gemini() -> bool:
    if Agent is None or not _gemini_api_keys():
        return False
    return time.time() >= float(st.session_state.get("_gemini_cooldown_until", 0))


def _cooldown_gemini(reason: str) -> None:
    st.session_state["_gemini_cooldown_until"] = time.time() + GEMINI_COOLDOWN_SECONDS
    st.session_state["_gemini_cooldown_reason"] = reason


def _is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        marker in message
        for marker in ["429", "rate limit", "quota", "resource_exhausted"]
    )


def _prompt_key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _signature(title: str, summary: str, context: str, historical_context: str) -> str:
    content = (
        f"{INSIGHT_TEXT_VERSION}\n{title}\n{summary}\n{context}\n"
        f"{historical_context}\n{_contexts_version()}"
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _contexts_version() -> str:
    if not DISASTER_CONTEXTS_PATH.exists():
        return "no-contexts"
    try:
        return hashlib.sha256(
            DISASTER_CONTEXTS_PATH.read_bytes()
        ).hexdigest()
    except OSError:
        return "unreadable-contexts"


def _gemini_api_keys() -> list[str]:
    keys = [
        _setting("GEMINI_API_KEY"),
        _setting("GEMINI_API_KEY_2"),
        _setting("GOOGLE_API_KEY"),
        _setting("GOOGLE_API_KEY_2"),
    ]
    deduped: list[str] = []
    for key in keys:
        if key and key not in deduped:
            deduped.append(key)
    return deduped


def _setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value.strip()
    try:
        secret_value = st.secrets.get(name, default)
    except Exception:
        secret_value = default
    return str(secret_value).strip()
