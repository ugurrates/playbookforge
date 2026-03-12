"""Tests for PlaybookForge File Storage Manager."""

import pytest
import tempfile
from pathlib import Path
from backend.pdf.file_storage import FileStorageManager


@pytest.fixture
def storage(tmp_path):
    """Create a FileStorageManager with a temporary directory."""
    return FileStorageManager(storage_dir=tmp_path)


class TestFileStorage:
    def test_save_and_get(self, storage):
        """Should save a file and retrieve it."""
        content = b"Hello, PlaybookForge!"
        meta = storage.save_file(
            content=content,
            original_filename="test.pdf",
            content_type="application/pdf",
            description="A test file",
        )

        assert meta.id.startswith("file-")
        assert meta.original_filename == "test.pdf"
        assert meta.content_type == "application/pdf"
        assert meta.file_size == len(content)
        assert meta.description == "A test file"

        # Retrieve
        result = storage.get_file(meta.id)
        assert result is not None
        retrieved_meta, retrieved_content = result
        assert retrieved_content == content
        assert retrieved_meta.id == meta.id

    def test_list_files(self, storage):
        """Should list all files."""
        storage.save_file(b"file1", "doc1.pdf")
        storage.save_file(b"file2", "doc2.pdf")
        storage.save_file(b"file3", "doc3.txt", content_type="text/plain")

        files = storage.list_files()
        assert len(files) == 3

    def test_list_files_by_playbook_id(self, storage):
        """Should filter files by playbook_id."""
        storage.save_file(b"file1", "a.pdf", playbook_id="pb-001")
        storage.save_file(b"file2", "b.pdf", playbook_id="pb-002")
        storage.save_file(b"file3", "c.pdf", playbook_id="pb-001")

        files = storage.list_files(playbook_id="pb-001")
        assert len(files) == 2
        assert all(f.playbook_id == "pb-001" for f in files)

    def test_delete_file(self, storage):
        """Should delete a file and its metadata."""
        meta = storage.save_file(b"to delete", "delete_me.pdf")

        assert storage.get_file(meta.id) is not None
        assert storage.delete_file(meta.id) is True
        assert storage.get_file(meta.id) is None
        assert storage.delete_file(meta.id) is False  # already deleted

    def test_delete_nonexistent(self, storage):
        """Should return False for nonexistent file."""
        assert storage.delete_file("file-nonexistent") is False

    def test_metadata_persistence(self, tmp_path):
        """Metadata should persist across manager instances."""
        storage1 = FileStorageManager(storage_dir=tmp_path)
        meta = storage1.save_file(b"persistent", "persist.pdf", description="keep me")

        # Create new instance, should load existing metadata
        storage2 = FileStorageManager(storage_dir=tmp_path)
        result = storage2.get_file(meta.id)
        assert result is not None
        retrieved_meta, retrieved_content = result
        assert retrieved_content == b"persistent"
        assert retrieved_meta.description == "keep me"

    def test_get_metadata_only(self, storage):
        """Should retrieve metadata without file content."""
        meta = storage.save_file(b"content", "test.pdf", description="meta only")

        retrieved = storage.get_metadata(meta.id)
        assert retrieved is not None
        assert retrieved.id == meta.id
        assert retrieved.description == "meta only"

    def test_tags(self, storage):
        """Should store and retrieve tags."""
        meta = storage.save_file(
            b"tagged", "tagged.pdf",
            tags=["edr", "response", "guide"],
        )
        assert meta.tags == ["edr", "response", "guide"]

        retrieved = storage.get_metadata(meta.id)
        assert retrieved is not None
        assert retrieved.tags == ["edr", "response", "guide"]

    def test_file_size_tracking(self, storage):
        """Should accurately track file size."""
        content = b"x" * 1024
        meta = storage.save_file(content, "sized.pdf")
        assert meta.file_size == 1024
