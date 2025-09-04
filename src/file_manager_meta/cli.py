import typer

from pathlib import Path
from typing_extensions import Annotated

from rich.console import Console

from file_manager_meta.enums import SortBy, KeepRule
from file_manager_meta.sort import organizer
from file_manager_meta.repair import repair_extension
from file_manager_meta.report import generate_report
from file_manager_meta.deduplicate import deduplicate_files

app = typer.Typer()
console = Console()


@app.command()
def sort(directory: Annotated[Path, typer.Argument(exists=True, dir_okay=True, help="Directory to sort")],
         new_directory: Annotated[Path, typer.Option(dir_okay=True, help="New directory for sorted files")] = None,
         sort_by: Annotated[SortBy, typer.Option(case_sensitive=False, prompt=True,
                                                 help="Sorting criterion: 'ext', 'date', or 'size'")] = "ext",
         ):
    """Sorts files by extension, creation date, or size for better organization."""
    if not new_directory:
        new_directory = directory

    organizer(directory, new_directory, sort_by.value)


@app.command()
def report(directory: Annotated[Path, typer.Argument(exists=True, help="Directory to report")],
         output: Annotated[Path, typer.Option(help="Output HTML file path")] = None,
         ):
    """Generates a detailed report with file metadata and integrity hashes (MD5, SHA-1, SHA-256)."""
    generate_report(directory, output)


@app.command()
def repair(directory: Annotated[Path, typer.Argument(exists=True, dir_okay=True, help="Directory to repair")]):
    """Repair files with missing or incorrect extensions."""
    repair_extension(directory)


@app.command()
def deduplicate(
    directory: Annotated[Path, typer.Argument(exists=True, dir_okay=True, help="Directory to scan for duplicates")],
    keep: Annotated[KeepRule, typer.Option(case_sensitive=False, help="Rule to decide which file to keep.")] = KeepRule.oldest,
    dry_run: Annotated[bool, typer.Option(help="Perform a dry run without deleting files.")] = False,
):
    """Finds and deletes duplicate files."""
    if not dry_run:
        typer.confirm(
            "You are not in dry-run mode. Files will be permanently deleted. Are you sure?",
            abort=True,
        )
    deduplicate_files(directory, dry_run=dry_run, keep_rule=keep.value)


if __name__ == "__main__":
    app()
