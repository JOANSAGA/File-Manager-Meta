import sqlite3
import os
import hashlib
from pathlib import Path
import platform  # To detect OS for platform-specific cache dir

import typer
from rich.console import Console
from rich.table import Table

console = Console()


# Function to get platform-specific cache directory
def _get_cache_dir() -> Path:
    if platform.system() == "Windows":
        # LOCALAPPDATA is preferred for non-roaming data
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "file-manager-meta" / "cache"
    elif platform.system() == "Darwin":  # macOS
        return Path.home() / "Library" / "Caches" / "file-manager-meta"
    else:  # Linux and other Unix-like systems
        return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "file-manager-meta"


# Function to generate unique DB path for a given directory
def _get_cache_db_path(directory: Path) -> Path:
    cache_dir = _get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)  # Ensure cache directory exists

    # Use a hash of the absolute path of the analyzed directory for uniqueness
    dir_hash = hashlib.md5(str(directory.absolute()).encode('utf-8')).hexdigest()
    db_name = f"cache_{dir_hash}.db"
    return cache_dir / db_name


def init_cache(directory: Path) -> tuple[sqlite3.Connection, Path]:
    """Initializes the database for a given directory and returns a connection object and its path."""
    db_path = _get_cache_db_path(directory)
    try:
        conn = sqlite3.connect(db_path, timeout=30)
    except sqlite3.OperationalError as e:
        console.print(f"[bold red]Error connecting to cache database: {e}. This might be due to a locked database file. Try running 'file-manager-meta cache clear-all' to clear all caches.[/bold red]")
        raise typer.Exit(code=1)
    # Create table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS file_hashes (
            path TEXT PRIMARY KEY,
            mtime REAL NOT NULL,
            size INTEGER NOT NULL,
            md5 TEXT,
            sha1 TEXT,
            sha256 TEXT,
            exiftool_file_type TEXT,
            create_date TEXT,
            date_time_original TEXT,
            file_modify_date TEXT
        );
    """)
    conn.commit()
    return conn, db_path


def get_cached_hashes(conn: sqlite3.Connection, file_path: Path, stat_info) -> dict | None:
    """Retrieves cached hashes if the file is unchanged."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT mtime, size, md5, sha1, sha256, exiftool_file_type, create_date, date_time_original, file_modify_date FROM file_hashes WHERE path = ?",
        (str(file_path),)
    )
    row = cursor.fetchone()
    if row:
        mtime, size, md5, sha1, sha256, exiftool_file_type, create_date, date_time_original, file_modify_date = row
        # Check if file metadata matches the cached metadata
        if mtime == stat_info.st_mtime and size == stat_info.st_size:
            return {
                "md5": md5,
                "sha1": sha1,
                "sha256": sha256,
                "exiftool_file_type": exiftool_file_type,
                "create_date": create_date,
                "date_time_original": date_time_original,
                "file_modify_date": file_modify_date
            }
    return None


def set_cached_hashes(conn: sqlite3.Connection, file_path: Path, stat_info, hashes: dict):
    """Inserts or updates a file's hashes and ExifTool file type in the cache."""
    conn.execute(
        """REPLACE INTO file_hashes (path, mtime, size, md5, sha1, sha256, exiftool_file_type, create_date, date_time_original, file_modify_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(file_path),
            stat_info.st_mtime,
            stat_info.st_size,
            hashes.get("md5"),
            hashes.get("sha1"),
            hashes.get("sha256"),
            hashes.get("exiftool_file_type"),
            hashes.get("create_date"),
            hashes.get("date_time_original"),
            hashes.get("file_modify_date"),
        )
    )
    conn.commit()


def view_cache_contents(directory: Path):
    db_path = _get_cache_db_path(directory)

    if not db_path.exists():
        console.print(f"[red]No cache database found for directory: {directory}[/red]")
        return

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(file_hashes)")  # Get column info
        columns = [info[1] for info in cursor.fetchall()]  # Column names

        table = Table(title=f"Cache Contents for {directory}")
        for col in columns:
            table.add_column(col)

        cursor.execute("SELECT * FROM file_hashes")
        for row in cursor.fetchall():
            table.add_row(*[str(item) for item in row])

        console.print(table)

    except sqlite3.Error as e:
        console.print(f"[bold red]Error reading cache database: {e}[/bold red]")
    finally:
        conn.close()


def clear_cache(directory: Path):
    db_path = _get_cache_db_path(directory)

    if db_path.exists():
        try:
            os.remove(db_path)
            console.print(f"[green]Cache database deleted for directory: {directory}[/green]")
        except OSError as e:
            console.print(f"[bold red]Error deleting cache database {db_path}: {e}[/bold red]")
    else:
        console.print(f"[yellow]No cache database found for directory: {directory}[/yellow]")


def recreate_database(directory: Path):
    db_path = _get_cache_db_path(directory)
    if db_path.exists():
        try:
            # Ensure all connections to the database are closed before attempting to delete
            # This might require more sophisticated connection management in a real app
            # For now, we assume connections are managed externally or are short-lived.
            # If the file is locked, this deletion will fail.
            os.remove(db_path)
            console.print(f"[green]Existing cache database deleted for directory: {directory}[/green]")
        except OSError as e:
            console.print(f"[bold red]Error deleting existing cache database {db_path}: {e}[/bold red]")
            return

    # Re-initialize the database, which will create a new one with the latest schema
    conn, _ = init_cache(directory)
    conn.close()
    console.print(f"[green]New cache database created for directory: {directory}[/green]")


def clear_all_caches():
    cache_dir = _get_cache_dir()
    if not cache_dir.exists():
        console.print(f"[yellow]Cache directory does not exist: {cache_dir}[/yellow]")
        return

    deleted_count = 0
    for item in cache_dir.iterdir():
        if item.is_file() and item.name.startswith("cache_") and item.name.endswith(".db"):
            try:
                os.remove(item)
                console.print(f"[green]Deleted cache file: {item.name}[/green]")
                deleted_count += 1
            except OSError as e:
                console.print(f"[bold red]Error deleting cache file {item.name}: {e}[/bold red]")
    
    if deleted_count > 0:
        console.print(f"[green]Successfully cleared {deleted_count} cache files.[/green]")
    else:
        console.print(f"[yellow]No cache files found to clear in {cache_dir}.[/yellow]")


# Make _get_cache_db_path public for cli.py
get_cache_file_path = _get_cache_db_path
