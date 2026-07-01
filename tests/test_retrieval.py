from healf_max.kb.schemas import KBRecord
from healf_max.kb.search import lexical_search


def test_fallback_search_returns_matching_records_from_memory_fixture() -> None:
    records = [
        KBRecord(
            id="moment.hyrox",
            title="Hyrox fatigue and low deep sleep",
            kind="moments",
            tags=["hyrox", "sleep", "ferritin"],
            body="Training load, low ferritin follow-up, electrolytes and sleep support.",
            path="moments/hyrox.md",
        ),
        KBRecord(
            id="tone.stack",
            title="Low chaos stack",
            kind="tone",
            tags=["tone"],
            body="Do not overwhelm the customer with a large stack.",
            path="tone/stack.md",
        ),
    ]

    results = lexical_search("low ferritin tired hyrox deep sleep", records)

    assert [result.id for result in results[:1]] == ["moment.hyrox"]
    assert results[0].score > results[1].score
