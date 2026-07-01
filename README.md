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

## Commands

```bash
uv run healf-max ask "I need more energy"
uv run healf-max ask --debug "I'm training for Hyrox in 12 weeks..."
uv run healf-max bloods-demo
uv run healf-max bloods-demo --debug

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
- product category fit
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

```text
kb/
  LLM.md
  README.md
  _schemas/
  evidence/
  biomarkers/
  products/
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
- 8 product category records
- 7 editorial records
- 5 trust records
- 6 tone records
- 5 wellbeing moments
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

## Retrieval

Ingestion writes an inspectable local index:

```text
.storage/kb_index.jsonl
.storage/kb_manifest.json
.storage/kb_embeddings.npy
```

If an API key is present, ingestion attempts embeddings with `HEALF_MAX_EMBEDDING_MODEL`. If not, it writes the JSONL index and uses lexical search.

Search ranking combines:

- tag match
- title and ID match
- semantic frontmatter fields
- body keyword match
- optional embedding similarity
- `retrieval_priority`
- linked records from matched moments, biomarkers and evidence
- type-balanced trace records for editorial, trust, tone and brand context

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
- local JSONL/Numpy storage for the KB index

Public references used for direction:

- [OpenAI Responses function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [OpenAI Responses streaming](https://developers.openai.com/api/docs/guides/streaming-responses)
- [Typer](https://github.com/fastapi/typer)
- [Rich](https://github.com/Textualize/rich)
- [knowledge-rag](https://github.com/lyonzin/knowledge-rag)
- [rag-agent](https://github.com/kevwan/rag-agent)
- [Hugging Face RAG evaluation cookbook](https://huggingface.co/learn/cookbook/en/rag_evaluation)
- [SafeRAG](https://github.com/IAAR-Shanghai/SafeRAG)

## Development

```bash
uv run pytest
uv run python -m compileall healf_max
```
