"""
PlaybookForge — Playbook Library Manager.
File-based JSON storage for pre-loaded and user-created CACAO playbooks.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default storage path
DEFAULT_LIBRARY_DIR = Path(__file__).parent.parent.parent / "library"


class PlaybookEntry:
    """A playbook in the library with metadata."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        source_platform: str,
        source_repo: str,
        source_file: str,
        playbook_types: list[str],
        step_count: int,
        action_count: int,
        tags: list[str],
        mitre_techniques: list[str],
        cacao_playbook: dict,
        created_at: str | None = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.source_platform = source_platform
        self.source_repo = source_repo
        self.source_file = source_file
        self.playbook_types = playbook_types
        self.step_count = step_count
        self.action_count = action_count
        self.tags = tags
        self.mitre_techniques = mitre_techniques
        self.cacao_playbook = cacao_playbook
        self.created_at = created_at or datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_platform": self.source_platform,
            "source_repo": self.source_repo,
            "source_file": self.source_file,
            "playbook_types": self.playbook_types,
            "step_count": self.step_count,
            "action_count": self.action_count,
            "tags": self.tags,
            "mitre_techniques": self.mitre_techniques,
            "cacao_playbook": self.cacao_playbook,
            "created_at": self.created_at,
        }

    def to_summary(self) -> dict:
        """Return metadata only (no full playbook body)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_platform": self.source_platform,
            "source_repo": self.source_repo,
            "playbook_types": self.playbook_types,
            "step_count": self.step_count,
            "action_count": self.action_count,
            "tags": self.tags,
            "mitre_techniques": self.mitre_techniques,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PlaybookEntry:
        return cls(**data)


class PlaybookLibrary:
    """File-based playbook library. Each playbook is stored as a JSON file."""

    def __init__(self, library_dir: Path | str | None = None):
        self.library_dir = Path(library_dir) if library_dir else DEFAULT_LIBRARY_DIR
        self.library_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, dict] = {}
        self._index_file = self.library_dir / "_index.json"
        self._lock = threading.Lock()
        self._load_index()

    def _load_index(self) -> None:
        """Load the index file for fast listing."""
        with self._lock:
            if self._index_file.exists():
                try:
                    with open(self._index_file, "r", encoding="utf-8") as f:
                        self._index = json.load(f)
                except (json.JSONDecodeError, IOError, OSError, ValueError) as e:
                    logger.warning("Failed to load library index: %s", e)
                    self._index = {}
                    self._rebuild_index()
            else:
                self._rebuild_index()

    def _save_index(self) -> None:
        """Persist the index to disk (thread-safe with atomic write)."""
        with self._lock:
            try:
                tmp_file = self._index_file.with_suffix(".tmp")
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump(self._index, f, indent=2, ensure_ascii=False)
                tmp_file.replace(self._index_file)
            except (IOError, OSError) as e:
                logger.error("Failed to save library index: %s", e)

    def _rebuild_index(self) -> None:
        """Rebuild index from all JSON files in the library directory."""
        self._index = {}
        for path in self.library_dir.glob("*.json"):
            if path.name.startswith("_"):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entry = PlaybookEntry.from_dict(data)
                self._index[entry.id] = entry.to_summary()
            except Exception as e:
                logger.warning("Failed to index %s: %s", path.name, e)
        self._save_index()

    def add(self, entry: PlaybookEntry) -> str:
        """Add a playbook to the library. Returns the entry ID."""
        filepath = self.library_dir / f"{entry.id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(entry.to_dict(), f, indent=2, ensure_ascii=False)
        self._index[entry.id] = entry.to_summary()
        self._save_index()
        return entry.id

    def get(self, playbook_id: str) -> PlaybookEntry | None:
        """Get a full playbook entry by ID."""
        filepath = self.library_dir / f"{playbook_id}.json"
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PlaybookEntry.from_dict(data)

    def list_all(
        self,
        platform: str | None = None,
        search: str | None = None,
        tag: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """List playbooks with optional filters."""
        entries = list(self._index.values())

        if platform:
            entries = [e for e in entries if e.get("source_platform") == platform]

        if tag:
            tag_lower = tag.lower()
            entries = [
                e for e in entries
                if any(tag_lower in t.lower() for t in e.get("tags", []))
            ]

        if search:
            search_lower = search.lower()
            entries = [
                e for e in entries
                if search_lower in e.get("name", "").lower()
                or search_lower in e.get("description", "").lower()
                or any(search_lower in t.lower() for t in e.get("tags", []))
            ]

        total = len(entries)
        entries = entries[offset : offset + limit]

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "playbooks": entries,
        }

    def count(self) -> int:
        return len(self._index)

    def platforms(self) -> dict[str, int]:
        """Return count of playbooks per source platform."""
        counts: dict[str, int] = {}
        for entry in self._index.values():
            platform = entry.get("source_platform", "unknown")
            counts[platform] = counts.get(platform, 0) + 1
        return counts

    def tags(self) -> dict[str, int]:
        """Return all tags with their counts."""
        tag_counts: dict[str, int] = {}
        for entry in self._index.values():
            for t in entry.get("tags", []):
                tag_counts[t] = tag_counts.get(t, 0) + 1
        return dict(sorted(tag_counts.items(), key=lambda x: -x[1]))

    def delete(self, playbook_id: str) -> bool:
        """Delete a playbook from the library."""
        filepath = self.library_dir / f"{playbook_id}.json"
        if filepath.exists():
            filepath.unlink()
        if playbook_id in self._index:
            del self._index[playbook_id]
            self._save_index()
            return True
        return False


# Global library instance
library = PlaybookLibrary()
