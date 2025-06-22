"""
Unit tests for the review_queue module.
"""

import sqlite3
import sys
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from review_queue import ReviewItem, ReviewQueue


class TestReviewItem:
    """Test cases for ReviewItem dataclass."""

    def test_review_item_creation(self):
        """Test ReviewItem creation with all fields."""
        now = datetime.now()
        item = ReviewItem(
            id=1,
            file_path="/test/file.py",
            reason="Test reason",
            created_at=now,
            status="pending",
            decision=None,
            metadata={"test": "data"},
        )

        assert item.id == 1
        assert item.file_path == "/test/file.py"
        assert item.reason == "Test reason"
        assert item.status == "pending"
        assert item.decision is None
        assert item.metadata == {"test": "data"}
        assert item.created_at == now

    def test_review_item_defaults(self):
        """Test ReviewItem with default values."""
        item = ReviewItem(id=1, file_path="/test/file.py", reason="Test reason")

        assert item.id == 1
        assert item.status == "pending"
        assert item.decision is None
        assert item.metadata is None
        assert isinstance(item.created_at, datetime)


class TestReviewQueue:
    """Test cases for ReviewQueue class."""

    def test_init_creates_database(self, temp_dir):
        """Test ReviewQueue initialization creates database."""
        db_path = temp_dir / "test_review.db"
        queue = ReviewQueue(str(db_path))

        assert db_path.exists()

        # Verify table structure
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

        assert ("review_items",) in tables

    def test_add_item_basic(self, review_queue):
        """Test adding a file to the review queue."""
        file_path = "/test/file.py"
        reason = "Test review"

        item_id = review_queue.add_item(file_path, reason)

        assert item_id is not None
        assert isinstance(item_id, int)

        # Verify item was added
        items = review_queue.get_pending_items()
        assert len(items) == 1
        assert items[0].file_path == file_path
        assert items[0].reason == reason

    def test_add_item_with_metadata(self, review_queue):
        """Test adding a file with metadata."""
        file_path = "/test/file.py"
        reason = "Test review"
        metadata = {"patterns": ["*.py"], "conflict": True}

        item_id = review_queue.add_item(file_path, reason, metadata)
        assert item_id is not None

        items = review_queue.get_pending_items()
        assert len(items) == 1
        assert items[0].metadata == metadata

    def test_add_duplicate_file(self, review_queue):
        """Test adding duplicate file path returns existing ID."""
        file_path = "/test/file.py"
        reason = "Test review"

        item_id1 = review_queue.add_item(file_path, reason)
        item_id2 = review_queue.add_item(file_path, reason)

        assert item_id1 is not None
        assert item_id1 == item_id2

        items = review_queue.get_pending_items()
        assert len(items) == 1

    def test_get_pending_items_empty(self, review_queue):
        """Test getting pending items from empty queue."""
        items = review_queue.get_pending_items()
        assert items == []

    def test_get_pending_items_multiple(self, review_queue):
        """Test getting multiple pending items."""
        files = ["/test/file1.py", "/test/file2.py", "/test/file3.py"]

        for file_path in files:
            review_queue.add_item(file_path, f"Review {file_path}")

        items = review_queue.get_pending_items()
        assert len(items) == 3
        file_paths = [item.file_path for item in items]
        assert all(fp in file_paths for fp in files)

    def test_resolve_item_include(self, review_queue):
        """Test marking item as resolved with include decision."""
        file_path = "/test/file.py"
        item_id = review_queue.add_item(file_path, "Test review")
        assert item_id is not None

        success = review_queue.resolve_item(item_id, "include", "*.py")
        assert success

        pending_items = review_queue.get_pending_items()
        assert len(pending_items) == 0

        resolved_items = review_queue.get_resolved_items()
        assert len(resolved_items) == 1
        assert resolved_items[0].decision == "include"
        assert resolved_items[0].status == "resolved"

    def test_resolve_item_ignore(self, review_queue):
        """Test marking item as resolved with ignore decision."""
        file_path = "/test/file.py"
        item_id = review_queue.add_item(file_path, "Test review")
        assert item_id is not None

        success = review_queue.resolve_item(item_id, "ignore")
        assert success

        resolved_items = review_queue.get_resolved_items()
        assert len(resolved_items) == 1
        assert resolved_items[0].decision == "ignore"

    def test_resolve_item_invalid_id(self, review_queue):
        """Test marking non-existent item as resolved."""
        success = review_queue.resolve_item(999, "include", "*.py")
        assert not success

    def test_resolve_item_invalid_decision(self, review_queue):
        """Test marking item with invalid decision."""
        file_path = "/test/file.py"
        item_id = review_queue.add_item(file_path, "Test review")
        assert item_id is not None

        success = review_queue.resolve_item(item_id, "invalid", "*.py")
        assert not success

    def test_get_resolved_items_empty(self, review_queue):
        """Test getting resolved items from empty queue."""
        items = review_queue.get_resolved_items()
        assert items == []

    def test_get_resolved_items_multiple(self, review_queue):
        """Test getting multiple resolved items."""
        files = ["/test/file1.py", "/test/file2.py"]

        for i, file_path in enumerate(files):
            item_id = review_queue.add_item(file_path, f"Review {i}")
            assert item_id is not None
            decision = "include" if i % 2 == 0 else "ignore"
            review_queue.resolve_item(item_id, decision, "*.py")

        resolved_items = review_queue.get_resolved_items()
        assert len(resolved_items) == 2
        decisions = [item.decision for item in resolved_items]
        assert "include" in decisions
        assert "ignore" in decisions

    def test_get_item_by_id(self, review_queue):
        """Test getting specific item by ID."""
        file_path = "/test/file.py"
        reason = "Test review"
        metadata = {"test": True}

        item_id = review_queue.add_item(file_path, reason, metadata)
        assert item_id is not None

        item = review_queue.get_item(item_id)
        assert item is not None
        assert item.id == item_id
        assert item.file_path == file_path
        assert item.reason == reason
        assert item.metadata == metadata

    def test_get_item_by_id_not_found(self, review_queue):
        """Test getting non-existent item by ID."""
        item = review_queue.get_item(999)
        assert item is None

    def test_delete_item(self, review_queue):
        """Test deleting an item from the queue."""
        file_path = "/test/file.py"
        item_id = review_queue.add_item(file_path, "Test review")
        assert item_id is not None

        success = review_queue.remove_item(item_id)
        assert success

        item = review_queue.get_item(item_id)
        assert item is None
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) == 0

    def test_delete_item_not_found(self, review_queue):
        """Test deleting non-existent item."""
        success = review_queue.remove_item(999)
        assert not success

    def test_clear_resolved_items(self, review_queue):
        """Test clearing resolved items."""
        for i in range(3):
            item_id = review_queue.add_item(f"/test/file{i}.py", f"Review {i}")
            assert item_id is not None
            review_queue.resolve_item(item_id, "include", "*.py")

        review_queue.add_item("/test/pending.py", "Pending review")
        cleared_count = review_queue.clear_resolved_items()
        assert cleared_count == 3
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) == 1
        resolved_items = review_queue.get_resolved_items()
        assert len(resolved_items) == 0

    def test_get_stats(self, review_queue):
        """Test getting queue statistics."""
        for i in range(3):
            review_queue.add_item(f"/test/pending{i}.py", f"Pending {i}")

        item_id = review_queue.add_item("/test/resolved.py", "Resolved")
        assert item_id is not None
        review_queue.resolve_item(item_id, "include")

        stats = review_queue.get_stats()
        assert stats["total_items"] == 4
        assert stats["pending_items"] == 3
        assert stats["resolved_items"] == 1

    def test_get_stats_empty(self, review_queue):
        """Test getting statistics from empty queue."""
        stats = review_queue.get_stats()
        assert stats["total_items"] == 0
        assert stats["pending_items"] == 0
        assert stats["resolved_items"] == 0

    def test_database_error_handling(self, temp_dir):
        """Test handling of database errors."""
        invalid_path = temp_dir / "readonly"
        invalid_path.mkdir()
        db_path = invalid_path / "review.db"

        # Make the directory read-only to cause an error
        invalid_path.chmod(0o555)

        with pytest.raises(sqlite3.OperationalError):
            ReviewQueue(str(db_path))

        # Restore permissions for cleanup
        invalid_path.chmod(0o755)

    def test_concurrent_access(self, review_queue):
        """Test concurrent access to the database."""
        results = []

        def add_files(start_idx, count):
            for i in range(start_idx, start_idx + count):
                item_id = review_queue.add_item(f"/test/file{i}.py", f"Test {i}")
                if item_id:
                    results.append(item_id)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_files, args=(i * 10, 10))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 50
        stats = review_queue.get_stats()
        assert stats["total_items"] == 50
        assert stats["pending_items"] == 50
