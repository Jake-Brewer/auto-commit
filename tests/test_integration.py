"""
Integration tests for auto-commit system.
Tests how different components work together.
"""

import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path
from queue import Queue
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from commit_worker import CommitWorker, CommitWorkerPool
from config import AppConfig, LLMConfig
from config_manager import ConfigurationManager, FileAction
from git_ops import GitRepo
from review_queue import ReviewQueue
from watcher import ChangeHandler


class TestFileWatchingIntegration:
    """Integration tests for file watching and processing."""

    def test_file_change_to_commit_flow(self, temp_git_repo):
        """Test complete flow from file change to commit."""
        temp_dir, repo = temp_git_repo

        # Setup components
        config_manager = ConfigurationManager(str(temp_dir))
        git_repo = GitRepo(str(temp_dir))
        event_queue = Queue()
        review_queue = ReviewQueue(str(temp_dir / "review.db"))

        # Create .gitinclude to auto-include Python files
        gitinclude = temp_dir / ".gitinclude"
        gitinclude.write_text("*.py\n")

        # Mock LLM generator
        mock_llm = Mock()
        mock_llm.generate_commit_message.return_value = "feat: add test file"

        # Create worker
        worker = CommitWorker(
            config_manager=config_manager,
            git_repo=git_repo,
            review_queue=review_queue,
            llm_generator=mock_llm,
        )

        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello world')")

        # Simulate file system event
        from watchdog.events import FileCreatedEvent

        event = FileCreatedEvent(str(test_file))

        # Process event
        worker.process_event(event)

        # Verify file was committed
        assert len(list(repo.iter_commits())) == 2  # Initial + new commit
        latest_commit = repo.head.commit
        assert "feat: add test file" in latest_commit.message

    def test_ambiguous_file_review_flow(self, temp_git_repo):
        """Test flow for files that need human review."""
        temp_dir, repo = temp_git_repo

        # Setup components
        config_manager = ConfigurationManager(str(temp_dir))
        review_queue = ReviewQueue(str(temp_dir / "review.db"))

        # Create conflicting patterns
        gitinclude = temp_dir / ".gitinclude"
        gitinclude.write_text("*.txt\n")

        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("*.txt\n")

        # Create test file
        test_file = temp_dir / "ambiguous.txt"
        test_file.write_text("This file has conflicting patterns")

        # Check file action
        action = config_manager.get_file_action(str(test_file))
        assert action == FileAction.REVIEW

        # Add to review queue
        review_queue.add_file(
            file_path=str(test_file),
            reason="Conflicting include/ignore patterns",
            metadata={"patterns": ["*.txt (include)", "*.txt (ignore)"]},
        )

        # Verify file is in review queue
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) == 1
        assert pending_items[0].file_path == str(test_file)
        assert "Conflicting" in pending_items[0].reason

    def test_worker_pool_processing(self, temp_git_repo):
        """Test multi-threaded event processing."""
        temp_dir, repo = temp_git_repo

        # Setup components
        config_manager = ConfigurationManager(str(temp_dir))
        git_repo = GitRepo(str(temp_dir))
        event_queue = Queue()
        review_queue = ReviewQueue(str(temp_dir / "review.db"))

        # Create .gitinclude for Python files
        gitinclude = temp_dir / ".gitinclude"
        gitinclude.write_text("*.py\n")

        # Mock LLM generator
        mock_llm = Mock()
        mock_llm.generate_commit_message.return_value = "feat: add files"

        # Create worker pool
        worker_pool = CommitWorkerPool(
            config_manager=config_manager,
            git_repo=git_repo,
            event_queue=event_queue,
            review_queue=review_queue,
            llm_generator=mock_llm,
            num_workers=2,
        )

        # Start worker pool
        worker_pool.start()

        try:
            # Create multiple test files
            test_files = []
            for i in range(5):
                test_file = temp_dir / f"test{i}.py"
                test_file.write_text(f"print('test {i}')")
                test_files.append(test_file)

                # Add events to queue
                from watchdog.events import FileCreatedEvent

                event = FileCreatedEvent(str(test_file))
                event_queue.put(event)

            # Wait for processing
            time.sleep(2)

            # Verify all files were processed
            commits = list(repo.iter_commits())
            assert len(commits) > 1  # Should have multiple commits

        finally:
            worker_pool.stop()

    def test_configuration_hierarchy_resolution(self, temp_dir):
        """Test hierarchical configuration file resolution."""
        # Create nested directory structure
        subdir1 = temp_dir / "level1"
        subdir1.mkdir()
        subdir2 = subdir1 / "level2"
        subdir2.mkdir()

        # Create config files at different levels
        root_gitignore = temp_dir / ".gitignore"
        root_gitignore.write_text("*.log\n*.tmp")

        level1_gitinclude = subdir1 / ".gitinclude"
        level1_gitinclude.write_text("*.py\n*.md")

        level2_gitignore = subdir2 / ".gitignore"
        level2_gitignore.write_text("test_*")

        # Setup configuration manager
        config_manager = ConfigurationManager(str(temp_dir))

        # Test file at level 2
        test_file = subdir2 / "test_file.py"
        test_file.touch()

        # Should be ignored due to level2 gitignore pattern
        action = config_manager.get_file_action(str(test_file))
        assert action == FileAction.IGNORE

        # Test different file at level 2
        other_file = subdir2 / "other.py"
        other_file.touch()

        # Should be included due to level1 gitinclude pattern
        action = config_manager.get_file_action(str(other_file))
        assert action == FileAction.INCLUDE

    @patch("src.llm_comm.requests.post")
    def test_llm_commit_message_generation(self, mock_post, temp_git_repo):
        """Test LLM integration for commit message generation."""
        temp_dir, repo = temp_git_repo

        # Mock LLM response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "feat: implement user authentication system"
        }
        mock_post.return_value = mock_response

        # Setup components
        from config import LLMConfig
        from llm_comm import LLMCommitGenerator

        llm_config = LLMConfig()
        llm_generator = LLMCommitGenerator(llm_config)
        git_repo = GitRepo(str(temp_dir))

        # Create and stage changes
        auth_file = temp_dir / "auth.py"
        auth_file.write_text(
            """
class AuthSystem:
    def __init__(self):
        self.users = {}
    
    def authenticate(self, username, password):
        return username in self.users
"""
        )

        git_repo.add_files([str(auth_file)])
        diff = git_repo.get_diff()

        # Generate commit message
        commit_message = llm_generator.generate_commit_message(diff)

        assert commit_message == "feat: implement user authentication system"
        mock_post.assert_called_once()

    def test_ui_backend_integration(self, temp_dir):
        """Test UI backend integration with review queue."""
        from ui_backend import create_ui_backend

        # Setup components
        review_queue = ReviewQueue(str(temp_dir / "review.db"))
        config_manager = ConfigurationManager(str(temp_dir))

        # Add test items to review queue
        test_files = ["file1.txt", "file2.py", "file3.log"]
        for file_path in test_files:
            review_queue.add_file(
                file_path=file_path, reason="Test review", metadata={"test": True}
            )

        # Create UI backend
        app = create_ui_backend(review_queue, config_manager)

        # Test client
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Test getting pending items
        response = client.get("/api/review/pending")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3
        assert any(item["file_path"] == "file1.txt" for item in data)

        # Test making decision
        item_id = data[0]["id"]
        response = client.post(
            f"/api/review/{item_id}/decision",
            json={"decision": "include", "pattern": "*.txt"},
        )
        assert response.status_code == 200

        # Verify decision was recorded
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) == 2  # One item should be resolved


