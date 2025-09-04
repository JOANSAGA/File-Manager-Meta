import os
from datetime import datetime
from typing import Optional

import typer
from pathlib import Path

from rich.progress import Progress, BarColumn, TaskProgressColumn
from rich.console import Console
from rich.table import Table

from file_manager_meta.repair import repair_extension
from file_manager_meta.enums import SortBy, DateGranularity

console = Console()

def organizer(directory: Path, new_directory: Path, sort_by: SortBy, date_granularity: Optional[DateGranularity] = None):
    files_without_extension = []
    skipped_files = []
    sorted_count = 0 # New counter for successfully sorted files
    total_files = sum(len(files) for _, _, files in os.walk(directory))

    with Progress("[progress.description]{task.description}", BarColumn(), TaskProgressColumn()) as progress:
        task = progress.add_task(f"[green]Sorting files: {sort_by}", total=total_files)

        for dir_path, dir_names, file_names in os.walk(directory):
            # Modify dir_names in-place to skip system/hidden directories
            dir_names[:] = [d for d in dir_names if d not in ['System Volume Information', '$RECYCLE.BIN']]
            dir_names[:] = [d for d in dir_names if not d.startswith('.')] # Skip hidden directories

            for file in file_names:
                file_path = Path(dir_path) / file
                # Skip hidden files (starting with '.')
                if file_path.name.startswith('.'):
                    progress.advance(task)
                    continue

                if file_path.is_file():

                    if not file_path.suffix:
                        files_without_extension.append(file_path)
                        progress.advance(task)
                        continue

                    new_directory.mkdir(exist_ok=True)
                    
                    try:
                        success = False # Assume failure
                        if sort_by == SortBy.EXT:
                            success = sort_by_extension(file_path, new_directory, file)
                        elif sort_by == SortBy.DATE:
                            success = sort_by_date(file_path, new_directory, file, date_granularity)
                        elif sort_by == SortBy.SIZE:
                            success = sort_by_size(file_path, new_directory, file)
                        
                        if success:
                            sorted_count += 1
                    except (PermissionError, OSError) as e:
                        console.print(f"[bold red]Error sorting {file_path.name}: {e}[/bold red]")
                        skipped_files.append(file_path)

                progress.advance(task)
    console.rule(f"Task completed! {sorted_count} files sorted.") # Use sorted_count here

    # Deleting empty directories
    deleted_dirs_count, skipped_dirs_count = delete_empty_directory(directory)
    console.print(f"[green]Empty directories deleted:[/green] {deleted_dirs_count}")
    if skipped_dirs_count > 0:
        console.print(f"[yellow]Empty directories skipped:[/yellow] {skipped_dirs_count} (due to permissions or other errors)")

    # Repair files with missing or incorrect extensions
    if files_without_extension:
        without_extension(directory, files_without_extension)

    if skipped_files:
        console.print("\n[bold yellow]Some files were skipped due to errors:[/bold yellow]")
        for skipped_file in skipped_files:
            console.print(f" - {skipped_file}")

    console.rule("Sort Task Summary")
    console.print(f"[green]Total files processed:[/green] {total_files}")
    console.print(f"[green]Files successfully sorted:[/green] {sorted_count}")
    if files_without_extension:
        console.print(f"[yellow]Files skipped (no extension):[/yellow] {len(files_without_extension)}")
    if skipped_files:
        console.print(f"[red]Files skipped (due to errors):[/red] {len(skipped_files)}")
    console.print(f"[green]Empty directories deleted:[/green] {deleted_dirs_count}")
    if skipped_dirs_count > 0:
        console.print(f"[yellow]Empty directories skipped:[/yellow] {skipped_dirs_count}")

def sort_by_extension(file_path: Path, new_directory: Path, file):
    extension = file_path.suffix[1:]  # Get the extension without the dot
    extension_dir = new_directory / extension
    extension_dir.mkdir(exist_ok=True)
    return save_file(file_path, extension_dir / file)


