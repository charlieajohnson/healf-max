<p align="center">
  <img src="assets/healf-logo.jpg" alt="Healf logo" width="220">
</p>

# Healf-Max

Command-line wellbeing recommendation assistant for a D2C health and wellness brand.

Healf-Max helps customers turn body data, goals and lifestyle context into the next useful wellbeing decision. It is evidence-aware, product-aware and safety-bound, but it is not a diagnosis tool and not a supplement shopping-list generator.

## Setup

```bash
uv sync
cp .env.example .env
```

## Commands

```bash
uv run healf-max ask "I need more energy"
uv run healf-max ask --debug "I'm training for Hyrox in 12 weeks..."
uv run healf-max kb validate
uv run healf-max kb ingest
uv run healf-max bloods-demo
```

If `OPENAI_API_KEY` is missing, LLM-backed commands degrade with a clear local response rather than crashing.

## What it does

- interprets customer goals
- retrieves from a markdown-first KB
- reasons across blood markers, wearables, products, evidence and tone signals
- streams a grounded response
- stays inside wellness boundaries
- keeps biomarkers as routing constraints, not product triggers

## What it does not do

- diagnose
- prescribe
- replace a clinician or practitioner
- claim products treat medical conditions

## Example

```bash
uv run healf-max ask --debug "I'm training for Hyrox in 12 weeks, my Oura deep sleep is low, and I'm often tired. What should I look at?"
```

The useful answer shape is:

1. start with the bottleneck
2. check safety and biomarker boundaries
3. retrieve only the context needed
4. recommend narrow category lanes
5. avoid false precision and product pressure

## Knowledge base

The KB is markdown-first and split by signal type:

- `kb/moments/` for customer situations
- `kb/biomarkers/` for marker interpretation boundaries
- `kb/evidence/` for claim support
- `kb/products/` for category and product fit
- `kb/editorial/`, `kb/trust/`, and `kb/tone/` for brand-native phrasing and confidence signals

Build the local JSONL/Numpy index:

```bash
uv run healf-max kb ingest
```

Search falls back to lexical markdown search when no index exists.

## Architecture

Healf-Max uses a small explicit orchestration layer:

- Typer for the CLI
- Rich for terminal rendering
- Pydantic for typed domain models
- deterministic safety checks before the model
- OpenAI Responses API function tools for optional context retrieval
- local JSONL/Numpy storage for an inspectable KB index

Public references used for direction:

- [OpenAI Responses function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [OpenAI Responses streaming](https://developers.openai.com/api/docs/guides/streaming-responses)
- [Typer](https://github.com/fastapi/typer)
- [Rich](https://github.com/Textualize/rich)

## Development

```bash
uv run pytest
```