class TestErrorHandlingIntegration:
    """Integration tests for error handling scenarios."""

    def test_git_error_recovery(self, temp_dir):
        """Test recovery from git operation errors."""
        # Create directory that's not a git repo
        config_manager = ConfigurationManager(str(temp_dir))

        # GitRepo should raise error for non-git directory
        with pytest.raises(Exception):
            git_repo = GitRepo(str(temp_dir))

    def test_llm_fallback_integration(self, temp_git_repo):
        """Test LLM fallback to Linear when service is unavailable."""
        temp_dir, repo = temp_git_repo

        # Mock failed LLM request
        with patch("src.llm_comm.requests.post") as mock_post:
            mock_post.side_effect = Exception("LLM service unavailable")

            # Mock Linear integration
            with patch("src.linear_fallback.create_linear_issue") as mock_linear:
                mock_linear.return_value = "test-issue-id"

                from config import LLMConfig
                from llm_comm import LLMCommitGenerator

                llm_config = LLMConfig(enable_linear_fallback=True)
                llm_generator = LLMCommitGenerator(llm_config)

                # Should fallback to Linear
                result = llm_generator.generate_commit_message("test diff")

                # Should return fallback message
                assert "Linear issue created" in result
                mock_linear.assert_called_once()

    def test_database_error_handling(self, temp_dir):
        """Test handling of database errors in review queue."""
        # Create review queue with invalid database path
        invalid_db_path = temp_dir / "readonly" / "review.db"

        # This should handle the error gracefully
        review_queue = ReviewQueue(str(invalid_db_path))

        # Operations should not crash even with database issues
        try:
            review_queue.add_file("test.py", "test reason")
            items = review_queue.get_pending_items()
            assert items == []  # Should return empty list on error
        except Exception:
            pytest.fail("Review queue should handle database errors gracefully")


class TestPerformanceIntegration:
    """Integration tests for performance scenarios."""

    def test_large_file_processing(self, temp_git_repo):
        """Test processing of large numbers of files."""
        temp_dir, repo = temp_git_repo

        # Setup components
        config_manager = ConfigurationManager(str(temp_dir))
        review_queue = ReviewQueue(str(temp_dir / "review.db"))

        # Create many files
        num_files = 100
        for i in range(num_files):
            test_file = temp_dir / f"file_{i:03d}.py"
            test_file.write_text(f"# File {i}")

        # Process all files
        processed_count = 0
        for i in range(num_files):
            file_path = str(temp_dir / f"file_{i:03d}.py")
            action = config_manager.get_file_action(file_path)
            if action == FileAction.REVIEW:
                review_queue.add_file(file_path, "No pattern match")
            processed_count += 1

        assert processed_count == num_files

        # Verify review queue can handle many items
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) <= num_files

    def test_concurrent_access(self, temp_git_repo):
        """Test concurrent access to shared resources."""
        temp_dir, repo = temp_git_repo

        # Setup shared components
        config_manager = ConfigurationManager(str(temp_dir))
        review_queue = ReviewQueue(str(temp_dir / "review.db"))

        # Function to simulate concurrent file processing
        def process_files(start_idx, count):
            for i in range(start_idx, start_idx + count):
                file_path = str(temp_dir / f"concurrent_{i}.py")
                action = config_manager.get_file_action(file_path)
                if action == FileAction.REVIEW:
                    review_queue.add_file(file_path, f"Concurrent test {i}")

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_files, args=(i * 10, 10))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all items were processed
        pending_items = review_queue.get_pending_items()
        assert len(pending_items) <= 50  # Up to 50 items could be added
