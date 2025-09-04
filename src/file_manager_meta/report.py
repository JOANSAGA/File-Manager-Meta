from collections import defaultdict
import os
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from file_manager_meta.hashes import calculate_hashes
from file_manager_meta.cache_manager import init_cache

def generate_report(directory: Path, output: Path = None):
    """Generates a detailed report with file metadata and integrity hashes, and lists duplicate files."""

    console = Console()
    if output and output.suffix != ".html":
        console.print("Output file must have a .html extension", style="red")
        raise typer.Exit(code=1)

    report_console = Console(record=True) if output else console
    conn, db_path = init_cache(directory)
    console.print(f"Using cache database: [dim]{db_path}[/dim]")

    try:
        # 1. Collect and group files by directory
        files_by_directory = defaultdict(list)
        for dir_path, _, file_names in os.walk(directory):
            if file_names:
                for file_name in file_names:
                    files_by_directory[Path(dir_path)].append(file_name)

        hash_map = defaultdict(list)

        # 2. Process and print tables for each directory
        console.print("Generating report (using cache)...")
        for dir_path in sorted(files_by_directory.keys()):
            relative_dir_path = dir_path.relative_to(directory)
            table_title = f"File Hashes in ./{relative_dir_path}" if str(relative_dir_path) != "." else "File Hashes in Root Directory"

            table = Table(title=table_title)
            table.add_column("File", style="cyan")
            table.add_column("MD5", style="magenta")
            table.add_column("SHA-1", style="green")
            table.add_column("SHA-256", style="yellow")

            for file_name in sorted(files_by_directory[dir_path]):
                file_path = dir_path / file_name
                if file_path.is_file():
                    hashes = calculate_hashes(file_path, conn)
                    table.add_row(
                        file_name,
                        hashes.get("md5"),
                        hashes.get("sha1"),
                        hashes.get("sha256"),
                    )
                    if hashes.get("md5"):
                        relative_file_path = str(file_path.relative_to(directory))
                        hash_map[hashes["md5"]].append(relative_file_path)
            
            report_console.print(table)

            if output:
                console.print(f"Processed directory [cyan]./{relative_dir_path}[/cyan]... OK", style="dim")

        # 3. Duplicates Table
        duplicates_table = Table(title="Duplicate File Sets")
        duplicates_table.add_column("Files in Set", no_wrap=True)

        has_duplicates = False
        for files in hash_map.values():
            if len(files) > 1:
                has_duplicates = True
                duplicates_table.add_row("\n".join(sorted(files)))
                duplicates_table.add_section()

        if has_duplicates:
            report_console.print(duplicates_table)
        else:
            report_console.print("No duplicate files found.", style="green")

        if output:
            html_content = report_console.export_html()
            custom_css = "<style> body, code { font-size: 0.9em; } </style>"
            html_content = html_content.replace("</head>", f"{custom_css}</head>")
            with open(output, "w", encoding="utf-8") as f:
                f.write(html_content)
            console.print(f"Report saved to {output}", style="green")

    finally:
        conn.close()
        console.print("[dim]Cache connection closed.[/dim]")