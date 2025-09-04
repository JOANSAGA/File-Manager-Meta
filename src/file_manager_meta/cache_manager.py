import sqlite3
import os
import hashlib
from pathlib import Path
import platform # To detect OS for platform-specific cache dir

# Function to get platform-specific cache directory
def _get_cache_dir() -> Path:
    if platform.system() == "Windows":
        # LOCALAPPDATA is preferred for non-roaming data
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "file-manager-meta" / "cache"
    elif platform.system() == "Darwin": # macOS
        return Path.home() / "Library" / "Caches" / "file-manager-meta"
    else: # Linux and other Unix-like systems
        return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "file-manager-meta"

# Function to generate unique DB path for a given directory
def _get_cache_db_path(directory: Path) -> Path:
    cache_dir = _get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True) # Ensure cache directory exists

    # Use a hash of the absolute path of the analyzed directory for uniqueness
    dir_hash = hashlib.md5(str(directory.absolute()).encode('utf-8')).hexdigest()
    db_name = f"cache_{dir_hash}.db"
    return cache_dir / db_name

def init_cache(directory: Path) -> tuple[sqlite3.Connection, Path]:
    """Initializes the database for a given directory and returns a connection object and its path."""
    db_path = _get_cache_db_path(directory)
    conn = sqlite3.connect(db_path)
    # Create table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS file_hashes (
            path TEXT PRIMARY KEY,
            mtime REAL NOT NULL,
            size INTEGER NOT NULL,
            md5 TEXT,
            sha1 TEXT,
            sha256 TEXT
        );
    """)
    conn.commit()
    return conn, db_path

def get_cached_hashes(conn: sqlite3.Connection, file_path: Path, stat_info) -> dict | None:
    """Retrieves cached hashes if the file is unchanged."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT mtime, size, md5, sha1, sha256 FROM file_hashes WHERE path = ?",
        (str(file_path),)
    )
    row = cursor.fetchone()
    if row:
        mtime, size, md5, sha1, sha256 = row
        # Check if file metadata matches the cached metadata
        if mtime == stat_info.st_mtime and size == stat_info.st_size:
            return {"md5": md5, "sha1": sha1, "sha256": sha256}
    return None

def set_cached_hashes(conn: sqlite3.Connection, file_path: Path, stat_info, hashes: dict):
    """Inserts or updates a file's hashes in the cache."""
    conn.execute(
        """REPLACE INTO file_hashes (path, mtime, size, md5, sha1, sha256)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            str(file_path),
            stat_info.st_mtime,
            stat_info.st_size,
            hashes.get("md5"),
            hashes.get("sha1"),
            hashes.get("sha256"),
        )
    )
    conn.commit()