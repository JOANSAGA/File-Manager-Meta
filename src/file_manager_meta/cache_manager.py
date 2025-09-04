import sqlite3
from pathlib import Path

DB_NAME = ".file_manager_cache.db"

def init_cache(directory: Path):
    """Initializes the database and returns a connection object."""
    db_path = directory / DB_NAME
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
    return conn

def get_cached_hashes(conn: sqlite3.Connection, file_path: Path, stat_info):
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
