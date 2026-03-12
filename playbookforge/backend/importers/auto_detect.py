"""
PlaybookForge - Auto-detect importer
Tries each registered importer's detect() method to identify the platform.
"""

from __future__ import annotations

from typing import Optional

from .base import BaseImporter


def auto_detect(content: str, importers: list[BaseImporter]) -> Optional[BaseImporter]:
    """
    Try each importer's detect() method and return the first match.

    Args:
        content: The raw file content to detect.
        importers: List of registered importer instances.

    Returns:
        The matching BaseImporter, or None if no match.
    """
    for importer in importers:
        try:
            if importer.detect(content):
                return importer
        except Exception:
            continue
    return None
