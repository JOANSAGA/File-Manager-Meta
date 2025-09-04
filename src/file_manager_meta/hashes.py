import hashlib
import sqlite3
from pathlib import Path

from file_manager_meta.cache_manager import get_cached_hashes, set_cached_hashes

def _calculate_hashes_from_file(file_path: Path) -> dict:
    """Calculates MD5, SHA-1, and SHA-256 hashes for a given file."""
    hashes = {
        "md5": hashlib.md5(),
        "sha1": hashlib.sha1(),
        "sha256": hashlib.sha256(),
    }
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                for algorithm in hashes.values():
                    algorithm.update(chunk)
        return {name: algorithm.hexdigest() for name, algorithm in hashes.items()}
    except (IOError, OSError):
        # Return empty dict if file can't be read
        return {}

def calculate_hashes(file_path: Path, conn: sqlite3.Connection) -> dict:
    """
    Gets hashes for a file, using the cache if possible.
    """
    try:
        stat_info = file_path.stat()
    except (IOError, OSError):
        return {}

    # 1. Try to get hashes from cache
    cached_hashes = get_cached_hashes(conn, file_path, stat_info)
    if cached_hashes:
        return cached_hashes

    # 2. If not in cache or changed, calculate fresh hashes
    fresh_hashes = _calculate_hashes_from_file(file_path)

    # 3. Store the new hashes in the cache
    if fresh_hashes:
        set_cached_hashes(conn, file_path, stat_info, fresh_hashes)
    
    return fresh_hashes