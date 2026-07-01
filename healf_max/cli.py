from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from healf_max.config import load_settings
from healf_max.domain.planner import build_turn_plan
from healf_max.domain.safety import classify_safety
from healf_max.kb.index import build_index
from healf_max.kb.search import search_kb
from healf_max.kb.validator import validate_kb
from healf_max.llm import stream_turn
from healf_max.tools.registry import build_context_bundle

app = typer.Typer(help="Healf-Max command-line wellbeing recommendation assistant.")
kb_app = typer.Typer(help="Knowledge-base maintenance and search.")
app.add_typer(kb_app, name="kb")
console = Console()


@app.command()
def ask(
    query: str = typer.Argument(..., help="Customer wellbeing question."),
    debug: bool = typer.Option(False, "--debug", help="Show visible safety, plan and retrieval trace."),
) -> None:
    """Answer a customer wellbeing question."""
    _print_debug(query, debug=debug)
    _stream(query, debug=debug)


@app.command("bloods-demo")
def bloods_demo(
    debug: bool = typer.Option(False, "--debug", help="Show visible safety, plan and retrieval trace."),
) -> None:
    """Run the synthetic bloods and wearable demo."""
    query = (
        "I am training for Hyrox in 12 weeks. My deep sleep is low, HRV is below baseline, "
        "I am tired, and my latest bloods show low ferritin and borderline B12. What should I look at?"
    )
    _print_debug(query, debug=debug)
    _stream(query, debug=debug)


@kb_app.command("validate")
def kb_validate(
    strict: bool = typer.Option(False, "--strict", help="Treat warnings as validation failures."),
) -> None:
    """Validate markdown KB records."""
    settings = load_settings()
    result = validate_kb(settings.kb_dir, strict=strict)
    if result.ok:
        console.print(f"[green]KB valid[/green]: {result.record_count} records")
    else:
        console.print(f"[red]KB invalid[/red]: {result.record_count} readable records")
    if result.counts_by_type:
        table = Table(title="Records by type")
        table.add_column("type")
        table.add_column("count", justify="right")
        for record_type, count in sorted(result.counts_by_type.items()):
            table.add_row(record_type, str(count))
        console.print(table)
    for warning in result.warnings:
        console.print(f"[yellow]warning[/yellow] {warning}")
    for error in result.errors:
        console.print(f"[red]error[/red] {error}")
    if not result.ok:
        raise typer.Exit(1)


@kb_app.command("ingest")
def kb_ingest() -> None:
    """Build the local JSONL/Numpy KB index."""
    settings = load_settings()
    count = build_index(kb_dir=settings.kb_dir, storage_dir=settings.storage_dir)
    console.print(f"[green]Indexed[/green] {count} KB records into {settings.storage_dir}")


@kb_app.command("search")
def kb_search(query: str = typer.Argument(..., help="Search query.")) -> None:
    """Search the local KB index with lexical fallback."""
    settings = load_settings()
    records = search_kb(query, kb_dir=settings.kb_dir, storage_dir=settings.storage_dir, limit=20)
    if not records:
        console.print("[yellow]No matching KB records found.[/yellow]")
        return

    for record_type in _ordered_types(records):
        table = Table(title=record_type)
        table.add_column("score", justify="right")
        table.add_column("path")
        table.add_column("title")
        table.add_column("why")
        for record in [item for item in records if item.type == record_type]:
            table.add_row(
                f"{record.score:.1f}",
                record.path,
                record.title,
                "; ".join(record.retrieval_reason),
            )
        console.print(table)


def _stream(query: str, *, debug: bool) -> None:
    for chunk in stream_turn(query, debug=debug):
        console.print(chunk, end="")
    console.print()


def _print_debug(query: str, *, debug: bool) -> None:
    if not debug:
        return
    settings = load_settings()
    safety = classify_safety(query)
    plan = build_turn_plan(query, safety)
    trace = build_context_bundle(
        query,
        safety=safety,
        plan=plan,
        settings=settings,
        debug=True,
        include_bloods="blood" in query.lower() or "ferritin" in query.lower(),
    )
    console.print(Panel(trace, title="Debug trace", border_style="cyan"))


def main() -> None:
    app()


def _ordered_types(records: list[object]) -> list[str]:
    order = [
        "wellbeing_moment",
        "biomarker",
        "evidence_claim",
        "wearable_signal",
        "product_category",
        "editorial_signal",
        "trust_signal",
        "tone_pattern",
        "brand_signal",
        "example",
    ]
    present = {getattr(record, "type") for record in records}
    return [record_type for record_type in order if record_type in present] + sorted(present.difference(order))


if __name__ == "__main__":
    main()
