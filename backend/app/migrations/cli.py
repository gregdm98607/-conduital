"""CLI commands for migration integrity checking.

Usage:
    python -m app.migrations.cli chain      # Show migration chain
    python -m app.migrations.cli check      # Run all integrity checks
    python -m app.migrations.cli validate   # Validate schema matches models
    python -m app.migrations.cli history    # Show migration history
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine

from app.core.config import settings
from app.migrations.chain import (
    get_chain_order,
    get_migration_chain,
    validate_chain,
    compare_chain_to_db,
)
from app.migrations.integrity import IntegrityReport, IssueSeverity, run_all_checks
from app.migrations.validators import get_schema_diff, validate_alembic_version

app = typer.Typer(
    name="migrations",
    help="Migration integrity checking commands",
    no_args_is_help=True,
)
console = Console()


def get_engine():
    """Create database engine from settings."""
    return create_engine(settings.DATABASE_URL)


@app.command()
def chain():
    """Show migration chain and detect issues."""
    console.print(Panel.fit("[bold]Migration Chain Analysis[/bold]"))

    migrations = get_migration_chain()
    if not migrations:
        console.print("[red]No migrations found![/red]")
        raise typer.Exit(1)

    # Validate chain
    result = validate_chain()

    # Show chain order
    order = get_chain_order()
    console.print(f"\n[bold]Chain ({len(order)} migrations):[/bold]")
    for i, rev in enumerate(order):
        info = migrations.get(rev)
        prefix = "  " if i > 0 else ""
        connector = "-> " if i > 0 else ""
        desc = info.description[:50] if info else "?"
        console.print(f"{prefix}{connector}[cyan]{rev}[/cyan] ({desc})")

    # Show status
    console.print("")
    if result.is_valid:
        console.print("[green]Status: HEALTHY[/green]")
        console.print(f"Head: [cyan]{result.head_revision}[/cyan]")
    else:
        console.print("[red]Status: ISSUES DETECTED[/red]")
        for error in result.errors:
            console.print(f"  [red]- {error}[/red]")

    if result.orphaned:
        console.print(f"\n[yellow]Orphaned migrations:[/yellow]")
        for rev in result.orphaned:
            console.print(f"  - {rev}")

    if result.multiple_heads:
        console.print(f"\n[yellow]Multiple heads (branches):[/yellow]")
        for rev in result.multiple_heads:
            console.print(f"  - {rev}")


@app.command()
def check():
    """Run all integrity checks on the database."""
    console.print(Panel.fit("[bold]Migration Integrity Check[/bold]"))

    engine = get_engine()

    # Chain validation
    console.print("\n[bold]1. Chain Validation[/bold]")
    chain_result = validate_chain()
    if chain_result.is_valid:
        console.print("  [green][OK][/green] Migration chain is continuous")
    else:
        console.print("  [red][FAIL][/red] Chain issues detected:")
        for error in chain_result.errors:
            console.print(f"    - {error}")

    # DB sync check
    console.print("\n[bold]2. Database Sync[/bold]")
    sync = compare_chain_to_db(engine)
    if sync["in_sync"]:
        console.print(f"  [green][OK][/green] Database at head: {sync['db_revision']}")
    else:
        console.print(f"  [yellow][WARN][/yellow] Database revision: {sync['db_revision']}")
        console.print(f"         Chain head: {sync['chain_head']}")
        if sync["pending_migrations"]:
            console.print(f"         Pending: {len(sync['pending_migrations'])} migrations")

    # Data integrity
    console.print("\n[bold]3. Data Integrity[/bold]")
    report = run_all_checks(engine)
    console.print(f"  Checked {report.tables_checked} tables, {report.rows_checked} rows")

    if report.is_healthy:
        console.print("  [green][OK][/green] No integrity issues found")
    else:
        console.print(f"  [red][FAIL][/red] {report.error_count} errors, {report.warning_count} warnings")

        # Group by table
        by_table: dict[str, list] = {}
        for issue in report.issues:
            by_table.setdefault(issue.table, []).append(issue)

        for table, issues in by_table.items():
            console.print(f"\n  [bold]{table}:[/bold]")
            for issue in issues:
                severity_color = "red" if issue.severity == IssueSeverity.ERROR else "yellow"
                console.print(
                    f"    [{severity_color}][{issue.severity.value.upper()}][/{severity_color}] "
                    f"{issue.column}: {issue.message}"
                )
                if issue.count > 0:
                    console.print(f"           Count: {issue.count}")
                if issue.sample_values:
                    samples = ", ".join(str(v) for v in issue.sample_values[:3])
                    console.print(f"           Samples: {samples}")

    # Summary
    console.print("\n" + "=" * 50)
    all_good = chain_result.is_valid and sync["in_sync"] and report.is_healthy
    if all_good:
        console.print("[green]All checks passed![/green]")
    else:
        console.print("[red]Issues detected - review above[/red]")
        raise typer.Exit(1)


@app.command()
def validate():
    """Validate database schema matches SQLAlchemy models."""
    console.print(Panel.fit("[bold]Schema Validation[/bold]"))

    engine = get_engine()

    # Import models to get metadata
    from app.models import Base

    diff = get_schema_diff(engine, Base.metadata)

    if diff.is_empty:
        console.print("[green]Schema matches models![/green]")
        return

    if diff.missing_tables:
        console.print("\n[red]Missing tables:[/red]")
        for table in diff.missing_tables:
            console.print(f"  - {table}")

    if diff.extra_tables:
        console.print("\n[yellow]Extra tables (not in models):[/yellow]")
        for table in diff.extra_tables:
            console.print(f"  - {table}")

    if diff.missing_columns:
        console.print("\n[red]Missing columns:[/red]")
        for table, cols in diff.missing_columns.items():
            console.print(f"  {table}: {', '.join(cols)}")

    if diff.extra_columns:
        console.print("\n[yellow]Extra columns:[/yellow]")
        for table, cols in diff.extra_columns.items():
            console.print(f"  {table}: {', '.join(cols)}")

    if diff.errors:
        console.print("\n[red]Errors:[/red]")
        for error in diff.errors:
            console.print(f"  - {error}")

    raise typer.Exit(1)


@app.command()
def history():
    """Show migration history with database state."""
    console.print(Panel.fit("[bold]Migration History[/bold]"))

    engine = get_engine()
    migrations = get_migration_chain()
    order = get_chain_order()
    sync = compare_chain_to_db(engine)

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", width=3)
    table.add_column("Revision", width=20)
    table.add_column("Description", width=40)
    table.add_column("Status", width=10)

    db_revision = sync.get("db_revision")
    pending = set(sync.get("pending_migrations", []))

    for i, rev in enumerate(order, 1):
        info = migrations.get(rev)
        desc = info.description[:40] if info else "?"

        if rev == db_revision:
            status = "[green]current[/green]"
        elif rev in pending:
            status = "[yellow]pending[/yellow]"
        else:
            status = "[dim]applied[/dim]"

        table.add_row(str(i), rev, desc, status)

    console.print(table)

    console.print(f"\nDatabase revision: [cyan]{db_revision or 'None'}[/cyan]")
    console.print(f"Chain head: [cyan]{sync.get('chain_head') or 'None'}[/cyan]")


@app.command()
def alembic_check():
    """Validate alembic_version table."""
    console.print(Panel.fit("[bold]Alembic Version Check[/bold]"))

    engine = get_engine()
    chain_result = validate_chain()

    is_valid, message = validate_alembic_version(engine, chain_result.head_revision)

    if is_valid:
        console.print(f"[green][OK][/green] {message}")
    else:
        console.print(f"[red][FAIL][/red] {message}")
        raise typer.Exit(1)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
