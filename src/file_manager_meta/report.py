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

    files_by_directory = defaultdict(list)

    try:
        # 1. Collect and group files by directory
        all_file_paths = []
        for dir_path, dir_names, file_names in os.walk(directory):
            # Modify dir_names in-place to skip system/hidden directories
            dir_names[:] = [d for d in dir_names if d not in ['System Volume Information', '$RECYCLE.BIN']]
            dir_names[:] = [d for d in dir_names if not d.startswith('.')] # Skip hidden directories

            if file_names:
                for file_name in file_names:
                    file_path = Path(dir_path) / file_name
                    # Skip hidden files
                    if file_path.name.startswith('.'):
                        continue

                    try:
                        if file_path.is_file() and not file_path.is_symlink():
                            all_file_paths.append(file_path)
                            files_by_directory[Path(dir_path)].append(file_name)
                    except OSError:
                        continue

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
        
        # Add summary
        total_files_processed = len(all_file_paths) # From Step 2
        total_duplicate_sets = len([files for files in hash_map.values() if len(files) > 1]) # From Step 3

        console.rule("Report Task Summary")
        console.print(f"[green]Total files scanned:[/green] {total_files_processed}")
        console.print(f"[green]Duplicate sets found:[/green] {total_duplicate_sets}")
        if output:
            console.print(f"[green]Report saved to:[/green] {output}")