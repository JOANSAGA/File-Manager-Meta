import os
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from concurrent.futures import ProcessPoolExecutor # New import

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

# Helper function for multiprocessing
def _process_file_for_deduplication(file_path: Path, root_directory: Path):
    # Each process needs its own connection
    conn, _ = init_cache(root_directory) # _get_cache_db_path is called inside init_cache
    try:
        hashes = calculate_hashes(file_path, conn)
        return file_path, hashes.get("md5")
    finally:
        conn.close()

def deduplicate_files(directory: Path, dry_run: bool, keep_rule: str):
    console = Console()
    console.print(f"Starting duplicate scan in [cyan]{directory}[/cyan]...\n")

    # Initialize cache in main process to ensure DB file exists
    conn, db_path = init_cache(directory)
    conn.close() # Close immediately, workers will open their own
    console.print(f"Using cache database: [dim]{db_path}[/dim]")

    # --- Step 1: Collect all file paths ---
    console.print("Step 1: Collecting all file paths...")
    all_file_paths = []
    for dir_path, dir_names, file_names in os.walk(directory):
        # Modify dir_names in-place to skip system/hidden directories
        dir_names[:] = [d for d in dir_names if d not in ['System Volume Information', '$RECYCLE.BIN']]
        dir_names[:] = [d for d in dir_names if not d.startswith('.')] # Skip hidden directories

        for file_name in file_names:
            file_path = Path(dir_path) / file_name
            # Skip hidden files
            if file_path.name.startswith('.'):
                continue

            try:
                if file_path.is_file() and not file_path.is_symlink():
                    all_file_paths.append(file_path)
            except OSError:
                continue
    
    if not all_file_paths:
        console.print("[green]No files found to scan.[/green]")
        return

    # --- Step 2: Group files by size ---
    console.print("Step 2: Grouping files by size...")
    files_by_size = defaultdict(list)
    for file_path in all_file_paths:
        try:
            file_size = file_path.stat().st_size
            files_by_size[file_size].append(file_path)
        except OSError:
            continue

    # Filter out unique files (those with unique sizes)
    candidate_files_for_hashing = []
    for size, files in files_by_size.items():
        if len(files) > 1:
            candidate_files_for_hashing.extend(files)
    
    if not candidate_files_for_hashing:
        console.print("[green]No potential duplicate files found based on size.[/green]")
        return

    # --- Step 3: Calculate hashes in parallel ---
    console.print("Step 3: Calculating hashes for candidate files (in parallel, using cache)...")
    hash_map = defaultdict(list)
    
    # Use ProcessPoolExecutor for parallel hashing
    with ProcessPoolExecutor() as executor:
        # Submit tasks and collect results
        # Pass root_directory to each worker so they can init their own cache
        results = executor.map(_process_file_for_deduplication, candidate_files_for_hashing, [directory] * len(candidate_files_for_hashing))
        
        for file_path, md5_hash in results:
            if md5_hash:
                hash_map[md5_hash].append(file_path)

    # --- Step 4: Identify duplicate sets and report/delete ---
    duplicate_sets = [files for files in hash_map.values() if len(files) > 1]

    # Calculate total files to delete (or would be deleted) for summary
    total_files_to_delete_count = sum(len(files) - 1 for files in duplicate_sets)

    if not duplicate_sets:
        console.print("[green]No duplicate files found.[/green]")
        return

    if dry_run:
        # --- Detailed Dry Run Report ---
        console.print("\n[yellow]Dry run mode enabled. The following actions would be taken:[/yellow]\n")
        for i, files in enumerate(duplicate_sets):
            table = Table(title=f"Duplicate Set {i + 1} (Size: {format_size(files[0].stat().st_size)})\n")
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
                table.add_row(
                    "[red]DELETE[/red]",
                    str(file_to_delete),
                    format_timestamp(file_to_delete.stat().st_ctime)
                )
            
            console.print(table)
        
        console.print(f"\n[yellow]Dry run complete. {total_files_to_delete_count} files would be deleted.[/yellow]")

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
    
    # Summary at the end
    console.rule("Deduplication Task Summary")
    console.print(f"[green]Total files scanned:[/green] {len(all_file_paths)}")
    console.print(f"[green]Duplicate sets found:[/green] {len(duplicate_sets)}")
    if total_files_to_delete_count > 0:
        if dry_run:
            console.print(f"[yellow]Files that would be deleted:[/yellow] {total_files_to_delete_count}")
        else:
            console.print(f"[green]Files successfully deleted:[/green] {len(files_to_delete)}")
    else:
        console.print("[green]No files were deleted.[/green]")