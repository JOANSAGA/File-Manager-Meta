import typer

from pathlib import Path
from typing_extensions import Annotated

from file_manager_meta.enums import SortBy
from file_manager_meta.sort import organizer
from file_manager_meta.repair import repair_extension

app = typer.Typer()


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
def report(directory: Annotated[Path, typer.Argument(exists=True, help="Directory to sort")]):
    """Generates a detailed report with file metadata and integrity hashes (MD5, SHA-1, SHA-256)."""
    print(f"Directory: {directory}")


@app.command()
def repair(directory: Annotated[Path, typer.Argument(exists=True, dir_okay=True, help="Directory to repair")]):
    """Repair files with missing or incorrect extensions."""
    repair_extension(directory)


if __name__ == "__main__":
    app()
