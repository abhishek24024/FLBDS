"""Command-line interface for FLBDS v3.0."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from flbds.config import get_settings
from flbds.graph.store import GraphStore
from flbds.knowledge.physics import PhysicalLawsCatalog
from flbds.knowledge.triz import TrizKnowledge
from flbds.ontology.models import SapphireGraph
from flbds.ontology.validate import validate_graph

app = typer.Typer(
    name="flbds",
    help="FLBDS v3.0 — Functional & Logical Biomimetic Design System",
    no_args_is_help=True,
)
console = Console()


@app.command()
def doctor() -> None:
    """Run environment, knowledge base, and subsystem self-checks."""
    console.print(Panel.fit("[bold cyan]FLBDS v3.0 System Self-Check (Doctor)[/bold cyan]"))

    table = Table(title="Diagnostic Status")
    table.add_column("Subsystem", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    # 1. Config
    try:
        settings = get_settings()
        table.add_row("Configuration", "[green]OK[/green]", f"Root: {settings.paths.root}")
    except Exception as e:
        table.add_row("Configuration", "[red]FAIL[/red]", str(e))

    # 2. TRIZ Knowledge Base
    try:
        triz = TrizKnowledge()
        n_params = len(triz.all_parameters())
        n_principles = len(triz.all_principles())
        sample = triz.principles_for(14, 21)
        assert sample == [10, 26, 28, 35]
        table.add_row(
            "TRIZ Knowledge Spine",
            "[green]OK[/green]",
            f"{n_params} params, {n_principles} principles, matrix verified",
        )
    except Exception as e:
        table.add_row("TRIZ Knowledge Spine", "[red]FAIL[/red]", str(e))

    # 3. Physics & Buckingham Pi
    try:
        phys = PhysicalLawsCatalog()
        n_laws = len(phys.all_laws())
        n_groups = len(phys.all_groups())
        re_exp = phys.get_group("Re").length_exponent
        table.add_row(
            "Physical Laws Catalog",
            "[green]OK[/green]",
            f"{n_laws} laws, {n_groups} Pi-groups (Re exp={re_exp})",
        )
    except Exception as e:
        table.add_row("Physical Laws Catalog", "[red]FAIL[/red]", str(e))

    # 4. Property Graph Store
    try:
        store = GraphStore(":memory:")
        table.add_row("Graph Store (SQLite)", "[green]OK[/green]", "In-memory test store verified")
    except Exception as e:
        table.add_row("Graph Store (SQLite)", "[red]FAIL[/red]", str(e))

    # 5. Curated Seed Graphs
    try:
        seeds_dir = Path(__file__).resolve().parent / "data" / "seeds"
        seed_files = list(seeds_dir.glob("*.json"))
        assert len(seed_files) >= 10
        table.add_row("Curated Seeds", "[green]OK[/green]", f"{len(seed_files)} seed graphs present")
    except Exception as e:
        table.add_row("Curated Seeds", "[yellow]WARN[/yellow]", str(e))

    # 6. GPU Detection
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            n_gpus = torch.cuda.device_count()
            table.add_row("GPU Acceleration", "[green]OK[/green]", f"{n_gpus}x {dev_name}")
        else:
            table.add_row("GPU Acceleration", "[yellow]CPU[/yellow]", "CUDA not available in current env")
    except ImportError:
        table.add_row("GPU Acceleration", "[yellow]N/A[/yellow]", "PyTorch optional dependency not loaded")

    console.print(table)


@app.command()
def validate(
    path: Path = typer.Argument(..., help="Path to SapphireGraph JSON file"),
    strict: bool = typer.Option(True, "--strict/--lenient", help="Strict abductive variable checking"),
) -> None:
    """Validate a SAPPhIRE causal property graph."""
    if not path.exists():
        console.print(f"[red]Error:[/red] File not found: {path}")
        raise typer.Exit(code=1)

    try:
        g = SapphireGraph.from_json(path)
    except Exception as e:
        console.print(f"[red]Error parsing graph JSON:[/red] {e}")
        raise typer.Exit(code=1)

    report = validate_graph(g, strict_abductive=strict)
    if report.ok:
        console.print(f"[green]PASS[/green] {g.id}: valid {g.domain} graph ({len(g.nodes)} nodes, {len(g.edges)} edges)")
        console.print(f"Construct coverage: {report.metrics.get('construct_coverage', 0):.0%}")
        console.print(f"Grounding ratio:    {report.metrics.get('grounding_ratio', 0):.0%}")
    else:
        console.print(f"[red]FAIL[/red] {g.id}: {len(report.errors)} error(s)")
        for err in report.errors:
            console.print(f" - [red]{err.code}[/red]: {err['message']}")
        raise typer.Exit(code=1)


@app.command()
def seed_store(
    db_path: Optional[str] = typer.Option(None, "--db", help="Target SQLite path"),
) -> None:
    """Populate graph store with curated biological and engineering seed graphs."""
    settings = get_settings()
    target_db = db_path or str(settings.paths.graph_db)
    store = GraphStore(target_db)

    seeds_dir = Path(__file__).resolve().parent / "data" / "seeds"
    loaded = 0
    for p in sorted(seeds_dir.glob("*.json")):
        g = SapphireGraph.from_json(p)
        store.save_graph(g)
        loaded += 1
        console.print(f"Loaded: [cyan]{g.id}[/cyan] ({g.domain})")

    console.print(f"[green]Successfully loaded {loaded} seed graphs into {target_db}[/green]")



@app.command()
def ingest(
    file: Path = typer.Option(..., "--file", "-f", help="Path to raw text file or manuscript"),
    domain: str = typer.Option("biological", "--domain", "-d", help="Domain: biological or engineering"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Title of system"),
    graph_id: Optional[str] = typer.Option(None, "--id", help="Graph identifier"),
    db_path: Optional[str] = typer.Option(None, "--db", help="Target SQLite graph store path"),
) -> None:
    """Extract and ingest a SAPPhIRE causal graph from text into G_MCKG."""
    if not file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(code=1)

    raw_text = file.read_text(encoding="utf-8")
    doc_title = title or file.stem.replace("_", " ").title()
    gid = graph_id or f"{domain[:3]}:{file.stem.lower()}"

    from flbds.extraction.fusion import SAPPhIREExtractor
    extractor = SAPPhIREExtractor()
    graph, meta = extractor.extract(
        text=raw_text,
        graph_id=gid,
        title=doc_title,
        domain=domain,
        source_id=f"file:{file.name}",
    )

    settings = get_settings()
    store = GraphStore(db_path or str(settings.paths.graph_db))
    store.save_graph(graph)

    status_str = "[green]VALID[/green]" if meta["valid"] else "[red]INVALID[/red]"
    console.print(Panel.fit(
        f"Ingested: [bold cyan]{graph.id}[/bold cyan] ({graph.title})\n"
        f"Status: {status_str} | Errors: {meta['n_errors']} | Warnings: {meta['n_warnings']}\n"
        f"Construct Coverage: {meta['construct_coverage']:.0%} | Grounding: {meta['grounding_ratio']:.0%}\n"
        f"Saved to: {store.db_path}"
    ))



@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8765, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
) -> None:
    """Start the FLBDS v3.0 API & UI demonstration server."""
    import uvicorn
    console.print(f"[bold green]Starting FLBDS v3.0 API and UI at http://{host}:{port}[/bold green]")
    uvicorn.run("flbds.api.server:app", host=host, port=port, reload=reload)


@app.command(name="eval")
def run_eval() -> None:
    """Execute master benchmark evaluation across all 5 specification families."""
    from flbds.eval.benchmark import BenchmarkRunner
    runner = BenchmarkRunner()
    console.print("[cyan]Running master benchmark evaluation suite...[/cyan]")
    report = runner.run_all()
    console.print(report.summary_table())
    if not report.overall_pass:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
