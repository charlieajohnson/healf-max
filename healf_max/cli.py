from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from healf_max.config import load_settings
from healf_max.domain.planner import build_turn_plan
from healf_max.domain.safety import classify_safety
from healf_max.evals.safety import default_paths, load_cases, load_thresholds, run_safety_eval, write_report
from healf_max.kb.search import search_kb
from healf_max.kb.validator import validate_kb

app = typer.Typer(help="Healf-Max command-line wellbeing recommendation assistant.")
kb_app = typer.Typer(help="Knowledge-base maintenance and search.")
evals_app = typer.Typer(help="Offline evaluation harnesses.")
app.add_typer(kb_app, name="kb")
app.add_typer(evals_app, name="evals")
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
    json_output: bool = typer.Option(False, "--json", help="Output the machine-readable Bloods plan."),
    profile: str | None = typer.Option(None, "--profile", help="Path to a synthetic Bloods panel YAML file."),
) -> None:
    """Run the synthetic Bloods and wearable flagship demo."""
    from healf_max.demo.bloods import (
        build_bloods_demo_plan,
        build_bloods_demo_prompt,
        render_bloods_demo_debug,
        render_bloods_demo_fallback,
        render_bloods_demo_json,
    )

    settings = load_settings()
    plan = build_bloods_demo_plan(profile_path=profile, settings=settings)
    if json_output:
        typer.echo(render_bloods_demo_json(plan))
        return
    if debug:
        console.print(Panel(render_bloods_demo_debug(plan), title="Bloods flagship trace", border_style="cyan"))
    if not settings.openai_api_key:
        console.print(render_bloods_demo_fallback(plan))
        return
    from healf_max.llm import stream_turn

    for chunk in stream_turn(build_bloods_demo_prompt(plan), debug=False):
        console.print(chunk, end="")
    console.print()


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
    from healf_max.kb.index import build_index

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


@evals_app.command("safety")
def evals_safety(
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable safety eval report."),
    report_dir: str | None = typer.Option(None, "--report-dir", help="Directory for report.json and report.md."),
) -> None:
    """Run the deterministic safety classifier eval."""
    settings = load_settings()
    cases_path, thresholds_path = default_paths(settings.project_root)
    report = run_safety_eval(load_cases(cases_path), thresholds=load_thresholds(thresholds_path))
    if report_dir:
        write_report(report, report_dir)
    if json_output:
        typer.echo(report.model_dump_json(indent=2))
    else:
        _print_safety_eval_report(report)
    if not report.passed:
        raise typer.Exit(1)


def _stream(query: str, *, debug: bool) -> None:
    from healf_max.llm import stream_turn

    for chunk in stream_turn(query, debug=debug):
        console.print(chunk, end="")
    console.print()


def _print_safety_eval_report(report: object) -> None:
    passed = getattr(report, "passed")
    macro = getattr(report, "macro_f1")
    console.print(f"[{'green' if passed else 'red'}]Safety eval {'passed' if passed else 'failed'}[/]: macro-F1={macro:.3f}")
    metrics_table = Table(title="Per-category metrics")
    metrics_table.add_column("category")
    metrics_table.add_column("precision", justify="right")
    metrics_table.add_column("recall", justify="right")
    metrics_table.add_column("f1", justify="right")
    metrics_table.add_column("support", justify="right")
    for category, metrics in sorted(getattr(report, "per_category").items()):
        metrics_table.add_row(
            category,
            f"{metrics.precision:.3f}",
            f"{metrics.recall:.3f}",
            f"{metrics.f1:.3f}",
            str(metrics.support),
        )
    console.print(metrics_table)
    critical = getattr(report, "critical_false_negatives")
    if critical:
        for item in critical:
            console.print(f"[red]critical false negative[/] {item.case_id}: {item.message}")
    else:
        console.print("[green]Critical false negatives: 0[/green]")
    console.print(f"Over-blocks: {len(getattr(report, 'over_blocks'))}")


def _print_debug(query: str, *, debug: bool) -> None:
    if not debug:
        return
    from healf_max.tools.registry import build_context_bundle

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
