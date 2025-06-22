"""
Review Queue module for managing files that need human review.

This module implements a SQLite-based persistent queue for files that are
flagged as ambiguous and require human review before commit decisions.
"""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ReviewItem:
    """Represents a file that needs review."""

    id: Optional[int]
    file_path: str
    event_type: str
    timestamp: datetime
    reason: str
    status: str = "pending"  # pending, approved, rejected
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewItem":
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class ReviewQueue:
    """
    SQLite-based persistent queue for files requiring human review.

    This queue stores files that have ambiguous include/ignore rules
    and need human decision before proceeding with commit operations.
    """

    def __init__(self, db_path: str = "review_queue.db"):
        """
        Initialize the ReviewQueue.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger("ReviewQueue")
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database and create tables if needed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS review_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create index for faster queries
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_status 
                    ON review_items(status)
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_file_path 
                    ON review_items(file_path)
                """
                )

                conn.commit()
                self.logger.debug(f"Database initialized at {self.db_path}")

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def add_item(
        self,
        file_path: str,
        event_type: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add a file to the review queue.

        Args:
            file_path: Path to the file needing review
            event_type: Type of file system event (created, modified, etc.)
            reason: Reason why the file needs review
            metadata: Optional additional metadata

        Returns:
            ID of the created review item
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO review_items 
                    (file_path, event_type, timestamp, reason, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        file_path,
                        event_type,
                        datetime.now().isoformat(),
                        reason,
                        json.dumps(metadata) if metadata else None,
                    ),
                )

                item_id = cursor.lastrowid
                conn.commit()

                self.logger.info(f"Added review item {item_id}: {file_path}")
                return item_id

        except Exception as e:
            self.logger.error(f"Failed to add review item: {e}")
            raise

    def get_pending_items(self, limit: Optional[int] = None) -> List[ReviewItem]:
        """
        Get all pending review items.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of pending ReviewItem objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT id, file_path, event_type, timestamp, reason, 
                           status, metadata
                    FROM review_items 
                    WHERE status = 'pending'
                    ORDER BY timestamp ASC
                """

                if limit:
                    query += f" LIMIT {limit}"

                cursor = conn.execute(query)
                items = []

                for row in cursor.fetchall():
                    metadata = json.loads(row[6]) if row[6] else None
                    item = ReviewItem(
                        id=row[0],
                        file_path=row[1],
                        event_type=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        reason=row[4],
                        status=row[5],
                        metadata=metadata,
                    )
                    items.append(item)

                self.logger.debug(f"Retrieved {len(items)} pending items")
                return items

        except Exception as e:
            self.logger.error(f"Failed to get pending items: {e}")
            return []

    def update_item_status(self, item_id: int, status: str) -> bool:
        """
        Update the status of a review item.

        Args:
            item_id: ID of the review item
            status: New status (pending, approved, rejected)

        Returns:
            True if update was successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    UPDATE review_items 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (status, item_id),
                )

                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"Updated item {item_id} status to {status}")
                    return True
                else:
                    self.logger.warning(f"No item found with ID {item_id}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to update item status: {e}")
            return False

    def get_item(self, item_id: int) -> Optional[ReviewItem]:
        """
        Get a specific review item by ID.

        Args:
            item_id: ID of the review item

        Returns:
            ReviewItem object or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, file_path, event_type, timestamp, reason, 
                           status, metadata
                    FROM review_items 
                    WHERE id = ?
                """,
                    (item_id,),
                )

                row = cursor.fetchone()
                if row:
                    metadata = json.loads(row[6]) if row[6] else None
                    return ReviewItem(
                        id=row[0],
                        file_path=row[1],
                        event_type=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        reason=row[4],
                        status=row[5],
                        metadata=metadata,
                    )

                return None

        except Exception as e:
            self.logger.error(f"Failed to get item {item_id}: {e}")
            return None

    def remove_item(self, item_id: int) -> bool:
        """
        Remove a review item from the queue.

        Args:
            item_id: ID of the review item to remove

        Returns:
            True if removal was successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM review_items WHERE id = ?
                """,
                    (item_id,),
                )

                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"Removed item {item_id}")
                    return True
                else:
                    self.logger.warning(f"No item found with ID {item_id}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to remove item {item_id}: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the review queue.

        Returns:
            Dictionary with queue statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT status, COUNT(*) 
                    FROM review_items 
                    GROUP BY status
                """
                )

                stats = {"total": 0}
                for status, count in cursor.fetchall():
                    stats[status] = count
                    stats["total"] += count

                self.logger.debug(f"Queue stats: {stats}")
                return stats

        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {"total": 0}

    def clear_completed(self) -> int:
        """
        Remove all approved and rejected items from the queue.

        Returns:
            Number of items removed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM review_items 
                    WHERE status IN ('approved', 'rejected')
                """
                )

                removed_count = cursor.rowcount
                conn.commit()

                self.logger.info(f"Cleared {removed_count} completed items")
                return removed_count

        except Exception as e:
            self.logger.error(f"Failed to clear completed items: {e}")
            return 0
