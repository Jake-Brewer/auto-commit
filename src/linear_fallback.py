"""Linear fallback module for LLM commit message generation.

This module provides fallback functionality when the local LLM is unavailable.
It creates Linear issues with diff information and polls for human responses.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class LinearFallbackConfig:
    """Configuration for Linear fallback functionality."""

    fallback_team_id: str
    fallback_project_id: Optional[str] = None
    poll_interval_seconds: int = 30
    max_poll_duration_minutes: int = 60
    issue_title_prefix: str = "Auto-commit: Commit message needed"


class LinearFallbackError(Exception):
    """Raised when Linear fallback operations fail."""

    pass


class LinearFallbackManager:
    """Manages Linear fallback for LLM commit message generation."""

    def __init__(self, config: LinearFallbackConfig):
        self.config = config
        # issue_id -> expected_format
        self._pending_issues: Dict[str, str] = {}

    def create_commit_message_request(self, diff_content: str, file_paths: list) -> str:
        """Create a Linear issue requesting a commit message for the diff.

        Args:
            diff_content: The git diff content
            file_paths: List of file paths that changed

        Returns:
            The created Linear issue ID

        Raises:
            LinearFallbackError: If issue creation fails
        """
        try:
            # Format the issue description with diff and instructions
            description = self._format_issue_description(diff_content, file_paths)

            # Create the Linear issue
            from src.linear_integration import create_linear_issue

            issue_data = {
                "title": f"{self.config.issue_title_prefix} - {', '.join(file_paths[:3])}{'...' if len(file_paths) > 3 else ''}",
                "description": description,
                "teamId": self.config.fallback_team_id,
                "priority": 2,  # High priority
            }

            if self.config.fallback_project_id:
                issue_data["projectId"] = self.config.fallback_project_id

            issue_id = create_linear_issue(issue_data)

            # Track this issue for polling
            self._pending_issues[issue_id] = "commit_message"

            logger.info(
                f"Created Linear fallback issue {issue_id} for commit message request"
            )
            return issue_id

        except Exception as e:
            raise LinearFallbackError(f"Failed to create Linear fallback issue: {e}")

    def poll_for_commit_message(self, issue_id: str) -> Optional[str]:
        """Poll a Linear issue for a commit message response.

        Args:
            issue_id: The Linear issue ID to poll

        Returns:
            The commit message if found, None if still pending

        Raises:
            LinearFallbackError: If polling fails or times out
        """
        start_time = datetime.now()
        max_duration = timedelta(minutes=self.config.max_poll_duration_minutes)

        while datetime.now() - start_time < max_duration:
            try:
                # Check issue comments for commit message
                commit_message = self._check_issue_for_response(issue_id)
                if commit_message:
                    # Clean up tracking
                    self._pending_issues.pop(issue_id, None)
                    logger.info(f"Received commit message from Linear issue {issue_id}")
                    return commit_message

                # Wait before next poll
                time.sleep(self.config.poll_interval_seconds)

            except Exception as e:
                logger.error(f"Error polling Linear issue {issue_id}: {e}")
                time.sleep(self.config.poll_interval_seconds)

        # Timeout reached
        self._pending_issues.pop(issue_id, None)
        raise LinearFallbackError(
            f"Timeout waiting for response on Linear issue {issue_id}"
        )

    def _format_issue_description(self, diff_content: str, file_paths: list) -> str:
        """Format the Linear issue description with diff and instructions."""
        description = f"""**Auto-commit needs a commit message**

The local LLM is unavailable, so human assistance is needed to generate a commit message.

**Files changed:**
{chr(10).join(f'- {path}' for path in file_paths)}

**Diff:**
```diff
{diff_content}
```

**Instructions:**
Please reply to this issue with a conventional commit message that describes these changes.

**Expected format:**
```
type(scope): description

Optional longer description if needed
```

**Example:**
```
feat(auth): add user authentication middleware

Implements JWT-based authentication with role checking
```

Once you provide the commit message, the auto-commit system will use it and close this issue.
"""
        return description

    def _check_issue_for_response(self, issue_id: str) -> Optional[str]:
        """Check a Linear issue for commit message responses in comments."""
        try:
            from src.linear_integration import get_issue_comments

            comments = get_issue_comments(issue_id)

            # Look for commit message in comments (reverse order to get latest first)
            for comment in reversed(comments):
                content = comment.get("body", "").strip()

                # Skip empty comments or system comments
                if not content or content.startswith("**Auto-commit"):
                    continue

                # Look for code blocks that might contain commit messages
                if "```" in content:
                    lines = content.split("\n")
                    in_code_block = False
                    commit_lines = []

                    for line in lines:
                        if line.strip().startswith("```"):
                            if in_code_block:
                                # End of code block
                                if commit_lines:
                                    commit_message = "\n".join(commit_lines).strip()
                                    if self._is_valid_commit_message(commit_message):
                                        return commit_message
                                commit_lines = []
                                in_code_block = False
                            else:
                                # Start of code block
                                in_code_block = True
                        elif in_code_block:
                            commit_lines.append(line)

                # Also check if the entire comment looks like a commit message
                if self._is_valid_commit_message(content):
                    return content

            return None

        except Exception as e:
            logger.error(f"Error checking Linear issue {issue_id} for responses: {e}")
            return None

    def _is_valid_commit_message(self, message: str) -> bool:
        """Check if a message looks like a valid commit message."""
        if not message or len(message.strip()) < 10:
            return False

        # Basic validation: should have a reasonable first line
        first_line = message.split("\n")[0].strip()

        # Should be reasonable length
        if len(first_line) < 10 or len(first_line) > 100:
            return False

        # Should contain a colon (conventional commits format)
        if ":" not in first_line:
            return False

        # Should not be a question or instruction
        if first_line.endswith("?") or first_line.lower().startswith(
            ("please", "can you", "how")
        ):
            return False

        return True

    def cleanup_pending_issues(self):
        """Clean up any pending issues that are no longer needed."""
        for issue_id in list(self._pending_issues.keys()):
            try:
                # Could implement logic to close or update old issues
                logger.debug(f"Cleaning up pending issue {issue_id}")
            except Exception as e:
                logger.error(f"Error cleaning up issue {issue_id}: {e}")

        self._pending_issues.clear()
