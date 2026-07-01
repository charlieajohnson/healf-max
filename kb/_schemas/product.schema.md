---
id: schema.product
type: reference
title: Product record schema
status: active
retrieval_priority: 1
reviewed_at: '2026-07-01'
---
# Product Record Schema

Product records are dated catalogue snapshots, not live commerce truth.

Required frontmatter:

```yaml
id: lmnt_recharge_electrolytes
type: product
title: LMNT Recharge Electrolytes
status: active
brand: LMNT
name: LMNT Recharge Electrolytes
catalogue_snapshot: healf_best_sellers_2026_06_30
source_path: supplied/scaffold/kb/products/01-lmnt-lmnt-recharge-electrolytes.md
product_url: https://healf.com/products/lmnt-recharge-electrolytes-variety-pack
category_routes:
- electrolytes
retrieval_priority: 7
reviewed_at: '2026-07-01'
```

Product records should link to durable category records through `category_routes`. Category records link back through `catalogue_products`.

Any price, stock, delivery or review values must be treated as snapshot metadata and must not be presented as live availability or live pricing.
