import typer

from pathlib import Path
from typing_extensions import Annotated
from typing import List, Optional

from rich.console import Console

from file_manager_meta.enums import SortBy, KeepRule, DateGranularity
from file_manager_meta.sort import organizer
from file_manager_meta.repair import repair_extension
from file_manager_meta.report import generate_report
from file_manager_meta.deduplicate import deduplicate_files
from file_manager_meta.cache_manager import view_cache_contents, clear_cache, get_cache_file_path, recreate_database, \
    clear_all_caches  # New import

app = typer.Typer()
console = Console()


@app.command()
def sort(directory: Annotated[Path, typer.Argument(exists=True, dir_okay=True, help="Directory to sort")],
         new_directory: Annotated[Path, typer.Option(dir_okay=True, help="New directory for sorted files")] = None,
         sort_by: Annotated[SortBy, typer.Option(case_sensitive=False, prompt=True,
                                                 help="Sorting criterion: 'ext', 'date', or 'size'")] = SortBy.EXT,
         date_granularity: Annotated[Optional[DateGranularity], typer.Option(
             help="Granularity for date sorting: 'year', 'month', or 'day'. Only valid with --sort-by date."
         )] = None,
         ):
    """Sorts files by extension, creation date, or size for better organization."""
    if date_granularity and sort_by != SortBy.DATE:
        console.print("[red]--date-granularity is only valid when --sort-by is 'date'.[/red]")
        raise typer.Exit(code=1)

    if not new_directory:
        new_directory = directory

    organizer(directory, new_directory, sort_by.value, date_granularity.value if date_granularity else None)


@app.command()
def report(directory: Annotated[Path, typer.Argument(exists=True, help="Directory to report")],
           output: Annotated[Path, typer.Option(help="Output HTML file path")] = None,
           ):
    """Generates a detailed report of file hashes, grouped by subfolder, and identifies duplicate file sets."""
    generate_report(directory, output)


@app.command()
def repair(paths: Annotated[List[Path], typer.Argument(exists=True, help="Paths to repair (files or directories)")]):
    """Repair files with missing or incorrect extensions."""
    repair_extension(paths)


@app.command()
def deduplicate(
        directory: Annotated[Path, typer.Argument(exists=True, dir_okay=True, help="Directory to scan for duplicates")],
        keep: Annotated[
            KeepRule, typer.Option(case_sensitive=False, help="Rule to decide which file to keep.")] = KeepRule.oldest,
        dry_run: Annotated[bool, typer.Option(help="Perform a dry run without deleting files.")] = False,
):
    """Finds and deletes duplicate files."""
    if not dry_run:
        typer.confirm(
            "You are not in dry-run mode. Files will be permanently deleted. Are you sure?",
            abort=True,
        )
    deduplicate_files(directory, dry_run=dry_run, keep_rule=keep.value)


# Create a Typer app for cache commands
cache_app = typer.Typer(name="cache", help="Manage the application's cache.")


@cache_app.command("view")
def cache_view(
        directory: Annotated[Path, typer.Argument(exists=True, dir_okay=True, help="Directory whose cache to view.")]):
    """View the contents of the cache database for a specific directory."""
    view_cache_contents(directory)


@cache_app.command("clear")
def cache_clear(
        directory: Annotated[Path, typer.Argument(exists=True, dir_okay=True, help="Directory whose cache to clear.")]):
    """Clear the cache database for a specific directory."""
    typer.confirm(
        f"This will permanently delete the cache database for {directory}. Are you sure?",
        abort=True,
    )
    clear_cache(directory)


@cache_app.command("recreate")
def cache_recreate(directory: Annotated[
    Path, typer.Argument(exists=True, dir_okay=True, help="Directory whose cache to recreate.")]):
    """Recreate the cache database for a specific directory."""
    typer.confirm(
        f"This will permanently delete and recreate the cache database for {directory}. Are you sure?",
        abort=True,
    )
    recreate_database(directory)


@cache_app.command("clear-all")
def cache_clear_all():
    """Clear all cache databases for the application."""
    typer.confirm(
        "This will permanently delete ALL cache databases for the application. Are you sure?",
        abort=True,
    )
    clear_all_caches()


@cache_app.command("path")
def cache_path(directory: Annotated[
    Path, typer.Argument(exists=True, dir_okay=True, help="Directory whose cache path to view.")]):
    """Show the path to the cache database for a specific directory."""
    db_path = get_cache_file_path(directory)
    console.print(f"Cache database path for [cyan]{directory}[/cyan]: [green]{db_path}[/green]")


# Register the cache_app as a subcommand of the main app
app.add_typer(cache_app)

if __name__ == "__main__":
    app()
