"""
Unit tests for the review_queue module.
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from review_queue import ReviewQueue, ReviewItem


class TestReviewItem:
    """Test cases for ReviewItem dataclass."""
    
    def test_review_item_creation(self):
        """Test ReviewItem creation with all fields."""
        item = ReviewItem(
            id=1,
            file_path="/test/file.py",
            reason="Test reason",
            created_at=datetime.now(),
            status="pending",
            decision=None,
            metadata={"test": "data"}
        )
        
        assert item.id == 1
        assert item.file_path == "/test/file.py"
        assert item.reason == "Test reason"
        assert item.status == "pending"
        assert item.decision is None
        assert item.metadata == {"test": "data"}
    
    def test_review_item_defaults(self):
        """Test ReviewItem with default values."""
        item = ReviewItem(
            file_path="/test/file.py",
            reason="Test reason"
        )
        
        assert item.id is None
        assert item.status == "pending"
        assert item.decision is None
        assert item.metadata == {}
        assert isinstance(item.created_at, datetime)


class TestReviewQueue:
    """Test cases for ReviewQueue class."""
    
    def test_init_creates_database(self, temp_dir):
        """Test ReviewQueue initialization creates database."""
        db_path = temp_dir / "test_review.db"
        queue = ReviewQueue(str(db_path))
        
        assert db_path.exists()
        
        # Verify table structure
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        assert ("review_items",) in tables
    
    def test_add_file_basic(self, review_queue):
        """Test adding a file to the review queue."""
        file_path = "/test/file.py"
        reason = "Test review"
        
        item_id = review_queue.add_file(file_path, reason)
        
        assert item_id is not None
        assert isinstance(item_id, int)
        
        # Verify item was added
        items = review_queue.get_pending_items()
        assert len(items) == 1
        assert items[0].file_path == file_path
        assert items[0].reason == reason
    
    def test_add_file_with_metadata(self, review_queue):
        """Test adding a file with metadata."""
        file_path = "/test/file.py"
        reason = "Test review"
        metadata = {"patterns": ["*.py"], "conflict": True}
        
        item_id = review_queue.add_file(file_path, reason, metadata)
        
        items = review_queue.get_pending_items()
        assert len(items) == 1
        assert items[0].metadata == metadata
    
    def test_add_duplicate_file(self, review_queue):
        """Test adding duplicate file path."""
        file_path = "/test/file.py"
        reason = "Test review"
        
        # Add first time
        item_id1 = review_queue.add_file(file_path, reason)
        
        # Add duplicate
        item_id2 = review_queue.add_file(file_path, reason)
        
        # Should still create new entry (different reasons/times)
        assert item_id1 != item_id2
        
        items = review_queue.get_pending_items()
        assert len(items) == 2
    
    def test_get_pending_items_empty(self, review_queue):
        """Test getting pending items from empty queue."""
        items = review_queue.get_pending_items()
        assert items == []
    
    def test_get_pending_items_multiple(self, review_queue):
        """Test getting multiple pending items."""
        files = ["/test/file1.py", "/test/file2.py", "/test/file3.py"]
        
        for file_path in files:
            review_queue.add_file(file_path, f"Review {file_path}")
        
        items = review_queue.get_pending_items()
        assert len(items) == 3
        
        # Should be ordered by creation time (newest first)
        file_paths = [item.file_path for item in items]
        assert all(fp in file_paths for fp in files)
    
    def test_mark_resolved_include(self, review_queue):
        """Test marking item as resolved with include decision."""
        file_path = "/test/file.py"
        item_id = review_queue.add_file(file_path, "Test review")
        
        success = review_queue.mark_resolved(item_id, "include", "*.py")
        assert success
        
        # Should no longer be in pending items
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) == 0
        
        # Verify resolution was recorded
        resolved_items = review_queue.get_resolved_items()
        assert len(resolved_items) == 1
        assert resolved_items[0].decision == "include"
        assert resolved_items[0].status == "resolved"
    
    def test_mark_resolved_ignore(self, review_queue):
        """Test marking item as resolved with ignore decision."""
        file_path = "/test/file.py"
        item_id = review_queue.add_file(file_path, "Test review")
        
        success = review_queue.mark_resolved(item_id, "ignore", "*.py")
        assert success
        
        resolved_items = review_queue.get_resolved_items()
        assert len(resolved_items) == 1
        assert resolved_items[0].decision == "ignore"
    
    def test_mark_resolved_invalid_id(self, review_queue):
        """Test marking non-existent item as resolved."""
        success = review_queue.mark_resolved(999, "include", "*.py")
        assert not success
    
    def test_mark_resolved_invalid_decision(self, review_queue):
        """Test marking item with invalid decision."""
        file_path = "/test/file.py"
        item_id = review_queue.add_file(file_path, "Test review")
        
        success = review_queue.mark_resolved(item_id, "invalid", "*.py")
        assert not success
    
    def test_get_resolved_items_empty(self, review_queue):
        """Test getting resolved items from empty queue."""
        items = review_queue.get_resolved_items()
        assert items == []
    
    def test_get_resolved_items_multiple(self, review_queue):
        """Test getting multiple resolved items."""
        files = ["/test/file1.py", "/test/file2.py"]
        
        for i, file_path in enumerate(files):
            item_id = review_queue.add_file(file_path, f"Review {i}")
            decision = "include" if i % 2 == 0 else "ignore"
            review_queue.mark_resolved(item_id, decision, "*.py")
        
        resolved_items = review_queue.get_resolved_items()
        assert len(resolved_items) == 2
        
        # Check decisions
        decisions = [item.decision for item in resolved_items]
        assert "include" in decisions
        assert "ignore" in decisions
    
    def test_get_item_by_id(self, review_queue):
        """Test getting specific item by ID."""
        file_path = "/test/file.py"
        reason = "Test review"
        metadata = {"test": True}
        
        item_id = review_queue.add_file(file_path, reason, metadata)
        
        item = review_queue.get_item_by_id(item_id)
        
        assert item is not None
        assert item.id == item_id
        assert item.file_path == file_path
        assert item.reason == reason
        assert item.metadata == metadata
    
    def test_get_item_by_id_not_found(self, review_queue):
        """Test getting non-existent item by ID."""
        item = review_queue.get_item_by_id(999)
        assert item is None
    
    def test_delete_item(self, review_queue):
        """Test deleting an item from the queue."""
        file_path = "/test/file.py"
        item_id = review_queue.add_file(file_path, "Test review")
        
        success = review_queue.delete_item(item_id)
        assert success
        
        # Item should no longer exist
        item = review_queue.get_item_by_id(item_id)
        assert item is None
        
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) == 0
    
    def test_delete_item_not_found(self, review_queue):
        """Test deleting non-existent item."""
        success = review_queue.delete_item(999)
        assert not success
    
    def test_clear_resolved_items(self, review_queue):
        """Test clearing resolved items."""
        # Add and resolve some items
        for i in range(3):
            item_id = review_queue.add_file(f"/test/file{i}.py", f"Review {i}")
            review_queue.mark_resolved(item_id, "include", "*.py")
        
        # Add one pending item
        review_queue.add_file("/test/pending.py", "Pending review")
        
        # Clear resolved items
        count = review_queue.clear_resolved_items()
        assert count == 3
        
        # Resolved items should be gone
        resolved_items = review_queue.get_resolved_items()
        assert len(resolved_items) == 0
        
        # Pending items should remain
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) == 1
    
    def test_get_stats(self, review_queue):
        """Test getting queue statistics."""
        # Add various items
        for i in range(3):
            review_queue.add_file(f"/test/pending{i}.py", f"Pending {i}")
        
        for i in range(2):
            item_id = review_queue.add_file(f"/test/resolved{i}.py", f"Resolved {i}")
            review_queue.mark_resolved(item_id, "include", "*.py")
        
        stats = review_queue.get_stats()
        
        assert stats["total_items"] == 5
        assert stats["pending_items"] == 3
        assert stats["resolved_items"] == 2
        assert "oldest_pending" in stats
        assert "newest_pending" in stats
    
    def test_get_stats_empty(self, review_queue):
        """Test getting statistics from empty queue."""
        stats = review_queue.get_stats()
        
        assert stats["total_items"] == 0
        assert stats["pending_items"] == 0
        assert stats["resolved_items"] == 0
        assert stats["oldest_pending"] is None
        assert stats["newest_pending"] is None
    
    def test_database_error_handling(self, temp_dir):
        """Test handling of database errors."""
        # Create invalid database path
        invalid_path = temp_dir / "readonly" / "review.db"
        
        # Should handle initialization error gracefully
        queue = ReviewQueue(str(invalid_path))
        
        # Operations should not crash
        item_id = queue.add_file("/test/file.py", "Test")
        assert item_id is None  # Should return None on error
        
        items = queue.get_pending_items()
        assert items == []  # Should return empty list on error
    
    def test_concurrent_access(self, review_queue):
        """Test concurrent access to the database."""
        import threading
        
        results = []
        
        def add_files(start_idx, count):
            for i in range(start_idx, start_idx + count):
                item_id = review_queue.add_file(f"/test/file{i}.py", f"Test {i}")
                results.append(item_id)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_files, args=(i * 10, 5))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all items were added
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) == 15
        
        # All results should be valid IDs
        assert all(r is not None for r in results)
        assert len(set(results)) == len(results)  # All unique 