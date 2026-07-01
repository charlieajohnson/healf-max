# Healf-Max Knowledge Base

Markdown-first records with typed YAML frontmatter. The corpus is deliberately split into small, traceable records so retrieval can combine evidence, biomarkers, product lanes, brand voice and safety boundaries without collapsing them into one blob.

The structure borrows from Andrej Karpathy's LLM Wiki idea: sources are compiled into durable Markdown knowledge records, then improved in Git over time. Healf-Max adds typed record schemas, safety fields and an explicit graph of frontmatter links so retrieval can follow known relationships rather than relying only on semantic similarity.

## Structure

- `_schemas/` - record-shape examples and validation notes
- `evidence/` - ingredient, practice and plain-language evidence claims
- `biomarkers/` - marker interpretation and action routing
- `signals/` - wearable and behavioural trend records
- `products/` - category-first commercial lanes plus dated catalogue snapshots
- `editorial/` - Healf-style editorial frames
- `trust/` - customer confidence and service signals
- `tone/` - reusable response language
- `moments/` - pre-modelled wellbeing situations
- `examples/` - regression/evaluation examples
- `brand/` - supplied Healf brand source context

## Rules

Every active record needs `id`, `type`, `title`, `status`, `retrieval_priority`, and `reviewed_at`. Health-related records also need `safety_boundary` and `prohibited_claims`.

Wellbeing moments may link to `biomarker_routes`, `evidence_routes`, `wearable_signals`, `product_lanes`, `editorial_signals`, `tone_patterns`, and `trust_signals`. Product categories link to product snapshots with `catalogue_products`; product snapshots link back with `category_routes` and can link to relevant category pairings with `paired_product_categories`. Ingestion writes those links into `.storage/kb_graph.json`. Search combines fielded matching, BM25, optional embeddings and graph-hop expansion, then preserves visible trace space for wearable, brand, editorial, trust and tone context on larger result sets.

## Products

`products/*.md` files are durable category lanes. `products/catalogue/*.md` files are dated product snapshots from the supplied Healf Best Sellers product corpus, pulled 2026-06-30.

Catalogue product records may store price, stock, review count, delivery and handle metadata, but those values are snapshot-only. Answers must not present them as live availability or live pricing.

Current product layer:

- 15 product category records
- 20 product snapshot records
- category-to-product graph links through `catalogue_products`
- product-to-category graph links through `category_routes`

Run:

```bash
uv run healf-max kb validate
uv run healf-max kb ingest
uv run healf-max kb search "low ferritin tired hyrox deep sleep"
```
