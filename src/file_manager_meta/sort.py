import os
from datetime import datetime

import typer
from pathlib import Path

from rich.progress import Progress, BarColumn, TaskProgressColumn
from rich.console import Console
from rich.table import Table

from file_manager_meta.repair import repair_extension
from file_manager_meta.enums import SortBy

console = Console()


def organizer(directory: Path, new_directory: Path, sort_by: SortBy):
    files_without_extension = []
    total_files = sum(len(files) for _, _, files in os.walk(directory))

    with Progress("[progress.description]{task.description}", BarColumn(), TaskProgressColumn()) as progress:
        task = progress.add_task(f"[green]Sorting files: {sort_by}", total=total_files)

        for dir_path, dir_names, file_names in os.walk(directory):
            for file in file_names:
                file_path = Path(dir_path) / file
                if file_path.is_file():

                    if not file_path.suffix:
                        files_without_extension.append(file_path)
                        continue

                    new_directory.mkdir(exist_ok=True)
                    match sort_by:
                        case SortBy.EXT:
                            sort_by_extension(file_path, new_directory, file)

                        case SortBy.DATE:
                            sort_by_date(file_path, new_directory, file)

                        case SortBy.SIZE:
                            sort_by_size(file_path, new_directory, file)

                progress.advance(task)
    console.rule(f"Task completed! {total_files} files sorted.")

    # Deleting empty directories
    delete_empty_directory(directory)

    # Repair files with missing or incorrect extensions
    if files_without_extension:
        without_extension(directory, files_without_extension)


def sort_by_extension(file_path: Path, new_directory: Path, file):
    extension = file_path.suffix[1:]  # Get the extension without the dot
    extension_dir = new_directory / extension
    extension_dir.mkdir(exist_ok=True)
    save_file(file_path, extension_dir / file)


def sort_by_date(file_path: Path, new_directory: Path, file):
    # Get the creation date of the file in format YYYY-MM-DD
    creation_date = datetime.fromtimestamp(file_path.stat().st_ctime).strftime("%Y-%m-%d").split("-")
    date_dir = new_directory / creation_date[0] / creation_date[1] / creation_date[2]
    date_dir.mkdir(parents=True, exist_ok=True)
    save_file(file_path, date_dir / file)


def sort_by_size(file_path: Path, new_directory: Path, file):
    console.print(file_path, new_directory, file)


def count_empty_directories(directory: Path) -> int:
    counter = 0
    for dir_path, dir_names, file_names in os.walk(directory):
        for dir_name in dir_names:
            folder = Path(dir_path) / dir_name
            if not any(folder.iterdir()):  # Check if the folder is empty
                counter += 1
    return counter


def delete_empty_directory(directory: Path):
    total_empty_dirs = count_empty_directories(directory)

    with Progress("[progress.description]{task.description}", BarColumn(), TaskProgressColumn()) as progress:
        task = progress.add_task("[green]Deleting empty directories", total=total_empty_dirs)

        # Delete empty directories
        for dir_path, dir_names, file_names in os.walk(directory, topdown=False):
            for dir_name in dir_names:
                folder = Path(dir_path) / dir_name
                if not any(folder.iterdir()):  # Check if the folder is empty
                    folder.rmdir()  # Remove the empty folder
                    # print(f"Folder deleted: {folder}")
                    progress.advance(task)
    console.rule(f"Task completed! Directories deleted.")


def save_file(file_path: Path, directory: Path):
    try:
        file_path.rename(directory)
    except FileExistsError as e:
        if directory.exists():
            base_name = directory.stem
            extension = directory.suffix
            parent = directory.parent
            counter = 1

            # Generate a new name until it does not exist
            while directory.exists():
                directory = parent / f"{base_name} ({counter}){extension}"
                counter += 1

        file_path.rename(directory)


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
