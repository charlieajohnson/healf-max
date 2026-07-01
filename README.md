<p align="center">
  <img src="assets/healf-logo.jpg" alt="Healf logo" width="220">
</p>

# Healf-Max

Command-line wellbeing recommendation assistant for a D2C UK health and wellness brand.

Healf-Max helps customers turn body data, goals, lifestyle context and curated product knowledge into the next useful wellbeing decision. It is evidence-aware, brand-native and commercially useful, but it is not a diagnosis tool and not a supplement shopping-list generator.

## Setup

```bash
uv sync
cp .env.example .env
```

Populate `.env` when you want live OpenAI-backed answers and embeddings:

```bash
OPENAI_API_KEY=
HEALF_MAX_MODEL=gpt-5.5-2026-04-23
HEALF_MAX_EMBEDDING_MODEL=text-embedding-3-small
HEALF_MAX_KB_DIR=kb
HEALF_MAX_STORAGE_DIR=.storage
HEALF_MAX_STREAM=true
```

If `OPENAI_API_KEY` is missing, LLM-backed commands degrade with a clear local response rather than crashing.

## Try This First

The flagship demo is the quickest way to see the intended behaviour:

```bash
uv run healf-max bloods-demo
```

It works without an API key by using deterministic synthetic Bloods, wearable and goal context.

## Commands

```bash
uv run healf-max bloods-demo
uv run healf-max bloods-demo --debug
uv run healf-max bloods-demo --json
uv run healf-max bloods-demo --profile data/synthetic_bloods_results.yaml

uv run healf-max ask "I need more energy"
uv run healf-max ask --debug "I'm training for Hyrox in 12 weeks..."

uv run healf-max kb validate
uv run healf-max kb validate --strict
uv run healf-max kb ingest
uv run healf-max kb search "low ferritin tired hyrox deep sleep"
```

## Product Shape

Healf-Max is a wellbeing decision layer. It combines:

- customer goals and posture
- deterministic safety classification
- synthetic customer, bloods and wearable context for demos
- typed markdown KB records
- evidence claims
- biomarker routing
- wearable trend routing
- product category fit
- dated product catalogue snapshots
- Healf editorial, trust, tone and brand signals

The answer shape is deliberately narrow:

1. punchy interpretation
2. what matters most
3. product or category lanes worth comparing
4. what not to overdo
5. safety or follow-up boundary
6. one useful follow-up question when needed

## Knowledge Base

The KB is markdown-first and split into small, traceable records with typed YAML frontmatter.

The design is inspired by Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern: compile raw source material once into durable, agent-readable Markdown pages rather than re-deriving meaning from loose chunks on every question. Healf-Max adapts that idea for a D2C wellness assistant by adding typed frontmatter, safety boundaries, linked records and a local hybrid retrieval layer.

```text
kb/
  LLM.md
  README.md
  _schemas/
  evidence/
  biomarkers/
  signals/
  products/
    catalogue/
  editorial/
  trust/
  tone/
  moments/
  examples/
  brand/
```

Every active record includes:

```yaml
id: ferritin_low_fatigue
type: evidence_claim
title: Ferritin, fatigue and training tolerance
status: active
retrieval_priority: 10
reviewed_at: "2026-07-01"
```

Health-related records also include:

```yaml
safety_boundary: []
prohibited_claims: []
```

The current corpus includes:

- 10 evidence records
- 6 biomarker records
- 1 wearable signal record
- 15 product category records
- 20 dated product records from the supplied Healf Best Sellers snapshot
- 8 editorial records
- 5 trust records
- 6 tone records
- 6 wellbeing moments
- 4 example records
- 5 supplied Healf brand records
- schema docs for the record types

## Brand Context

The `kb/brand/` records convert the supplied Healf source files into retrievable brand context:

- `brand.context_pack`
- `brand.story`
- `brand.quiz`
- `brand.zone`
- `brand.topics`

These records shape voice, personalisation and commercial framing. They do not establish medical evidence or live stock, price or delivery truth.

## Product Catalogue

The `kb/products/` layer now has two levels:

