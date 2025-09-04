import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ProcessPoolExecutor # New import

import exiftool
from rich.console import Console
from rich.progress import Progress

from file_manager_meta.cache_manager import init_cache, get_cached_hashes, set_cached_hashes # New import

console = Console()

def _parse_date_from_filename(filename: str) -> Optional[datetime]:
    match = re.search(r'(\d{14})', filename)
    if match:
        try:
            dt_obj = datetime.strptime(match.group(1), '%Y%m%d%H%M%S')
            if 1900 <= dt_obj.year <= datetime.now().year + 5: # Validate year range
                return dt_obj
        except ValueError:
            pass # Fall through to other patterns

    # YYYYMMDD_HHMMSS or YYYYMMDD
    match = re.search(r'(\d{4}[-_]?\d{2}[-_]?\d{2})[_.-]?(\d{6})?', filename)
    if match:
        date_part = match.group(1).replace('-', '').replace('_', '').replace('.', '')
        time_part = match.group(2) # This might be None

        try:
            dt_format = '%Y%m%d'
            if time_part and len(time_part) == 6:
                dt_format += '%H%M%S'
                date_part += time_part
            dt_obj = datetime.strptime(date_part, dt_format)
            if 1900 <= dt_obj.year <= datetime.now().year + 5: # Validate year range
                return dt_obj
        except ValueError:
            pass # Fall through

    # DDMMYYYY_HHMMSS or DDMMYYYY
    match = re.search(r'(\d{2}[-_]?\d{2}[-_]?\d{4})[_.-]?(\d{6})?', filename)
    if match:
        date_part = match.group(1).replace('-', '').replace('_', '').replace('.', '')
        time_part = match.group(2) # This might be None

        try:
            dt_format = '%d%m%Y' # Assuming DDMMYYYY
            if time_part and len(time_part) == 6:
                dt_format += '%H%M%S'
                date_part += time_part
            dt_obj = datetime.strptime(date_part, dt_format)
            if 1900 <= dt_obj.year <= datetime.now().year + 5: # Validate year range
                return dt_obj
        except ValueError:
            pass # Fall through

    # YYYY.MM.DD_HHMMSS or YYYY.MM.DD
    match = re.search(r'(\d{4}\.\d{2}\.\d{2})[_.-]?(\d{6})?', filename)
    if match:
        date_part = match.group(1).replace('.', '')
        time_part = match.group(2) # This might be None

        try:
            dt_format = '%Y%m%d' # Assuming YYYY.MM.DD
            if time_part and len(time_part) == 6:
                dt_format += '%H%M%S'
                date_part += time_part
            dt_obj = datetime.strptime(date_part, dt_format)
            if 1900 <= dt_obj.year <= datetime.now().year + 5: # Validate year range
                return dt_obj
        except ValueError:
            pass # Fall through

    return None

