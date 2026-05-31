# Dashboard de Desastres Naturais no Brasil

Dashboard interativo em Streamlit para analisar registros históricos de desastres naturais no Brasil entre 1991 e 2025. O projeto cruza dados do Atlas Digital de Desastres Naturais com uma classificação anual de El Niño/La Niña, permitindo explorar registros, impactos humanos, danos materiais, prejuízos econômicos e padrões ENSO.

## Principais Recursos

- Filtros por período, região, UF, município, mês, tipologia, status e fenômeno ENSO.
- KPIs gerais, humanos, materiais e econômicos.
- Gráficos interativos com Plotly.
- Cache de dataset processado em Parquet para acelerar o app.
- Insights automáticos abaixo dos gráficos, com fallback local e opção de geração via Gemini.
- Cache local de insights em JSON para economizar chamadas de API.
- Seção de conclusões com achados do recorte e contexto histórico dos principais picos.
- Tema claro customizado e responsivo.
- Landing page estática em `index.html`.

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
  analise-exploratorio.ipynb # Análise exploratória usada como apoio metodológico
assets/
  brand/                     # Ícone/favicons
  css/, js/, figma/          # Assets da landing page
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

O Parquet acelera a abertura do dashboard. Ele é recriado quando os arquivos raw são atualizados.

## Insights E Contexto Histórico

O dashboard mostra insights abaixo de cada gráfico. A geração segue esta ordem:

1. Usa insight salvo em `data/processed/chart_insights.json`, quando o cache ainda é válido.
2. Tenta gerar insights em lote com Gemini, se as chaves estiverem configuradas.
3. Usa fallback local quando não há chave, a API retorna erro, ocorre `429` ou o limite de uso é atingido.

O fallback é enriquecido por `data/reference/disaster_contexts.json`, que reúne eventos históricos relevantes para explicar picos do dashboard. Exemplos: enchentes no Rio Grande do Sul em 2024, tragédia da Região Serrana/RJ em 2011, cheia em Rio do Sul-SC, enchente em Iconha-ES e subsidência em Maceió-AL.

A seção **Conclusões** também consulta essa base para relacionar rankings e picos com possíveis eventos de contexto. Essas notas ajudam a interpretação, mas devem ser lidas como contexto histórico provável, não como prova causal automática.

## Configuração Do Gemini

A IA é opcional. Sem chaves, o dashboard usa os insights locais de fallback.

Para usar Gemini, crie `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "sua-chave-principal"
GEMINI_API_KEY_2 = "sua-chave-reserva"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

O app tenta a primeira chave, depois a segunda. Se houver erro, limite de cota ou código `429`, ele usa fallback local e evita novas tentativas por alguns minutos.

Existe um exemplo em:

```text
.streamlit/secrets.toml.example
```

## Rodando Localmente

Instale as dependências com `uv`:

```bash
uv sync
```

Inicie o dashboard:

```bash
uv run streamlit run frontend/app.py --server.port=8503
```

Ou use a task:

```bash
uv run task start
```

Acesse:

```text
http://localhost:8503
```

## Rodando Com Docker

Build e execução:

```bash
docker compose up --build
```

Acesse:

```text
http://localhost:8503
```

O `docker-compose.yml` monta o projeto em `/app`, então alterações locais no código são refletidas no container durante o desenvolvimento.

## Qualidade De Código

Rodar lint:

```bash
uv run ruff check .
```

Formatar:

```bash
uv run ruff format .
```

Aplicar correções automáticas:

```bash
uv run ruff check --fix .
```

## Metodologia E Limitações

- Os totais dependem dos filtros selecionados.
- Municípios são exibidos com UF para evitar ambiguidade.
- A classificação ENSO é anual; as comparações indicam associação temporal exploratória, não causalidade.
- Valores monetários dependem da planilha de valores corrigidos do Atlas.
- Contextos históricos em `data/reference/disaster_contexts.json` são uma curadoria auxiliar para enriquecer insights, não substituem análise causal.
- A análise exploratória permanece em `notebooks/analise-exploratorio.ipynb` como material de apoio. O fluxo atual do app não depende de script para regenerar esse notebook.

## Fontes

- Atlas Digital de Desastres Naturais no Brasil: https://atlasdigital.mdr.gov.br/paginas/index.xhtml
- Atualização do Atlas Digital pelo MIDR: https://www.gov.br/mdr/pt-br/noticias/midr-atualiza-atlas-digital-de-desastres-com-dados-consolidados-ate-2025
