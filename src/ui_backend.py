"""FastAPI backend for the user review UI.

This module provides the web API endpoints for the file review interface,
allowing users to review ambiguous files and make include/exclude decisions.
"""

import logging
from typing import List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config_manager import ConfigurationManager, FileAction
from src.review_queue import ReviewItem, ReviewQueue

logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class ReviewItemResponse(BaseModel):
    """Response model for review items."""

    id: str
    file_path: str
    project_path: str
    reason: str
    created_at: str
    file_size: Optional[int] = None
    file_preview: Optional[str] = None


class UserDecisionRequest(BaseModel):
    """Request model for user decisions."""

    item_id: str
    decision: (
        str  # 'include_global', 'include_project', 'ignore_global', 'ignore_project'
    )
    scope: str = "project"  # 'global' or 'project'


class UIBackend:
    """FastAPI backend for the user review interface."""

    def __init__(self, review_queue: ReviewQueue, config_manager: ConfigurationManager):
        self.review_queue = review_queue
        self.config_manager = config_manager
        self.app = FastAPI(
            title="Auto-commit Review UI",
            description="Web interface for reviewing ambiguous files",
            version="1.0.0",
        )

        # Configure CORS for local development
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.app.get("/")
        async def root():
            """Root endpoint returning basic info."""
            return {"message": "Auto-commit Review UI Backend", "version": "1.0.0"}

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "auto-commit-ui"}

        @self.app.get("/api/review-queue", response_model=List[ReviewItemResponse])
        async def get_review_queue():
            """Get all pending review items."""
            try:
                items = self.review_queue.get_pending_items()
                response_items = []

                for item in items:
                    # Try to get file preview
                    file_preview = self._get_file_preview(item.file_path)
                    file_size = self._get_file_size(item.file_path)

                    response_items.append(
                        ReviewItemResponse(
                            id=item.id,
                            file_path=item.file_path,
                            project_path=item.project_path,
                            reason=item.reason,
                            created_at=item.created_at.isoformat(),
                            file_size=file_size,
                            file_preview=file_preview,
                        )
                    )

                return response_items

            except Exception as e:
                logger.error(f"Error getting review queue: {e}")
                raise HTTPException(
                    status_code=500, detail="Failed to get review queue"
                )

        @self.app.post("/api/user-decision")
        async def submit_user_decision(
            decision: UserDecisionRequest, background_tasks: BackgroundTasks
        ):
            """Submit a user decision for a review item."""
            try:
                # Get the review item
                item = self.review_queue.get_item(decision.item_id)
                if not item:
                    raise HTTPException(status_code=404, detail="Review item not found")

                # Process the decision
                success = await self._process_user_decision(item, decision)

                if success:
                    # Remove item from queue in background
                    background_tasks.add_task(
                        self.review_queue.remove_item, decision.item_id
                    )
                    return {"status": "success", "message": "Decision processed"}
                else:
                    raise HTTPException(
                        status_code=500, detail="Failed to process decision"
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing user decision: {e}")
                raise HTTPException(
                    status_code=500, detail="Failed to process decision"
                )

        @self.app.delete("/api/review-queue/{item_id}")
        async def remove_review_item(item_id: str):
            """Remove a review item without making a decision."""
            try:
                success = self.review_queue.remove_item(item_id)
                if success:
                    return {"status": "success", "message": "Item removed"}
                else:
                    raise HTTPException(status_code=404, detail="Review item not found")

            except Exception as e:
                logger.error(f"Error removing review item: {e}")
                raise HTTPException(status_code=500, detail="Failed to remove item")

        @self.app.get("/api/stats")
        async def get_stats():
            """Get statistics about the review queue."""
            try:
                items = self.review_queue.get_pending_items()
                return {
                    "pending_items": len(items),
                    "oldest_item": (
                        min(items, key=lambda x: x.created_at).created_at.isoformat()
                        if items
                        else None
                    ),
                    "newest_item": (
                        max(items, key=lambda x: x.created_at).created_at.isoformat()
                        if items
                        else None
                    ),
                }
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                raise HTTPException(status_code=500, detail="Failed to get stats")

    async def _process_user_decision(
        self, item: ReviewItem, decision: UserDecisionRequest
    ) -> bool:
        """Process a user decision and update configuration."""
        try:
            # Map decision to FileAction and scope
            action_map = {
                "include_global": (FileAction.INCLUDE, "global"),
                "include_project": (FileAction.INCLUDE, "project"),
                "ignore_global": (FileAction.IGNORE, "global"),
                "ignore_project": (FileAction.IGNORE, "project"),
            }

            if decision.decision not in action_map:
                logger.error(f"Unknown decision: {decision.decision}")
                return False

            action, scope = action_map[decision.decision]

            # Update configuration
            success = self.config_manager.add_pattern(
                pattern=item.file_path,
                action=action,
                scope=scope,
                project_path=item.project_path,
            )

            if success:
                logger.info(
                    f"Added pattern {item.file_path} with action {action} in {scope} scope"
                )
                return True
            else:
                logger.error(f"Failed to add pattern {item.file_path}")
                return False

        except Exception as e:
            logger.error(f"Error processing decision: {e}")
            return False

    def _get_file_preview(self, file_path: str, max_lines: int = 20) -> Optional[str]:
        """Get a preview of the file content."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"... ({i} more lines)")
                        break
                    lines.append(line.rstrip())
                return "\n".join(lines)
        except Exception as e:
            logger.debug(f"Could not get preview for {file_path}: {e}")
            return None

    def _get_file_size(self, file_path: str) -> Optional[int]:
        """Get the file size in bytes."""
        try:
            import os

            return os.path.getsize(file_path)
        except Exception as e:
            logger.debug(f"Could not get size for {file_path}: {e}")
            return None

    def run(self, host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
        """Run the FastAPI server."""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="debug" if debug else "info",
            reload=debug,
        )


def create_ui_backend(
    review_queue: ReviewQueue, config_manager: ConfigurationManager
) -> UIBackend:
    """Factory function to create a UI backend instance."""
    return UIBackend(review_queue, config_manager)
