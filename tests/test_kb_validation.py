from healf_max.kb.parser import parse_markdown_text
from healf_max.kb.validator import validate_kb


def test_kb_validate_handles_empty_directory(tmp_path) -> None:
    result = validate_kb(tmp_path)

    assert result.ok is True
    assert result.record_count == 0
    assert result.errors == []


def test_loader_parses_markdown_frontmatter() -> None:
    record = parse_markdown_text(
        """---
id: evidence.sleep
title: Sleep pressure
kind: evidence
tags: [sleep, recovery]
---
Deep sleep is one recovery signal, not the whole story.
""",
        source_path="fixture.md",
    )

    assert record.id == "evidence.sleep"
    assert record.kind == "evidence"
    assert "recovery" in record.tags
    assert "Deep sleep" in record.body
