# Spec 0001: Retrieval Lanes And Safety Evals

Implemented scope for Stage 4:

- Recommendation lanes keep authored safety-first priority order but now expose retrieved support.
- Bloods demo JSON/debug output shows lane provenance.
- Safety evaluation uses a versioned offline YAML dataset, deterministic stdlib metrics and a CI-usable Typer command.
- The hard gate is zero critical false negatives: any human-review case must not allow product recommendations.

The implementation deliberately separates retrieval diagnostics from safety diagnostics, following the same broad pattern used by current RAG evaluation tooling: test retrieval context quality separately from generated answer quality, then add custom domain guardrails for application-specific risk.
