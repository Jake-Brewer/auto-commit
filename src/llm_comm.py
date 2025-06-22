"""
LLM Communication module for generating commit messages.

This module handles communication with a Large Language Model
to generate meaningful commit messages from git diffs.
"""

import json
import logging
from typing import List, Optional

import requests

from src.linear_fallback import (LinearFallbackConfig, LinearFallbackError,
                                 LinearFallbackManager)


class LLMCommitGenerator:
    """
    Generates commit messages using a local Docker LLM container.

    This class interfaces with a locally running 'sequentialthought'
    Docker container to generate commit messages from git diffs.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "sequentialthought",
        enable_linear_fallback: bool = True,
        fallback_team_id: str = "b5f1d099-acc2-4e51-a415-76c00c00f23b",
    ):
        """
        Initialize the LLM commit generator.

        Args:
            base_url: Base URL of the local LLM service
            model_name: Name of the model to use
            enable_linear_fallback: Whether to use Linear fallback
            fallback_team_id: Linear team ID for fallback issues
        """
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.logger = logging.getLogger("LLMCommitGenerator")

        # Setup Linear fallback if enabled
        self.linear_fallback = None
        if enable_linear_fallback:
            fallback_config = LinearFallbackConfig(fallback_team_id=fallback_team_id)
            self.linear_fallback = LinearFallbackManager(fallback_config)

        # Test connection on initialization
        self._test_connection()

    def _test_connection(self) -> bool:
        """Test if the LLM service is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("Successfully connected to LLM service")
                return True
            else:
                self.logger.warning(
                    f"LLM service returned status {response.status_code}"
                )
                return False
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Cannot connect to LLM service: {e}")
            return False

    def _format_prompt(self, diff: str) -> str:
        """
        Format the git diff into a prompt for the LLM.

        Args:
            diff: The git diff to analyze

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a helpful assistant that generates concise, descriptive git commit messages.

Based on the following git diff, generate a single line commit message following conventional commit format:
- Use format: type(scope): description
- Types: feat, fix, docs, style, refactor, test, chore
- Keep description under 72 characters
- Be specific about what changed

Git diff:
```
{diff}
```

Commit message:"""

        return prompt

    def _call_llm(self, prompt: str) -> Optional[str]:
        """
        Call the local LLM service with the given prompt.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            LLM response or None if failed
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 100,
                    "stop": ["\n", "```"],
                },
            }

            response = requests.post(
                f"{self.base_url}/api/generate", json=payload, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                self.logger.error(f"LLM API error: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling LLM: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing LLM response: {e}")
            return None

    def generate_commit_message(
        self, diff: str, file_paths: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Generate a commit message from a git diff using the LLM.

        Args:
            diff: The git diff to analyze
            file_paths: Optional list of changed file paths

        Returns:
            Generated commit message or None if failed
        """
        if not diff or diff.strip() == "":
            self.logger.warning("Empty diff provided")
            return "chore: update files"

        # Format the prompt
        prompt = self._format_prompt(diff)

        # Call the LLM
        response = self._call_llm(prompt)

        if response:
            # Clean up the response
            commit_msg = response.strip()

            # Validate the response looks like a commit message
            if len(commit_msg) > 0 and len(commit_msg) <= 100:
                self.logger.info(f"Generated commit message: {commit_msg}")
                return commit_msg
            else:
                self.logger.warning(f"Invalid LLM response: {commit_msg}")

        # Try Linear fallback if enabled and LLM failed
        if self.linear_fallback and file_paths:
            try:
                self.logger.info("LLM unavailable, using Linear fallback")
                issue_id = self.linear_fallback.create_commit_message_request(
                    diff, file_paths
                )

                # Poll for response (this will block)
                commit_msg = self.linear_fallback.poll_for_commit_message(issue_id)
                if commit_msg:
                    self.logger.info(
                        f"Received commit message via Linear: {commit_msg}"
                    )
                    return commit_msg

            except LinearFallbackError as e:
                self.logger.error(f"Linear fallback failed: {e}")

        # Final fallback to simple heuristic
        return self._fallback_commit_message(diff)

    def _fallback_commit_message(self, diff: str) -> str:
        """
        Generate a fallback commit message using simple heuristics.

        Args:
            diff: The git diff to analyze

        Returns:
            Simple commit message
        """
        self.logger.info("Using fallback commit message generation")

        lines = diff.split("\n")
        added_lines = len([line for line in lines if line.startswith("+")])
        removed_lines = len([line for line in lines if line.startswith("-")])

        if added_lines > removed_lines:
            return "feat: add new functionality"
        elif removed_lines > added_lines:
            return "refactor: remove code"
        else:
            return "chore: update implementation"


# Global instance for backward compatibility
_llm_generator = LLMCommitGenerator()


def generate_commit_message(diff: str) -> Optional[str]:
    """
    Generate a commit message from a git diff using an LLM.

    Args:
        diff: The git diff to analyze

    Returns:
        Generated commit message
    """
    return _llm_generator.generate_commit_message(diff)
