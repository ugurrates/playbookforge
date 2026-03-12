"""
PlaybookForge — File Storage Manager.

Simple file-based storage for user-uploaded documents (PDFs, etc.).
Follows the same pattern as library.py with metadata tracking.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_STORAGE_DIR = Path(__file__).parent.parent.parent / "file_storage"


@dataclass
class FileMetadata:
    """Metadata for a stored file."""
    id: str
    filename: str
    original_filename: str
    description: str = ""
    playbook_id: Optional[str] = None
    file_size: int = 0
    content_type: str = "application/octet-stream"
    uploaded_at: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> FileMetadata:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class FileStorageManager:
    """Manages uploaded files with metadata tracking."""

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        self.storage_dir = Path(storage_dir) if storage_dir else DEFAULT_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_file = self.storage_dir / "_metadata.json"
        self._index: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._load_index()

    def _load_index(self) -> None:
        """Load metadata index from disk."""
        with self._lock:
            if self._metadata_file.exists():
                try:
                    with open(self._metadata_file, "r", encoding="utf-8") as f:
                        self._index = json.load(f)
                except (json.JSONDecodeError, IOError, OSError, ValueError) as e:
                    logger.warning("Failed to load file metadata: %s", e)
                    self._index = {}

    def _save_index(self) -> None:
        """Persist metadata index to disk (thread-safe)."""
        with self._lock:
            try:
                tmp_file = self._metadata_file.with_suffix(".tmp")
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump(self._index, f, indent=2, ensure_ascii=False)
                tmp_file.replace(self._metadata_file)
            except (IOError, OSError) as e:
                logger.error("Failed to save file metadata: %s", e)

    def save_file(
        self,
        content: bytes,
        original_filename: str,
        content_type: str = "application/pdf",
        description: str = "",
        playbook_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> FileMetadata:
        """Save an uploaded file and return its metadata."""
        file_id = f"file-{uuid.uuid4().hex[:12]}"
        # Sanitize and create safe filename
        ext = Path(original_filename).suffix or ".pdf"
        safe_name = f"{file_id}{ext}"

        file_path = self.storage_dir / safe_name
        file_path.write_bytes(content)

        meta = FileMetadata(
            id=file_id,
            filename=safe_name,
            original_filename=original_filename,
            description=description,
            playbook_id=playbook_id,
            file_size=len(content),
            content_type=content_type,
            uploaded_at=datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            tags=tags or [],
        )

        self._index[file_id] = meta.to_dict()
        self._save_index()
        return meta

    def get_file(self, file_id: str) -> Optional[tuple[FileMetadata, bytes]]:
        """Get file metadata and content by ID. Returns None if not found."""
        if file_id not in self._index:
            return None

        meta = FileMetadata.from_dict(self._index[file_id])
        file_path = self.storage_dir / meta.filename

        if not file_path.exists():
            return None

        return meta, file_path.read_bytes()

    def get_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata only."""
        if file_id not in self._index:
            return None
        return FileMetadata.from_dict(self._index[file_id])

    def list_files(
        self,
        playbook_id: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> list[FileMetadata]:
        """List files, optionally filtered."""
        results = []
        for data in self._index.values():
            meta = FileMetadata.from_dict(data)
            if playbook_id and meta.playbook_id != playbook_id:
                continue
            if content_type and meta.content_type != content_type:
                continue
            results.append(meta)

        # Sort by upload date descending
        results.sort(key=lambda m: m.uploaded_at, reverse=True)
        return results

    def delete_file(self, file_id: str) -> bool:
        """Delete a file and its metadata. Returns True if deleted."""
        if file_id not in self._index:
            return False

        meta = FileMetadata.from_dict(self._index[file_id])
        file_path = self.storage_dir / meta.filename

        # Remove file from disk
        if file_path.exists():
            file_path.unlink()

        # Remove from index
        del self._index[file_id]
        self._save_index()
        return True


# Global singleton
file_storage = FileStorageManager()
