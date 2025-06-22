"""
Unit tests for the git_ops module.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import git
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_ops import GitRepo


class TestGitRepo:
    """Test cases for GitRepo class."""

    def test_init_existing_repo(self, temp_git_repo):
        """Test GitRepo initialization with existing repository."""
        temp_dir, repo = temp_git_repo

        git_repo = GitRepo(str(temp_dir))
        assert git_repo.repo_path == str(temp_dir)
        assert git_repo.repo is not None
        assert isinstance(git_repo.repo, git.Repo)

    def test_init_non_git_directory(self, temp_dir):
        """Test GitRepo initialization with non-git directory."""
        with pytest.raises(git.InvalidGitRepositoryError):
            GitRepo(str(temp_dir))

    def test_get_status_clean(self, temp_git_repo):
        """Test getting status of clean repository."""
        temp_dir, repo = temp_git_repo

        git_repo = GitRepo(str(temp_dir))
        status = git_repo.get_status()

        # Clean repo should have empty status
        assert status == ""

    def test_get_status_with_changes(self, temp_git_repo):
        """Test getting status with modified files."""
        temp_dir, repo = temp_git_repo

        # Modify existing file
        readme = temp_dir / "README.md"
        readme.write_text("# Modified Test Repository")

        # Add new file
        new_file = temp_dir / "new_file.py"
        new_file.write_text("print('hello')")

        git_repo = GitRepo(str(temp_dir))
        status = git_repo.get_status()

        assert "README.md" in status
        assert "new_file.py" in status

    def test_add_files_single(self, temp_git_repo):
        """Test adding a single file."""
        temp_dir, repo = temp_git_repo

        # Create new file
        new_file = temp_dir / "test.py"
        new_file.write_text("print('test')")

        git_repo = GitRepo(str(temp_dir))
        git_repo.add_files([str(new_file)])

        # Check if file is staged
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        assert "test.py" in staged_files

    def test_add_files_multiple(self, temp_git_repo):
        """Test adding multiple files."""
        temp_dir, repo = temp_git_repo

        # Create multiple files
        files = []
        for i in range(3):
            file_path = temp_dir / f"test{i}.py"
            file_path.write_text(f"print('test{i}')")
            files.append(str(file_path))

        git_repo = GitRepo(str(temp_dir))
        git_repo.add_files(files)

        # Check if all files are staged
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        for i in range(3):
            assert f"test{i}.py" in staged_files

    def test_add_files_nonexistent(self, temp_git_repo):
        """Test adding nonexistent file raises error."""
        temp_dir, repo = temp_git_repo

        git_repo = GitRepo(str(temp_dir))

        with pytest.raises(git.GitCommandError):
            git_repo.add_files(["nonexistent.py"])

    def test_commit_with_message(self, temp_git_repo):
        """Test committing with custom message."""
        temp_dir, repo = temp_git_repo

        # Create and stage a file
        new_file = temp_dir / "commit_test.py"
        new_file.write_text("print('commit test')")

        git_repo = GitRepo(str(temp_dir))
        git_repo.add_files([str(new_file)])

        commit_message = "feat: add commit test file"
        commit_sha = git_repo.commit(commit_message)

        assert commit_sha is not None
        assert len(commit_sha) == 40  # SHA-1 hash length

        # Verify commit message
        latest_commit = repo.head.commit
        assert latest_commit.message.strip() == commit_message

    def test_commit_no_changes(self, temp_git_repo):
        """Test committing with no staged changes."""
        temp_dir, repo = temp_git_repo

        git_repo = GitRepo(str(temp_dir))

        # Should return None when nothing to commit
        commit_sha = git_repo.commit("No changes")
        assert commit_sha is None

    def test_get_diff_staged(self, temp_git_repo):
        """Test getting diff of staged changes."""
        temp_dir, repo = temp_git_repo

        # Modify existing file
        readme = temp_dir / "README.md"
        readme.write_text("# Modified Test Repository\nNew line added")

        git_repo = GitRepo(str(temp_dir))
        git_repo.add_files([str(readme)])

        diff = git_repo.get_diff()

        assert "README.md" in diff
        assert "New line added" in diff
        assert "+New line added" in diff

    def test_get_diff_no_changes(self, temp_git_repo):
        """Test getting diff with no staged changes."""
        temp_dir, repo = temp_git_repo

        git_repo = GitRepo(str(temp_dir))
        diff = git_repo.get_diff()

        assert diff == ""

    def test_get_diff_working_directory(self, temp_git_repo):
        """Test getting diff of working directory changes."""
        temp_dir, repo = temp_git_repo

        # Modify file but don't stage
        readme = temp_dir / "README.md"
        readme.write_text("# Modified Test Repository\nUnstaged change")

        git_repo = GitRepo(str(temp_dir))
        diff = git_repo.get_diff(staged=False)

        assert "README.md" in diff
        assert "Unstaged change" in diff

    def test_get_tracked_files(self, temp_git_repo):
        """Test getting list of tracked files."""
        temp_dir, repo = temp_git_repo

        # Add additional files
        for i in range(3):
            file_path = temp_dir / f"tracked{i}.py"
            file_path.write_text(f"# File {i}")
            repo.index.add([str(file_path)])

        repo.index.commit("Add tracked files")

        git_repo = GitRepo(str(temp_dir))
        tracked_files = git_repo.get_tracked_files()

        assert "README.md" in tracked_files
        for i in range(3):
            assert f"tracked{i}.py" in tracked_files

    def test_get_tracked_files_empty_repo(self, temp_dir):
        """Test getting tracked files from empty repository."""
        # Create empty git repo
        repo = git.Repo.init(temp_dir)
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        git_repo = GitRepo(str(temp_dir))
        tracked_files = git_repo.get_tracked_files()

        assert tracked_files == []

    @patch("git_ops.git.Repo")
    def test_git_command_error_handling(self, mock_repo_class):
        """Test handling of git command errors."""
        # Mock repo that raises GitCommandError
        mock_repo = Mock()
        mock_repo.git.status.side_effect = git.GitCommandError("status", 1, "error")
        mock_repo_class.return_value = mock_repo

        git_repo = GitRepo("/fake/path")

        # Should handle GitCommandError gracefully
        status = git_repo.get_status()
        assert status == ""

    def test_repo_property_access(self, temp_git_repo):
        """Test accessing the underlying repo property."""
        temp_dir, repo = temp_git_repo

        git_repo = GitRepo(str(temp_dir))

        # Should return the git.Repo instance
        assert git_repo.repo is not None
        assert isinstance(git_repo.repo, git.Repo)
        assert git_repo.repo.working_dir == str(temp_dir)

    def test_add_all_files(self, temp_git_repo):
        """Test adding all modified files."""
        temp_dir, repo = temp_git_repo

        # Create multiple files
        for i in range(3):
            file_path = temp_dir / f"bulk{i}.py"
            file_path.write_text(f"# Bulk file {i}")

        git_repo = GitRepo(str(temp_dir))
        git_repo.add_files(["."])  # Add all files

        # Check if all files are staged
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        for i in range(3):
            assert f"bulk{i}.py" in staged_files
