"""
Review Queue module for managing files that need human review.

This module implements a SQLite-based persistent queue for files that are
flagged as ambiguous and require human review before commit decisions.
"""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ReviewItem:
    """Represents a file that needs review."""

    id: int
    file_path: str
    reason: str
    status: str = "pending"
    decision: Optional[str] = None
    add_to_include: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ReviewItem":
        """Create a ReviewItem from a database row."""
        data = dict(row)
        for key, value in data.items():
            if "at" in key and value and isinstance(value, str):
                try:
                    data[key] = datetime.fromisoformat(value)
                except ValueError:
                    # Handle cases where the timestamp might not be a full isoformat
                    data[key] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
        if "metadata" in data and isinstance(data["metadata"], str):
            data["metadata"] = json.loads(data["metadata"])
        return cls(**data)


class ReviewQueue:
    """A thread-safe queue for managing files that need manual review."""

    def __init__(self, db_path: str):
        """
        Initialize the ReviewQueue.

        Args:
            db_path: The path to the SQLite database file.
        """
        self.db_path = db_path
        self._lock = Lock()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-safe SQLite connection."""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_database(self) -> None:
        """Initialize the SQLite database and create tables if needed."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS review_items (
                        id INTEGER PRIMARY KEY,
                        file_path TEXT NOT NULL UNIQUE,
                        reason TEXT,
                        status TEXT NOT NULL,
                        decision TEXT,
                        add_to_include TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TIMESTAMP,
                        metadata TEXT
                    )
                    """
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def add_item(
        self, file_path: str, reason: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Add a file to the review queue.

        Args:
            file_path: The absolute path of the file to review.
            reason: The reason why the file needs review.
            metadata: Optional dictionary for additional data.

        Returns:
            The ID of the newly added item, or the existing item's ID if the
            file path is already in the queue. Returns None on failure.
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id FROM review_items WHERE file_path = ?", (file_path,)
                    )
                    if existing_item := cursor.fetchone():
                        logger.warning(
                            f"File {file_path} is already in the review queue with ID {existing_item[0]}."
                        )
                        return existing_item[0]

                    metadata_str = json.dumps(metadata) if metadata else None
                    cursor.execute(
                        """
                        INSERT INTO review_items (file_path, reason, status, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (file_path, reason, "pending", metadata_str, datetime.now()),
                    )
                    conn.commit()
                    item_id = cursor.lastrowid
                    logger.info(
                        f"Added file to review queue: {file_path} (ID: {item_id})"
                    )
                    return item_id
            except sqlite3.Error as e:
                logger.error(f"Failed to add file to review queue: {e}")
                return None

    def get_item(self, item_id: int) -> Optional[ReviewItem]:
        """
        Get a specific review item by its ID.
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM review_items WHERE id = ?", (item_id,))
                if row := cursor.fetchone():
                    return ReviewItem.from_row(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Failed to get review item {item_id}: {e}")
            return None

    def get_all_items(self, status: Optional[str] = None) -> List[ReviewItem]:
        """
        Get all items from the queue, optionally filtering by status.
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = "SELECT * FROM review_items"
                params = []
                if status:
                    query += " WHERE status = ?"
                    params.append(status)
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [ReviewItem.from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get review items: {e}")
            return []

    def get_pending_items(self) -> List[ReviewItem]:
        return self.get_all_items(status="pending")

    def get_resolved_items(self) -> List[ReviewItem]:
        return self.get_all_items(status="resolved")

    def resolve_item(
        self, item_id: int, decision: str, add_to_include: Optional[str] = None
    ) -> bool:
        """
        Mark an item as resolved with a specific decision.
        """
        if decision not in ["include", "ignore"]:
            logger.error(f"Invalid decision '{decision}' for item {item_id}.")
            return False

        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        UPDATE review_items
                        SET status = 'resolved', decision = ?, add_to_include = ?, resolved_at = ?
                        WHERE id = ?
                        """,
                        (decision, add_to_include, datetime.now(), item_id),
                    )
                    conn.commit()
                    success = cursor.rowcount > 0
                    if success:
                        logger.info(
                            f"Resolved item {item_id} with decision '{decision}'."
                        )
                    else:
                        logger.warning(f"Item {item_id} not found for resolution.")
                    return success
            except sqlite3.Error as e:
                logger.error(f"Failed to resolve item {item_id}: {e}")
                return False

    def remove_item(self, item_id: int) -> bool:
        """
        Delete an item from the queue.
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM review_items WHERE id = ?", (item_id,))
                    conn.commit()
                    success = cursor.rowcount > 0
                    if success:
                        logger.info(f"Deleted item {item_id} from review queue.")
                    else:
                        logger.warning(
                            f"Attempted to delete non-existent item {item_id}."
                        )
                    return success
            except sqlite3.Error as e:
                logger.error(f"Failed to delete item {item_id}: {e}")
                return False

    def clear_resolved_items(self) -> int:
        """
        Delete all resolved items from the queue.
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM review_items WHERE status = 'resolved'")
                    count = cursor.rowcount
                    conn.commit()
                    logger.info(f"Cleared {count} resolved items from review queue.")
                    return count
            except sqlite3.Error as e:
                logger.error(f"Failed to clear resolved items: {e}")
                return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the items in the queue.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM review_items")
                total_items = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM review_items WHERE status = 'pending'"
                )
                pending_items = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM review_items WHERE status = 'resolved'"
                )
                resolved_items = cursor.fetchone()[0]
                return {
                    "total_items": total_items,
                    "pending_items": pending_items,
                    "resolved_items": resolved_items,
                }
        except sqlite3.Error as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {
                "total_items": 0,
                "pending_items": 0,
                "resolved_items": 0,
                "error": str(e),
            }