def _process_file_for_metadata_update(file_path: Path, root_directory_for_cache: Path, dry_run: bool, tag: Optional[str], no_backup: bool, force: bool, verbose: bool):
    # Each process needs its own cache connection
    conn, _ = init_cache(root_directory_for_cache)
    try:
        stat_info = file_path.stat()
        cached_data = get_cached_hashes(conn, file_path, stat_info)

        filename_date = _parse_date_from_filename(file_path.name)
        if not filename_date:
            return "skipped", file_path.name, f"No date found in filename for {file_path.name}."

        current_metadata_date = None
        # Try to get metadata date from cache first
        if cached_data and cached_data.get('create_date'):
            try:
                current_metadata_date = datetime.strptime(cached_data['create_date'], '%Y:%m:%d %H:%M:%S')
            except ValueError:
                pass # Invalid cached date, will re-read with exiftool

        # If not in cache or invalid, read with exiftool
        if not current_metadata_date:
            with exiftool.ExifToolHelper() as et:
                metadata = et.get_tags(str(file_path), tags=['CreateDate', 'DateTimeOriginal', 'FileModifyDate'])
                if metadata and metadata[0]:
                    for date_tag in ['CreateDate', 'DateTimeOriginal', 'FileModifyDate']:
                        if date_tag in metadata[0]:
                            try:
                                date_str = metadata[0][date_tag].split('+')[0].strip()
                                current_metadata_date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                                break
                            except ValueError:
                                pass # Try next tag
            
            # Cache the newly read metadata dates
            if current_metadata_date:
                set_cached_hashes(conn, file_path, stat_info, {
                    "create_date": current_metadata_date.strftime('%Y:%m:%d %H:%M:%S'),
                    "date_time_original": current_metadata_date.strftime('%Y:%m:%d %H:%M:%S'),
                    "file_modify_date": current_metadata_date.strftime('%Y:%m:%d %H:%M:%S'),
                })


        if current_metadata_date and filename_date.date() == current_metadata_date.date() and not force:
            return "skipped", file_path.name, f"Dates already match for {file_path.name}."

        # Prepare date for ExifTool (YYYY:MM:DD HH:MM:SS format)
        new_date_str = filename_date.strftime('%Y:%m:%d %H:%M:%S')
        
        tags_to_write = {}
        if tag: # If a specific tag is requested
            tags_to_write[tag] = new_date_str
        else: # Otherwise, write to common creation date tags
            tags_to_write = {
                'CreateDate': new_date_str,
                'DateTimeOriginal': new_date_str,
                'FileModifyDate': new_date_str, # Also update file modification date
            }

        if dry_run:
            return "dry_run", file_path.name, f"Would update {file_path.name} with date and time: {new_date_str} (tags: {list(tags_to_write.keys())})." + (" (No backup would be created)." if no_backup else "")
        else:
            with exiftool.ExifToolHelper() as et: # Re-open ExifTool for writing
                exiftool_params = [] # Renamed to avoid confusion
                if no_backup:
                    exiftool_params.append("-overwrite_original")

                et.set_tags(str(file_path), tags_to_write, params=exiftool_params)
            
            # Update cache after successful write
            set_cached_hashes(conn, file_path, stat_info, {
                "create_date": new_date_str,
                "date_time_original": new_date_str,
                "file_modify_date": new_date_str,
            })
            return "updated", file_path.name, f"Successfully updated {file_path.name}."

    except exiftool.ExifToolException as e:
        # ExifToolException often contains more details in its message or stderr
        return "error", file_path.name, f" ExifTool error processing {file_path.name}: {e}"
    except Exception as e:
        return "error", file_path.name, f" Unexpected error processing {file_path.name}: {e}"
    finally:
        conn.close()

def update_metadata_date(paths: List[Path], dry_run: bool = False, tag: Optional[str] = None, no_backup: bool = False, force: bool = False, verbose: bool = False):
    console.print(f"Starting metadata date update for {len(paths)} paths...\n")

    # Determine the root directory for cache based on input paths
    root_directory_for_cache = None
    if paths:
        if paths[0].is_dir():
            root_directory_for_cache = paths[0]
        else:
            root_directory_for_cache = paths[0].parent
    
    if not root_directory_for_cache:
        console.print("[red]No valid paths provided for metadata update.[/red]")
        return

    files_to_process = []
    for input_path in paths:
        if input_path.is_file():
            files_to_process.append(input_path)
        elif input_path.is_dir():
            for dir_path, _, file_names in os.walk(input_path):
                for file_name in file_names:
                    files_to_process.append(Path(dir_path) / file_name)
    
    if not files_to_process:
        console.print("[yellow]No files found to process.[/yellow]")
        return

    updated_count = 0
    skipped_count = 0
    dry_run_count = 0
    error_count = 0

    with Progress() as progress:
        task = progress.add_task("[green]Processing files[/green]", total=len(files_to_process))
        
        # Use ProcessPoolExecutor for parallel processing
        with ProcessPoolExecutor() as executor:
            # Prepare arguments for each worker
            args = [(file_path, root_directory_for_cache, dry_run, tag, no_backup, force, verbose) for file_path in files_to_process]
            
            for result_type, file_name, message in executor.map(_process_file_for_metadata_update, *zip(*args)):
                progress.update(task, description=f"[green]Processing {file_name}[/green]")
                if result_type == "updated":
                    updated_count += 1
                    if verbose:
                        console.print(f"[green]{message}[/green]")
                elif result_type == "skipped":
                    skipped_count += 1
                    if verbose:
                        console.print(f"[dim]{message}[/dim]")
                elif result_type == "dry_run":
                    dry_run_count += 1
                    console.print(f"[yellow]{message}[/yellow]") # Always print dry run messages
                elif result_type == "error":
                    error_count += 1
                    console.print(f"[bold red]{message}[/bold red]") # Always print error messages
                progress.advance(task)
    
    console.print("\n[bold green]Metadata date update complete.[/bold green]")
    console.print(f"[green]Files updated:[/green] {updated_count}")
    console.print(f"[dim]Files skipped:[/dim] {skipped_count}")
    console.print(f"[yellow]Files in dry run:[/yellow] {dry_run_count}")
    console.print(f"[bold red]Files with errors:[/bold red] {error_count}")