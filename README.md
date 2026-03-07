# arXiv Weekly Digest

Fetches the latest ML/AI/stats papers from arxiv, filters them using Claude, and presents them in a Streamlit app.

## What it does

Every week it:
1. Pulls up to 1000 recent papers from arxiv across `cs.LG`, `cs.AI`, `cs.CL`, `cs.MA`, `stat.*`, `q-fin.*`
2. Pre-filters by venue (papers accepted at NeurIPS, ICML, ICLR, etc. are prioritised)
3. Runs a chunked Haiku pass to score relevance in batches of 50
4. Uses Sonnet to pick the final 20 most relevant papers
5. Uses Haiku to summarize each paper in plain English
6. Displays everything in a Streamlit app

## Model decisions

| Step | Model | Why |
|---|---|---|
| Chunked pre-filter | claude-haiku-4-5 | Cheap, fast — just needs to score relevance, not reason deeply |
| Final selection | claude-sonnet-4-6 | Better judgment for nuanced relevance across your specific interests |
| Summarization | claude-haiku-4-5 | Straightforward task, no need for Sonnet |

Processing 1000 papers costs roughly **$0.05–0.10 per run**.

## Setup

```bash
uv sync
cp config.yaml.example config.yaml   # then edit with your interests
```

Add your Anthropic API key to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Edit `config.yaml` with your interests and preferred venues (both are gitignored).

## Running

**One-off run:**
```bash
uv run python main.py
```

**Streamlit app:**
```bash
uv run streamlit run app.py
```

**Weekly cron job** (runs every Monday at 8am):
```
0 8 * * 1 cd /path/to/arxiv-papers && uv run python main.py
```

## Project structure

```
main.py           — pipeline: fetch → filter → select → summarize → save
arxiv_search.py   — arxiv API query
modelconnectors.py — Anthropic client setup
app.py            — Streamlit UI
config.yaml       — models, venues, personal interests (gitignored)
.env              — API key (gitignored)
results.json      — last run output (gitignored)
```
