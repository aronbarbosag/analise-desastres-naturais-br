from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .constants import CHART_PALETTE, ENSO_COLORS

COLORS = {
    "registros": CHART_PALETTE[0],
    "humanos": CHART_PALETTE[1],
    "materiais": CHART_PALETTE[2],
    "prejuizo_publico": CHART_PALETTE[3],
    "prejuizo_privado": CHART_PALETTE[4],
    "prejuizo_total": CHART_PALETTE[5],
}

CURRENT_THEME = {
    "paper_bgcolor": "#ffffff",
    "plot_bgcolor": "#ffffff",
    "font_color": "#020618",
    "axis_color": "#5b6c78",
    "grid_color": "#e4edf2",
    "line_color": "#d7e5ec",
}


def apply_default_layout(fig, title=None, height=420):
    fig.update_layout(
        template="plotly_white",
        title=title,
        height=height,
        paper_bgcolor=CURRENT_THEME["paper_bgcolor"],
        plot_bgcolor=CURRENT_THEME["plot_bgcolor"],
        font=dict(
            color=CURRENT_THEME["font_color"],
            family="Arial, sans-serif",
            size=13,
        ),
        title_font=dict(
            color=CURRENT_THEME["font_color"],
            size=17,
            family="Arial, sans-serif",
        ),
        colorway=CHART_PALETTE,
        legend=dict(
            bgcolor="rgba(255,255,255,0)",
            font=dict(color=CURRENT_THEME["font_color"]),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(
            color=CURRENT_THEME["font_color"],
            gridcolor=CURRENT_THEME["grid_color"],
            zerolinecolor=CURRENT_THEME["grid_color"],
            linecolor=CURRENT_THEME["line_color"],
            tickfont=dict(color=CURRENT_THEME["axis_color"]),
            title="",
            title_font=dict(color=CURRENT_THEME["axis_color"]),
        ),
        yaxis=dict(
            color=CURRENT_THEME["font_color"],
            gridcolor=CURRENT_THEME["grid_color"],
            zerolinecolor=CURRENT_THEME["grid_color"],
            linecolor=CURRENT_THEME["line_color"],
            tickfont=dict(color=CURRENT_THEME["axis_color"]),
            title="",
            title_font=dict(color=CURRENT_THEME["axis_color"]),
        ),
        margin=dict(l=16, r=16, t=64, b=24),
    )

    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None)
    return fig


def bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str = COLORS["registros"],
    height: int = 420,
) -> go.Figure:
    fig = px.bar(df, x=x, y=y, title=title, text_auto=".2s")
    fig.update_traces(marker_color=color, textposition="outside", cliponaxis=False)
    return apply_default_layout(fig, title=title, height=height)


def horizontal_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str = COLORS["registros"],
    height: int | None = None,
) -> go.Figure:
    data = df.sort_values(x, ascending=True)
    fig = px.bar(data, x=x, y=y, orientation="h", title=title, text_auto=".2s")
    fig.update_traces(marker_color=color, textposition="outside", cliponaxis=False)
    final_height = height or max(360, min(620, 110 + 24 * len(data)))
    return apply_default_layout(fig, title=title, height=final_height)


def line_or_bar(
    df: pd.DataFrame, x: str, y: str, title: str, color: str = COLORS["registros"]
) -> go.Figure:
    if len(df) > 18:
        fig = px.line(df, x=x, y=y, markers=True, title=title)
        fig.update_traces(
            line_color=color,
            marker_color=color,
            line_width=3,
            marker_size=7,
        )
    else:
        fig = px.bar(df, x=x, y=y, title=title, text_auto=".2s")
        fig.update_traces(marker_color=color)
    return apply_default_layout(fig, title=title, height=420)


def donut(df: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    fig = px.pie(df, names=names, values=values, hole=0.62, title=title)
    fig.update_traces(textposition="inside", textinfo="percent", sort=False)
    return apply_default_layout(fig, title=title, height=420)


def stacked_bar(
    df: pd.DataFrame, x: str, y: str, color_col: str, title: str
) -> go.Figure:
    fig = px.bar(
        df, x=x, y=y, color=color_col, title=title, color_discrete_map=ENSO_COLORS
    )
    return apply_default_layout(fig, title=title, height=420)


def grouped_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color_col: str,
    title: str,
    height: int = 420,
) -> go.Figure:
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color_col,
        barmode="group",
        title=title,
        text_auto=".2s",
        color_discrete_map=ENSO_COLORS,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return apply_default_layout(fig, title=title, height=height)


def heatmap(df: pd.DataFrame, title: str) -> go.Figure:
    if df.empty or len(df.columns) <= 1:
        fig = go.Figure()
        fig.update_layout(title=title)
        return apply_default_layout(fig, title=title)
    index_col = df.columns[0]
    plot_df = df.set_index(index_col)
    fig = px.imshow(plot_df, aspect="auto", title=title, color_continuous_scale="Blues")
    return apply_default_layout(fig, title=title, height=420)
