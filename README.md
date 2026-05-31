# Dashboard de Desastres Naturais no Brasil

Dashboard interativo em Streamlit para analisar registros históricos de desastres naturais no Brasil entre 1991 e 2025. O projeto cruza dados do Atlas Digital de Desastres Naturais com uma classificação anual de El Niño/La Niña, permitindo explorar registros, impactos humanos, danos materiais, prejuízos econômicos e padrões associados ao ENSO.

## Preview

> Espaço reservado para imagens da aplicação.

| Visão geral | Filtros e KPIs |
| --- | --- |
| `assets/screenshots/dashboard-overview.png` | `assets/screenshots/filters-kpis.png` |

| Gráficos e insights | Conclusões do recorte |
| --- | --- |
| `assets/screenshots/charts-insights.png` | `assets/screenshots/conclusions.png` |

Quando adicionar as imagens, substitua os caminhos acima por tags Markdown:

```md
![Visão geral do dashboard](assets/screenshots/dashboard-overview.png)
```

## Principais Recursos

- Filtros por período, região, UF, município, mês, tipologia, status e fenômeno ENSO.
- KPIs gerais, humanos, materiais e econômicos.
- Gráficos interativos com Plotly.
- Cache do dataset processado em Parquet para acelerar a abertura do app.
- Insights automáticos abaixo dos gráficos, com fallback local e geração opcional via Gemini.
- Cache local de insights em JSON para reduzir chamadas de API.
- Contextos históricos curados para enriquecer a leitura dos principais picos.
- Seção de conclusões com achados do recorte selecionado.
- Tema claro customizado e landing page estática em `index.html`.

## Stack

- Python 3.12+
- Streamlit
- Pandas
- Plotly
- Pydantic AI com provider Google Gemini
- Ruff
- Taskipy
- Docker e Docker Compose

## Estrutura

```text
frontend/
  app.py                     # Entrada do dashboard Streamlit
  components/
    ai_insights.py           # Gemini, cache e fallback dos insights
    charts.py                # Fábricas de gráficos Plotly
    cleaning.py              # Limpeza dos dados
    constants.py             # Caminhos, paletas e mapas de colunas
    data_loader.py           # Leitura dos arquivos raw
    enso.py                  # Classificação ENSO
    filters.py               # Sidebar e filtros
    insights.py              # Insights locais/fallback
    metrics.py               # Agregações e KPIs
    sections.py              # Abas/seções do dashboard
    styles.py                # CSS global do Streamlit
data/
  raw/                       # Arquivos originais
  processed/                 # Parquet e cache de insights
  reference/                 # Contextos históricos curados
notebooks/
  analise-exploratorio.ipynb # Análise exploratória de apoio metodológico
assets/
  brand/                     # Ícone/favicons
  css/, js/, figma/          # Assets da landing page
  screenshots/               # Imagens do README
```

## Dados

Coloque os arquivos abaixo em `data/raw/`:

```text
data/raw/desastres-naturais-atlas-digital.xlsx
data/raw/el_nino_la_nina_eventos_1990_2025.csv
```

O app gera automaticamente:

```text
data/processed/desastres_atlas_corrigidos_enso.parquet
data/processed/chart_insights.json
```

O Parquet acelera a abertura do dashboard e é recriado quando os arquivos raw são atualizados. O JSON guarda insights gerados para reaproveitamento quando o recorte e os dados do gráfico continuam compatíveis.

## Rodando Localmente

Instale as dependências:

```bash
uv sync
```

Inicie o dashboard com a task:

```bash
task start
```

Acesse:

```text
http://localhost:8503
```

## Tasks

Os comandos recorrentes ficam centralizados no `pyproject.toml` via Taskipy.

| Comando | Descrição |
| --- | --- |
| `task start` | Inicia o dashboard em `localhost:8503`. |
| `task lint` | Executa o Ruff para verificar qualidade de código. |
| `task format` | Aplica correções automáticas e formatação com Ruff. |
| `task test` | Executa a suíte de testes, quando houver testes no projeto. |

Para consultar as tasks disponíveis:

```bash
task --list
```

## Gemini E Insights

A IA é opcional. Sem chaves configuradas, o dashboard usa insights locais de fallback.

Para ativar o Gemini, crie `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "sua-chave-principal"
GEMINI_API_KEY_2 = "sua-chave-reserva"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

Existe um exemplo em:

```text
.streamlit/secrets.toml.example
```

A geração segue esta ordem:

1. Usa insight salvo em `data/processed/chart_insights.json`, quando o cache ainda é válido.
2. Tenta gerar insights em lote com Gemini, se as chaves estiverem configuradas.
3. Usa fallback local quando não há chave, a API retorna erro, ocorre `429` ou o limite de uso é atingido.

Os insights usam `data/reference/disaster_contexts.json` como curadoria auxiliar para explicar picos relevantes. Exemplos de contexto: enchentes no Rio Grande do Sul em 2024, tragédia da Região Serrana/RJ em 2011, cheia em Rio do Sul-SC, enchente em Iconha-ES e subsidência em Maceió-AL.

Essas notas devem ser lidas como contexto histórico provável, não como prova causal automática. Em cruzamentos ENSO, a leitura é exploratória e indica associação temporal, não causalidade.

## Docker

Build e execução:

```bash
docker compose up --build
```

Acesse:

```text
http://localhost:8503
```

O `docker-compose.yml` monta o projeto em `/app`, então alterações locais no código são refletidas no container durante o desenvolvimento.

## Landing Page

O arquivo `index.html` contém uma landing page estática para apresentação do projeto e link para o dashboard publicado.

Para visualizar localmente, abra o arquivo no navegador ou sirva a pasta com um servidor estático de sua preferência.

## Metodologia E Limitações

- Os totais dependem dos filtros selecionados.
- Municípios são exibidos com UF para evitar ambiguidade.
- A classificação ENSO é anual; comparações indicam associação temporal exploratória, não causalidade.
- Valores monetários dependem da planilha de valores corrigidos do Atlas.
- Contextos históricos em `data/reference/disaster_contexts.json` enriquecem a interpretação, mas não substituem análise causal.
- A análise exploratória permanece em `notebooks/analise-exploratorio.ipynb` como material de apoio. O fluxo atual do app não depende de script para regenerar esse notebook.

## Fontes

- Atlas Digital de Desastres Naturais no Brasil: https://atlasdigital.mdr.gov.br/paginas/index.xhtml
- Atualização do Atlas Digital pelo MIDR: https://www.gov.br/mdr/pt-br/noticias/midr-atualiza-atlas-digital-de-desastres-com-dados-consolidados-ate-2025
