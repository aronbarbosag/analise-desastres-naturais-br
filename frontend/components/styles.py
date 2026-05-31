from __future__ import annotations


def build_styles() -> str:
    return f"""
<style>
:root {{
{_theme_variables()}
}}



html,
body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {{
  background: var(--app-bg) !important;
  color: var(--ink) !important;
}}

[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] {{
  background-color: #ffffff !important;
}}

#dashboard-desastres-naturais-no-brasil {{
  margin-top: 1.5rem;
}}

#dashboard-desastres-naturais-no-brasil h1 {{
  max-width: 920px;
  margin-bottom: 0.6rem;
}}

#dashboard-desastres-naturais-no-brasil span {{
  color: var(--primary) !important;
  font-size: clamp(2rem, 3.4vw, 3.35rem);
  line-height: 1.06;
  letter-spacing: 0;
  font-weight: 850;
}}



.block-container {{
  padding-top: 1.25rem;
  padding-bottom: 2.4rem;
  color: var(--ink) !important;
  max-width: 1380px;
}}

[data-testid="stSidebar"] {{
  background: var(--sidebar-bg) !important;
  border-right: 1px solid var(--border) !important;
}}

[data-testid="stSidebar"] * {{
  color: var(--ink) !important;
}}

.sidebar-brand {{
  margin: 0.35rem 0 1rem;
  color: var(--ink) !important;
  font-size: 1.05rem;
  line-height: 1.25;
  font-weight: 800;
}}

h1, h2, h3, h4, h5, h6,
p, span, label, div {{
  color: var(--ink);
}}

.small-muted {{
  color: var(--muted) !important;
  font-size: 0.92rem;
}}

.chart-insight {{
  margin: -0.35rem 0 1.15rem;
  padding-left: 0.25rem;
  color: var(--muted) !important;
  font-size: 0.9rem;
  line-height: 1.55;
}}

.chart-insight::before {{
  content: "Insight: ";
  color: var(--primary) !important;
  font-weight: 800;
}}

.kpi-card {{
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px;
  padding: 14px 16px 12px 16px;
  box-shadow: var(--elevation);
  min-height: 104px;
  position: relative;
  overflow: hidden;
}}

.kpi-card::before {{
  content: "";
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 4px;
  background: var(--accent-solid);
}}

.kpi-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}}

.kpi-icon {{
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--icon-bg);
  color: var(--icon-color) !important;
  font-size: 1rem;
}}

.kpi-icon-img {{
  width: 16px;
  height: 16px;
  display: block;
  opacity: .95;
}}

.kpi-label {{
  color: var(--muted) !important;
  font-size: .76rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
}}

.kpi-value {{
  color: var(--ink) !important;
  font-size: 1.22rem;
  font-weight: 800;
  line-height: 1.15;
  margin-top: 10px;
  overflow-wrap: anywhere;
}}

.kpi-help {{
  color: var(--muted) !important;
  font-size: .74rem;
  margin-top: 4px;
}}

[data-testid="stRadio"] [role="radiogroup"] {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--border);
}}

[data-testid="stRadio"] [role="radiogroup"] label {{
  border: 1px solid var(--border) !important;
  background: transparent !important;
  border-radius: 8px !important;
  padding: 0.35rem 0.7rem !important;
  box-shadow: none;
}}

[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {{
  background: var(--surface-soft) !important;
  border-color: var(--primary-soft) !important;
}}

[data-baseweb="select"],
[data-baseweb="input"],
[data-baseweb="textarea"],
[data-baseweb="base-input"],
.stTextInput input,
.stNumberInput input,
.stDateInput input {{
  background: var(--surface) !important;
  color: var(--ink) !important;
}}

[data-baseweb="select"] *,
[data-baseweb="input"] *,
[data-baseweb="textarea"] * {{
  color: var(--ink) !important;
}}

input,
textarea,
select {{
  background-color: var(--surface) !important;
  color: var(--ink) !important;
  border-color: var(--border) !important;
}}

[role="listbox"],
[data-baseweb="popover"],
[data-baseweb="menu"] {{
  background: var(--surface) !important;
  color: var(--ink) !important;
}}

[role="option"] {{
  background: var(--surface) !important;
  color: var(--ink) !important;
}}

[role="option"]:hover {{
  background: var(--surface-soft) !important;
}}

.stButton > button,
.stDownloadButton > button {{
  background: var(--surface) !important;
  color: var(--ink) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}

.stButton > button:hover,
.stDownloadButton > button:hover {{
  background: var(--surface-soft) !important;
  color: var(--primary) !important;
  border-color: var(--primary-soft) !important;
}}

[data-testid="stDataFrame"],
[data-testid="stTable"] {{
  background: var(--surface) !important;
  color: var(--ink) !important;
}}

.streamlit-expanderHeader,
[data-testid="stExpander"],
.stAlert {{
  background: var(--surface) !important;
  color: var(--ink) !important;
  border-color: var(--border) !important;
}}

code,
pre {{
  background: var(--surface-soft) !important;
  color: var(--ink) !important;
}}

[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-baseweb="select"] > div {{
  background-color: var(--surface) !important;
  color: var(--ink) !important;
  border-color: var(--border) !important;
}}

[data-baseweb="select"] span,
[data-baseweb="select"] div,
[data-baseweb="popover"] span,
[data-baseweb="popover"] div,
[data-baseweb="menu"] span,
[data-baseweb="menu"] div {{
  color: var(--ink) !important;
}}

[data-baseweb="popover"] > div,
[data-baseweb="menu"],
ul[role="listbox"] {{
  background-color: var(--surface) !important;
  color: var(--ink) !important;
  border: 1px solid var(--border) !important;
}}

li[role="option"],
div[role="option"] {{
  background-color: var(--surface) !important;
  color: var(--ink) !important;
}}

li[role="option"]:hover,
div[role="option"]:hover {{
  background-color: var(--surface-soft) !important;
  color: var(--primary) !important;
}}

[data-baseweb="tag"] {{
  background-color: var(--chip-bg) !important;
  color: var(--chip-color) !important;
}}

[data-baseweb="tag"] span {{
  color: var(--chip-color) !important;
}}

[data-testid="stSlider"] * {{
  color: var(--ink) !important;
}}

[data-testid="stSlider"] [role="slider"] {{
  background-color: var(--primary) !important;
}}

.js-plotly-plot,
.plotly,
.plot-container,
.svg-container {{
  background: transparent !important;
}}

[data-testid="stVerticalBlock"] [data-testid="stPlotlyChart"] {{
  min-height: 420px;
}}

[data-testid="stSidebar"] .stSlider,
[data-testid="stSidebar"] .stMultiSelect,
[data-testid="stSidebar"] .stSelectbox,
[data-testid="stSidebar"] .stButton {{
  margin-bottom: 0.35rem;
}}

@media (max-width: 900px) {{
  .block-container {{
    padding: 1rem 0.85rem 2rem !important;
  }}

  #panorama-dos-desastres-naturais-no-brasil {{
    margin-top: 0.75rem;
  }}

  #panorama-dos-desastres-naturais-no-brasil h1 {{
    max-width: 100%;
    margin-bottom: 0.35rem;
  }}

  #panorama-dos-desastres-naturais-no-brasil span {{
    font-size: 2.1rem;
    line-height: 1.12;
  }}

  #panorama-dos-desastres-naturais-no-brasil span::after {{
    width: 72px;
    height: 3px;
    margin-top: 0.7rem;
  }}

  .small-muted {{
    font-size: 0.88rem;
    line-height: 1.5;
  }}

  [data-testid="column"] {{
    min-width: 100% !important;
    width: 100% !important;
    flex: 1 1 100% !important;
  }}

  [data-testid="stHorizontalBlock"] {{
    flex-wrap: wrap !important;
    gap: 0.8rem !important;
  }}

  .kpi-card {{
    min-height: auto;
    padding: 13px 14px 12px;
  }}

  .kpi-value {{
    font-size: 1.08rem;
  }}

  [data-testid="stRadio"] [role="radiogroup"] {{
    gap: 0.4rem;
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 0.55rem;
  }}

  [data-testid="stRadio"] [role="radiogroup"] label {{
    flex: 0 0 auto;
    padding: 0.42rem 0.62rem !important;
    white-space: nowrap;
  }}

  [data-testid="stVerticalBlock"] [data-testid="stPlotlyChart"] {{
    min-height: 340px;
  }}

  .chart-insight {{
    margin: -0.1rem 0 1rem;
    padding-left: 0;
    font-size: 0.86rem;
    line-height: 1.5;
  }}

  [data-testid="stDataFrame"] {{
    overflow-x: auto;
  }}
}}

@media (max-width: 520px) {{
  .block-container {{
    padding-left: 0.65rem !important;
    padding-right: 0.65rem !important;
  }}

  #panorama-dos-desastres-naturais-no-brasil span {{
    font-size: 1.75rem;
  }}

  [data-testid="stVerticalBlockBorderWrapper"] {{
    padding: 0.55rem !important;
    border-radius: 10px !important;
  }}

  [data-testid="stVerticalBlock"] [data-testid="stPlotlyChart"] {{
    min-height: 300px;
  }}

  .kpi-header {{
    align-items: flex-start;
  }}

  .kpi-label {{
    font-size: 0.7rem;
  }}

  .kpi-icon {{
    width: 28px;
    height: 28px;
  }}

  .sidebar-brand {{
    font-size: 0.98rem;
  }}

  .stButton > button,
  .stDownloadButton > button {{
    min-height: 42px;
  }}
}}
</style>
"""


def _theme_variables() -> str:
    return """
  color-scheme: light !important;
  --app-bg: #f7fbfc;
  --surface: #ffffff;
  --surface-soft: #f1f7fa;
  --card: #ffffff;
  --sidebar-bg: linear-gradient(180deg, #ffffff 0%, #f7fbfc 100%);
  --border: rgba(15, 95, 127, .14);
  --muted: #5b6c78;
  --ink: #020618;
  --primary: #0f5f7f;
  --primary-soft: #9dc4ff;
  --accent-solid: #9dc4ff;
  --icon-bg: #dbeafe;
  --icon-color: #1447e6;
  --chip-bg: #eaf4ff;
  --chip-color: #1f4f78;
  --elevation: 0 12px 24px rgba(18, 31, 46, .08);
"""
