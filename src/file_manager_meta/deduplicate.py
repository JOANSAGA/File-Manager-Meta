import os
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table

from file_manager_meta.hashes import calculate_hashes
from file_manager_meta.cache_manager import init_cache

def format_size(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    if size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    return f"{size_in_bytes / (1024 * 1024):.1f} MB"

def format_timestamp(ts):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def deduplicate_files(directory: Path, dry_run: bool, keep_rule: str):
    console = Console()
    console.print(f"Starting duplicate scan in [cyan]{directory}[/cyan]...")

    conn, db_path = init_cache(directory)
    console.print(f"Using cache database: [dim]{db_path}[/dim]")
    try:
        # --- Step 1: Group files by size to pre-filter ---
        console.print("Step 1: Finding potential duplicates by size...")
        files_by_size = defaultdict(list)
        for dir_path, _, file_names in os.walk(directory):
            for file_name in file_names:
                file_path = Path(dir_path) / file_name
                try:
                    if file_path.is_file() and not file_path.is_symlink():
                        size = file_path.stat().st_size
                        if size > 0:
                            files_by_size[size].append(file_path)
                except OSError:
                    continue

        # --- Step 2: Hash only the files that have potential duplicates ---
        console.print("Step 2: Calculating hashes for same-sized files (using cache)...")
        hash_map = defaultdict(list)
        for size, files in files_by_size.items():
            if len(files) > 1:
                for file_path in files:
                    hashes = calculate_hashes(file_path, conn)
                    md5_hash = hashes.get("md5")
                    if md5_hash:
                        hash_map[md5_hash].append(file_path)

        duplicate_sets = [files for files in hash_map.values() if len(files) > 1]

        if not duplicate_sets:
            console.print("[green]No duplicate files found.[/green]")
            return

        # --- Step 3: Report or Delete ---
        if dry_run:
            console.print("\n[yellow]Dry run mode enabled. The following actions would be taken:[/yellow]\n")
            total_to_delete = 0
            for i, files in enumerate(duplicate_sets):
                table = Table(title=f"Duplicate Set {i + 1} (Size: {format_size(files[0].stat().st_size)})")
                table.add_column("Status", style="bold")
                table.add_column("File Path", style="cyan", no_wrap=True)
                table.add_column("Created On")

                if keep_rule == 'oldest':
                    files.sort(key=lambda f: f.stat().st_ctime)
                
                file_to_keep = files[0]
                table.add_row(
                    "[green]KEEP[/green]",
                    str(file_to_keep),
                    format_timestamp(file_to_keep.stat().st_ctime)
                )

                for file_to_delete in files[1:]:
                    total_to_delete += 1
                    table.add_row(
                        "[red]DELETE[/red]",
                        str(file_to_delete),
                        format_timestamp(file_to_delete.stat().st_ctime)
                    )
                
                console.print(table)
            
            console.print(f"\n[yellow]Dry run complete. {total_to_delete} files would be deleted.[/yellow]")

        else:
            files_to_delete = []
            for files in duplicate_sets:
                if keep_rule == 'oldest':
                    files.sort(key=lambda f: f.stat().st_ctime)
                files_to_delete.extend(files[1:])

            if not files_to_delete:
                console.print("[bold yellow]No files to delete.[/bold yellow]")
                return

            table = Table(title="Files to be Permanently Deleted")
            table.add_column("File Path", style="red")
            for file_path in files_to_delete:
                table.add_row(str(file_path))
            console.print(table)
            
            console.print(f"\nProceeding with deletion of {len(files_to_delete)} files...")
            try:
                for file_path in files_to_delete:
                    os.remove(file_path)
                console.print("\n[green]Deletion complete.[/green]")
            except Exception as e:
                console.print(f"\n[bold red]An error occurred during deletion: {e}[/bold red]")
    finally:
        conn.close()
        console.print("[dim]Cache connection closed.[/dim]")