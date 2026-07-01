# Healf-Max Knowledge Base

Markdown-first records with typed YAML frontmatter. The corpus is deliberately split into small, traceable records so retrieval can combine evidence, biomarkers, product lanes, brand voice and safety boundaries without collapsing them into one blob.

## Structure

- `_schemas/` - record-shape examples and validation notes
- `evidence/` - ingredient, practice and plain-language evidence claims
- `biomarkers/` - marker interpretation and action routing
- `products/` - category-first commercial lanes
- `editorial/` - Healf-style editorial frames
- `trust/` - customer confidence and service signals
- `tone/` - reusable response language
- `moments/` - pre-modelled wellbeing situations
- `examples/` - regression/evaluation examples
- `brand/` - supplied Healf brand source context

## Rules

Every active record needs `id`, `type`, `title`, `status`, `retrieval_priority`, and `reviewed_at`. Health-related records also need `safety_boundary` and `prohibited_claims`.

Wellbeing moments may link to `evidence_routes`, `product_lanes`, `editorial_signals`, `tone_patterns`, and `trust_signals`. Search keeps evidence-led ranking first, then preserves visible trace space for brand, editorial, trust and tone context on larger result sets.

Run:

```bash
uv run healf-max kb validate
uv run healf-max kb ingest
uv run healf-max kb search "low ferritin tired hyrox deep sleep"
```