- `product_category` records define durable lanes such as creatine, electrolytes, magnesium, omega-3, longevity support and gut health support.
- `product` records under `kb/products/catalogue/` are dated Healf Best Sellers snapshots pulled from the supplied 2026-06-30 source files.

Product records link back to category records through `category_routes`; categories link forward through `catalogue_products`. This keeps concrete product retrieval useful without letting price, stock, review count or delivery metadata become live truth.

## Bloods Flagship Demo

Run:

```bash
uv run healf-max bloods-demo
uv run healf-max bloods-demo --debug
uv run healf-max bloods-demo --json
```

This demo uses synthetic Bloods and wearable data to show how Healf-Max can produce a proactive wellbeing check-in.

The synthetic customer is training for Hyrox in 12 weeks and has low ferritin, low vitamin D, suboptimal magnesium, low deep sleep and HRV below baseline.

The assistant prioritises follow-up and category-level support. It does not diagnose, prescribe, or turn abnormal blood results into a shopping list.

## Retrieval

Ingestion writes an inspectable local index:

```text
.storage/kb_index.jsonl
.storage/kb_manifest.json
.storage/kb_graph.json
.storage/kb_embeddings.npy
```

If an API key is present, ingestion attempts embeddings with `HEALF_MAX_EMBEDDING_MODEL`. If not, it writes the JSONL index and uses lexical search.

Search ranking combines:

- fielded Markdown/frontmatter matches
- BM25 over each compiled record
- tag match
- title and ID match
- semantic frontmatter fields
- body keyword match
- optional embedding similarity
- `retrieval_priority`
- graph-hop expansion from matched moments, biomarkers, evidence, wearable signals and product categories
- type-balanced trace records for wearable, editorial, trust, tone and brand context

Search output is grouped by record type and shows why each record was retrieved.

## Safety

Healf-Max keeps biomarkers as routing constraints, not product triggers.

It does not:

- diagnose
- prescribe
- replace a clinician or practitioner
- claim products treat medical conditions
- turn abnormal blood results into a shopping list
- cite editorial, influencer, trust or brand signals as medical evidence

Urgent symptoms, medication interactions, pregnancy or child-related contexts, and diagnosis requests stop product recommendations and route to appropriate human review.

## Architecture

Healf-Max uses a small explicit orchestration layer:

- Typer for the CLI
- Rich for terminal rendering
- Pydantic for typed domain models
- deterministic safety checks before the model
- OpenAI Responses API function tools for optional context retrieval
- local JSONL/Numpy/JSON graph storage for the KB index

Public references used for direction:

- [Andrej Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [OpenAI Responses function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [OpenAI Responses streaming](https://developers.openai.com/api/docs/guides/streaming-responses)
- [Typer](https://github.com/fastapi/typer)
- [Rich](https://github.com/Textualize/rich)
- [knowledge-rag](https://github.com/lyonzin/knowledge-rag)
- [rag-agent](https://github.com/kevwan/rag-agent)
- [Kwipu local Markdown Graph RAG](https://github.com/benmaster82/Kwipu)
- [GraphRAG Hybrid](https://github.com/rileylemm/graphrag-hybrid)
- [Hugging Face RAG evaluation cookbook](https://huggingface.co/learn/cookbook/en/rag_evaluation)
- [SafeRAG](https://github.com/IAAR-Shanghai/SafeRAG)
- [NIH ODS Iron](https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/)
- [NIH ODS Magnesium](https://ods.od.nih.gov/factsheets/Magnesium-HealthProfessional/)
- [NHS Vitamin B12 diagnosis](https://www.nhs.uk/conditions/vitamin-b12-or-folate-deficiency-anaemia/diagnosis/)
- [NHS Vitamin D](https://www.nhs.uk/conditions/vitamins-and-minerals/vitamin-d/)
- [Oura Readiness Score](https://ouraring.com/blog/readiness-score/)
- [HYROX race format](https://hyrox.com/the-fitness-race/)

## Development

```bash
uv run pytest
uv run python -m compileall healf_max
```
