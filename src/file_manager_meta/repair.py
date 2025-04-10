import os
import exiftool
from pathlib import Path

from rich.console import Console
from rich.progress import Progress

console = Console()


# get metadata from files used exiftool and rename files with missing or incorrect extensions
def repair_extension(directory: Path):
    total_files = sum(len(files) for _, _, files in os.walk(directory))

    with Progress() as progress:
        task = progress.add_task("[green]Repair files", total=total_files, leave=True)

        for dir_path, dir_names, file_names in os.walk(directory):
            for file in file_names:
                file_path = Path(dir_path) / file
                if file_path.is_file():

                    if not file_path.suffix:

                        with exiftool.ExifToolHelper() as et:
                            metadata = et.get_metadata(file_path.__str__())
                            if metadata:
                                new_extension = metadata[0]["File:FileTypeExtension"].lower()
                                new_file_path = file_path.with_suffix(f".{new_extension}")
                                file_path.rename(new_file_path)
                                console.print(f"Renamed {file_path} to {new_file_path}")

                progress.advance(task)
    console.rule(f"Task completed! {total_files} files repaired.")
