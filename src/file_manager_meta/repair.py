import os
import exiftool
from pathlib import Path
import sqlite3 # For OperationalError
from typing import List # New import

from rich.console import Console
from rich.progress import Progress

from file_manager_meta.cache_manager import init_cache, get_cached_hashes, set_cached_hashes # Import cache functions

console = Console()

def repair_extension(paths: List[Path]): # Modified signature
    # Determine the root directory for cache based on input paths
    root_directory_for_cache = None
    if paths:
        if paths[0].is_dir():
            root_directory_for_cache = paths[0]
        else:
            root_directory_for_cache = paths[0].parent
    
    if not root_directory_for_cache:
        console.print("[red]No valid paths provided for repair.[/red]")
        return

    console.print(f"Starting extension repair for provided paths (using cache in [cyan]{root_directory_for_cache}[/cyan])...")

    conn, db_path = init_cache(root_directory_for_cache) # Use determined root
    console.print(f"Using cache database: [dim]{db_path}[/dim]")

    files_to_process_with_exiftool = []
    files_repaired_from_cache = []
    files_repaired_from_exiftool = []
    
    files_skipped_already_had_extension = []
    files_skipped_exiftool_failed = []
    files_skipped_due_to_error = []

    try:
        # --- Step 1: Collect files and check cache ---
        console.print("Step 1: Collecting files and checking cache for extensions...")
        all_files_to_process = [] # Renamed from all_files_in_dir
        
        for input_path in paths: # Iterate through input paths
            if input_path.is_file():
                # Skip hidden files
                if input_path.name.startswith('.'):
                    files_skipped_due_to_error.append(input_path) # Treat as skipped due to hidden
                    continue
                all_files_to_process.append(input_path)
            elif input_path.is_dir():
                for dir_path, dir_names, file_names in os.walk(input_path):
                    # Modify dir_names in-place to skip system/hidden directories
                    dir_names[:] = [d for d in dir_names if d not in ['System Volume Information', '$RECYCLE.BIN']]
                    dir_names[:] = [d for d in dir_names if not d.startswith('.')] # Skip hidden directories

                    for file_name in file_names:
                        file_path = Path(dir_path) / file_name
                        # Skip hidden files
                        if file_path.name.startswith('.'):
                            files_skipped_due_to_error.append(file_path) # Treat as skipped due to hidden
                            continue
                        all_files_to_process.append(file_path)
            else:
                console.print(f"[yellow]Skipping invalid path: {input_path}[/yellow]")

        total_files = len(all_files_to_process) # Use all_files_to_process
        if total_files == 0:
            console.print("[green]No files found to repair.[/green]")
            return

        with Progress() as progress:
            task_collect = progress.add_task("[green]Collecting files[/green]", total=total_files)
            for file_path in all_files_to_process: # Iterate through collected files
                if file_path.is_file() and not file_path.is_symlink():
                    if not file_path.suffix: # Only process files without extension
                        try:
                            stat_info = file_path.stat()
                            cached_data = get_cached_hashes(conn, file_path, stat_info)
                            if cached_data and cached_data.get("exiftool_file_type"):
                                files_repaired_from_cache.append((file_path, cached_data["exiftool_file_type"]))
                            else:
                                files_to_process_with_exiftool.append(file_path)
                        except (OSError, sqlite3.OperationalError) as e:
                            console.print(f"[bold red]Error accessing file or cache for {file_path}: {e}[/bold red]")
                            files_skipped_due_to_error.append(file_path)
                    else:
                        files_skipped_already_had_extension.append(file_path) # Skip files that already have an extension
                else:
                    files_skipped_due_to_error.append(file_path) # Non-files or symlinks treated as errors for repair
                progress.advance(task_collect)

        # --- Step 2: Batch process files with ExifTool ---
        if files_to_process_with_exiftool:
            console.print(f"Step 2: Processing {len(files_to_process_with_exiftool)} files with ExifTool...\n")
            exiftool_results = {}
            with Progress() as progress:
                task_exiftool = progress.add_task("[green]Running ExifTool[/green]", total=len(files_to_process_with_exiftool))
                try:
                    with exiftool.ExifToolHelper() as et:
                        metadata_list = et.get_tags([str(f) for f in files_to_process_with_exiftool], tags=['FileTypeExtension'])
                        for m in metadata_list:
                            source_file = m.get('SourceFile')
                            file_type_ext = m.get('File:FileTypeExtension')
                            if source_file and file_type_ext:
                                exiftool_results[Path(source_file)] = file_type_ext.lower()
                            progress.advance(task_exiftool)
                except Exception as e:
                    console.print(f"[bold red]Error running ExifTool: {e}[/bold red]")
                    console.print("[yellow]Please ensure ExifTool is installed and in your system's PATH.[/yellow]")
                    files_skipped_exiftool_failed.extend(files_to_process_with_exiftool) # Mark all as skipped

            # Update cache and prepare for renaming
            for file_path in files_to_process_with_exiftool:
                new_extension = exiftool_results.get(file_path)
                if new_extension:
                    try:
                        stat_info = file_path.stat()
                        set_cached_hashes(conn, file_path, stat_info, {"exiftool_file_type": new_extension})
                        files_repaired_from_exiftool.append((file_path, new_extension))
                    except (OSError, sqlite3.OperationalError) as e:
                        console.print(f"[bold red]Error caching result for {file_path}: {e}[/bold red]")
                        files_skipped_due_to_error.append(file_path)
                else:
                    files_skipped_exiftool_failed.append(file_path) # ExifTool couldn't determine type

        # --- Step 3: Perform renaming and report ---
        console.print("Step 3: Renaming files...")
        renamed_count = 0
        with Progress() as progress:
            task_rename = progress.add_task("[green]Renaming files[/green]", total=len(files_repaired_from_cache) + len(files_repaired_from_exiftool))
            
            for file_path, new_extension in files_repaired_from_cache + files_repaired_from_exiftool:
                try:
                    new_file_path = file_path.with_suffix(f".{new_extension}")
                    file_path.rename(new_file_path)
                    console.print(f"Renamed [cyan]{file_path.name}[/cyan] to [green]{new_file_path.name}[/green] (Source: {'Cache' if (file_path, new_extension) in files_repaired_from_cache else 'ExifTool'})")
                    renamed_count += 1
                except OSError as e:
                    console.print(f"[bold red]Error renaming {file_path.name}: {e}[/bold red]")
                    files_skipped_due_to_error.append(file_path) # Add to error list
                progress.advance(task_rename)

        console.rule(f"Repair Task Completed")
        console.print(f"[green]Files renamed:[/green] {renamed_count}")
        
        # Report granular skipped counts
        if files_skipped_already_had_extension:
            console.print(f"[yellow]Files skipped (already had extension):[/yellow] {len(files_skipped_already_had_extension)}")
        if files_skipped_exiftool_failed:
            console.print(f"[yellow]Files skipped (ExifTool could not determine type):[/yellow] {len(files_skipped_exiftool_failed)}")
        if files_skipped_due_to_error:
            console.print(f"[red]Files skipped (due to errors):[/red] {len(files_skipped_due_to_error)}")

    finally:
        conn.close()
        console.print("[dim]Cache connection closed.[/dim]")

        # Add summary
        total_processed = renamed_count + len(files_skipped_already_had_extension) + len(files_skipped_exiftool_failed) + len(files_skipped_due_to_error)
        console.rule("Repair Task Summary")
        console.print(f"[green]Total files considered:[/green] {total_files}")
        console.print(f"[green]Files successfully repaired:[/green] {renamed_count}")
        if files_skipped_already_had_extension:
            console.print(f"[yellow]Files skipped (already had extension):[/yellow] {len(files_skipped_already_had_extension)}")
        if files_skipped_exiftool_failed:
            console.print(f"[yellow]Files skipped (ExifTool could not determine type):[/yellow] {len(files_skipped_exiftool_failed)}")
        if files_skipped_due_to_error:
            console.print(f"[red]Files skipped (due to errors):[/red] {len(files_skipped_due_to_error)}")
