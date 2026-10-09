import os
import hashlib
from typing import Dict, List, Tuple

def get_file_hash(filepath: str, block_size: int = 65536) -> str:
    """Calculates SHA-256 digest of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(block_size):
            hasher.update(chunk)
    return hasher.hexdigest()

class SyncManifest:
    """Represents local file tree state with hashes and timestamps."""

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def scan(self) -> Dict[str, dict]:
        """Scans the directory and returns {rel_path: {'hash': ..., 'size': ..., 'mtime': ...}}"""
        manifest = {}
        if not os.path.exists(self.root_dir):
            return manifest

        for root, dirs, files in os.walk(self.root_dir):
            # Ignore hidden dirs like .git, .p2p-sync
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.startswith("."):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, self.root_dir)
                try:
                    stat = os.stat(full_path)
                    manifest[rel_path] = {
                        "hash": get_file_hash(full_path),
                        "size": stat.st_size,
                        "mtime": stat.st_mtime
                    }
                except (OSError, PermissionError):
                    continue

        return manifest

    @staticmethod
    def diff(local_manifest: Dict[str, dict], remote_manifest: Dict[str, dict]) -> Tuple[List[str], List[str]]:
        """
        Calculates diff:
        - to_pull: files that remote has newer or missing locally
        - to_push: files that local has newer or missing remotely
        """
        to_pull = []
        to_push = []

        # Check files present in remote
        for rel_path, r_info in remote_manifest.items():
            if rel_path not in local_manifest:
                to_pull.append(rel_path)
            else:
                l_info = local_manifest[rel_path]
                if l_info["hash"] != r_info["hash"]:
                    if r_info.get("mtime", 0) > l_info.get("mtime", 0):
                        to_pull.append(rel_path)

        # Check files present locally
        for rel_path, l_info in local_manifest.items():
            if rel_path not in remote_manifest:
                to_push.append(rel_path)
            else:
                r_info = remote_manifest[rel_path]
                if l_info["hash"] != r_info["hash"]:
                    if l_info.get("mtime", 0) > r_info.get("mtime", 0):
                        to_push.append(rel_path)

        return to_pull, to_push
