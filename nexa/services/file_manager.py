"""
Nexa AI — File Manager Service
Search, open, list, and inspect files on the PC.
"""

import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from nexa.utils.logger import get_logger

logger = get_logger(__name__)

_OS = platform.system()  # "Windows", "Linux", "Darwin"


class FileManager:
    """File operations for Nexa: search, open, list, info."""

    def search_files(
        self,
        query: str,
        directory: str = str(Path.home()),
        max_results: int = 20,
    ) -> list[str]:
        """
        Search for files by name (case-insensitive substring match).

        Args:
            query: File name or pattern to search for.
            directory: Root directory to search in (default: home folder).
            max_results: Maximum number of results to return.

        Returns:
            List of matching absolute file paths.
        """
        results: list[str] = []
        try:
            root = Path(directory)
            query_lower = query.lower()
            for path in root.rglob("*"):
                if query_lower in path.name.lower():
                    results.append(str(path))
                    if len(results) >= max_results:
                        break
        except PermissionError:
            pass
        except Exception as exc:
            logger.error(f"search_files error: {exc}")
        logger.info(f"🔍 Found {len(results)} file(s) matching '{query}'")
        return results

    def open_file(self, filepath: str) -> bool:
        """
        Open a file with the default system application.

        Args:
            filepath: Absolute or relative path to the file.

        Returns:
            True if the open command was issued successfully.
        """
        try:
            path = Path(filepath)
            if not path.exists():
                logger.warning(f"File not found: {filepath}")
                return False

            if _OS == "Windows":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif _OS == "Darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])

            logger.info(f"📂 Opened: {filepath}")
            return True
        except Exception as exc:
            logger.error(f"open_file error: {exc}")
            return False

    def list_files(self, directory: str = ".") -> list[str]:
        """
        List all files and directories in a folder.

        Args:
            directory: Path to the directory to list.

        Returns:
            Sorted list of entry names.
        """
        try:
            entries = sorted(os.listdir(directory))
            logger.info(f"📁 Listed {len(entries)} items in '{directory}'")
            return entries
        except Exception as exc:
            logger.error(f"list_files error: {exc}")
            return []

    def get_file_info(self, filepath: str) -> dict[str, Any]:
        """
        Return metadata about a file.

        Args:
            filepath: Path to the file.

        Returns:
            Dict with keys: name, size_kb, modified, type, exists.
        """
        try:
            path = Path(filepath)
            if not path.exists():
                return {"exists": False, "name": path.name}
            stat = path.stat()
            return {
                "exists": True,
                "name": path.name,
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "type": path.suffix or "folder" if path.is_dir() else "unknown",
            }
        except Exception as exc:
            logger.error(f"get_file_info error: {exc}")
            return {"exists": False, "name": filepath}


# Module-level singleton
file_manager = FileManager()