def sort_by_date(file_path: Path, new_directory: Path, file, date_granularity: Optional[DateGranularity] = None):
    # Get the creation date of the file
    creation_datetime = datetime.fromtimestamp(file_path.stat().st_ctime)
    
    # Build the directory path based on granularity
    if date_granularity == DateGranularity.YEAR:
        date_dir = new_directory / str(creation_datetime.year)
    elif date_granularity == DateGranularity.MONTH:
        date_dir = new_directory / str(creation_datetime.year) / f"{creation_datetime.month:02d}"
    elif date_granularity == DateGranularity.DAY:
        date_dir = new_directory / str(creation_datetime.year) / f"{creation_datetime.month:02d}" / f"{creation_datetime.day:02d}"
    else: # Default to YYYY/MM/DD if no granularity specified
        date_dir = new_directory / str(creation_datetime.year) / f"{creation_datetime.month:02d}" / f"{creation_datetime.day:02d}"

    date_dir.mkdir(parents=True, exist_ok=True)
    return save_file(file_path, date_dir / file)


def _format_size_for_dir(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes}B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes // 1024}KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes // (1024 * 1024)}MB"
    else:
        return f"{size_in_bytes // (1024 * 1024 * 1024)}GB"

def sort_by_size(file_path: Path, new_directory: Path, file):
    try:
        size = file_path.stat().st_size
        size_dir_name = _format_size_for_dir(size)
        size_dir = new_directory / size_dir_name
        size_dir.mkdir(exist_ok=True)
        return save_file(file_path, size_dir / file)
    except OSError as e:
        console.print(f"[bold red]Error getting size for {file_path.name}: {e}[/bold red]")
        return False


def count_empty_directories(directory: Path) -> int:
    counter = 0
    for dir_path, dir_names, file_names in os.walk(directory):
        for dir_name in dir_names:
            folder = Path(dir_path) / dir_name
            if not any(folder.iterdir()):  # Check if the folder is empty
                counter += 1
    return counter


def delete_empty_directory(directory: Path):
    deleted_count = 0
    skipped_count = 0
    total_empty_dirs = count_empty_directories(directory)

    with Progress("[progress.description]{task.description}", BarColumn(), TaskProgressColumn()) as progress:
        task = progress.add_task("[green]Deleting empty directories[/green]", total=total_empty_dirs)

        for dir_path, dir_names, file_names in os.walk(directory, topdown=False):
            for dir_name in dir_names:
                folder = Path(dir_path) / dir_name
                if not any(folder.iterdir()):  # Check if the folder is empty
                    try:
                        folder.rmdir()
                        deleted_count += 1
                    except (PermissionError, OSError) as e:
                        console.print(f"[bold red]Error deleting empty directory {folder}: {e}[/bold red]")
                        skipped_count += 1
                    progress.advance(task)
    console.rule(f"Task completed! Empty directories processed.")
    return deleted_count, skipped_count


def save_file(file_path: Path, destination_path: Path):
    final_destination = destination_path

    if destination_path.exists():
        base_name = destination_path.stem
        extension = destination_path.suffix
        parent = destination_path.parent
        counter = 1

        while final_destination.exists():
            final_destination = parent / f"{base_name} ({counter}){extension}"
            counter += 1
    
    try:
        file_path.rename(final_destination)
        return True
    except (PermissionError, OSError) as e:
        console.print(f"[bold red]Error moving {file_path.name} to {final_destination.name}: {e}[/bold red]")
        return False


def without_extension(directory: Path, files_without_extension):
    table = Table(title="Files without extension")
    table.add_column("No.", justify="right", style="cyan", no_wrap=True)
    table.add_column("Files", style="magenta")

    for idx, file in enumerate(files_without_extension, start=1):
        table.add_row(str(idx), file.__str__())

    console.print(table)

    user_input = typer.prompt(f"Do you want to try repairing it? (Yes = y, No = n) [No]", type=bool, default=False,
                              show_default=False)

    if user_input:
        repair_extension(directory)