"""
Unit tests for the config_manager module.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigurationManager, FileAction


class TestFileAction:
    """Test cases for FileAction enum."""

    def test_file_action_values(self):
        """Test FileAction enum values."""
        assert FileAction.INCLUDE.value == "include"
        assert FileAction.IGNORE.value == "ignore"
        assert FileAction.REVIEW.value == "review"


class TestConfigurationManager:
    """Test cases for ConfigurationManager class."""

    def test_init(self, temp_dir):
        """Test ConfigurationManager initialization."""
        cm = ConfigurationManager(str(temp_dir))
        assert cm.watch_directory == temp_dir
        assert cm._config_cache == {}

    def test_find_config_files_no_files(self, config_manager, temp_dir):
        """Test finding config files when none exist."""
        test_file = temp_dir / "test.py"
        test_file.touch()

        config_files = config_manager._find_config_files(test_file)
        assert config_files == []

    def test_find_config_files_with_gitignore(self, config_manager, temp_dir):
        """Test finding config files with .gitignore present."""
        # Create .gitignore in watch directory
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("*.log\n__pycache__/")

        test_file = temp_dir / "test.py"
        test_file.touch()

        config_files = config_manager._find_config_files(test_file)
        assert len(config_files) == 1
        assert config_files[0] == (gitignore, "ignore")

    def test_find_config_files_with_gitinclude(self, config_manager, temp_dir):
        """Test finding config files with .gitinclude present."""
        # Create .gitinclude in watch directory
        gitinclude = temp_dir / ".gitinclude"
        gitinclude.write_text("*.py\n*.md")

        test_file = temp_dir / "test.py"
        test_file.touch()

        config_files = config_manager._find_config_files(test_file)
        assert len(config_files) == 1
        assert config_files[0] == (gitinclude, "include")

    def test_find_config_files_hierarchical(self, config_manager, temp_dir):
        """Test finding config files in hierarchical structure."""
        # Create nested directory structure
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        # Create config files at different levels
        root_gitignore = temp_dir / ".gitignore"
        root_gitignore.write_text("*.log")

        sub_gitinclude = subdir / ".gitinclude"
        sub_gitinclude.write_text("*.py")

        test_file = subdir / "test.py"
        test_file.touch()

        config_files = config_manager._find_config_files(test_file)

        # Should find both files in correct order (root first, then subdir)
        assert len(config_files) == 2
        assert config_files[0] == (root_gitignore, "ignore")
        assert config_files[1] == (sub_gitinclude, "include")

    def test_parse_config_file(self, config_manager, temp_dir):
        """Test parsing configuration files."""
        config_file = temp_dir / ".gitignore"
        config_file.write_text("*.log\n# Comment line\n__pycache__/\n\n*.tmp")

        patterns = config_manager._parse_config_file(config_file)

        # Should exclude comments and empty lines
        assert patterns == ["*.log", "__pycache__/", "*.tmp"]

    def test_parse_config_file_caching(self, config_manager, temp_dir):
        """Test that config file parsing uses caching."""
        config_file = temp_dir / ".gitignore"
        config_file.write_text("*.log")

        # First call
        patterns1 = config_manager._parse_config_file(config_file)
        assert config_file in config_manager._config_cache

        # Second call should use cache
        patterns2 = config_manager._parse_config_file(config_file)
        assert patterns1 == patterns2

    def test_matches_pattern_simple(self, config_manager, temp_dir):
        """Test simple pattern matching."""
        test_file = temp_dir / "test.log"
        pattern = "*.log"

        assert config_manager._matches_pattern(test_file, pattern, temp_dir)

    def test_matches_pattern_directory(self, config_manager, temp_dir):
        """Test directory pattern matching."""
        subdir = temp_dir / "cache"
        subdir.mkdir()
        test_file = subdir / "file.py"
        test_file.touch()

        pattern = "cache/"
        assert config_manager._matches_pattern(test_file, pattern, temp_dir)

    def test_matches_pattern_no_match(self, config_manager, temp_dir):
        """Test pattern that doesn't match."""
        test_file = temp_dir / "test.py"
        pattern = "*.log"

        assert not config_manager._matches_pattern(test_file, pattern, temp_dir)

    def test_get_file_action_no_config(self, config_manager, temp_dir):
        """Test file action when no config files exist."""
        test_file = temp_dir / "test.py"
        test_file.touch()

        action = config_manager.get_file_action(str(test_file))
        assert action == FileAction.REVIEW

    def test_get_file_action_include_only(self, config_manager, temp_dir):
        """Test file action with include pattern only."""
        gitinclude = temp_dir / ".gitinclude"
        gitinclude.write_text("*.py")

        test_file = temp_dir / "test.py"
        test_file.touch()

        action = config_manager.get_file_action(str(test_file))
        assert action == FileAction.INCLUDE

    def test_get_file_action_ignore_only(self, config_manager, temp_dir):
        """Test file action with ignore pattern only."""
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("*.log")

        test_file = temp_dir / "test.log"
        test_file.touch()

        action = config_manager.get_file_action(str(test_file))
        assert action == FileAction.IGNORE

    def test_get_file_action_ambiguous(self, config_manager, temp_dir):
        """Test file action with conflicting patterns."""
        gitinclude = temp_dir / ".gitinclude"
        gitinclude.write_text("*.py")

        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("*.py")

        test_file = temp_dir / "test.py"
        test_file.touch()

        action = config_manager.get_file_action(str(test_file))
        assert action == FileAction.REVIEW

    def test_add_pattern_include_project(self, config_manager, temp_dir):
        """Test adding include pattern at project level."""
        test_file = temp_dir / "test.py"

        success = config_manager.add_pattern(
            pattern="*.py",
            action=FileAction.INCLUDE,
            scope="project",
            project_path=str(test_file),
        )

        assert success
        gitinclude_path = temp_dir / ".gitinclude"
        assert gitinclude_path.exists()
        assert "*.py" in gitinclude_path.read_text()

    def test_add_pattern_ignore_global(self, config_manager, temp_dir):
        """Test adding ignore pattern at global level."""
        success = config_manager.add_pattern(
            pattern="*.log", action=FileAction.IGNORE, scope="global"
        )

        assert success
        gitignore_path = temp_dir / ".gitignore"
        assert gitignore_path.exists()
        assert "*.log" in gitignore_path.read_text()

    def test_add_pattern_duplicate(self, config_manager, temp_dir):
        """Test adding duplicate pattern."""
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("*.log\n")

        success = config_manager.add_pattern(
            pattern="*.log", action=FileAction.IGNORE, scope="global"
        )

        assert success  # Should succeed but not duplicate
        content = gitignore.read_text()
        assert content.count("*.log") == 1

    def test_add_pattern_invalid_action(self, config_manager):
        """Test adding pattern with invalid action."""
        success = config_manager.add_pattern(
            pattern="*.py",
            action=FileAction.REVIEW,  # Cannot add REVIEW patterns
            scope="project",
        )

        assert not success

    @patch("src.config_manager.GitRepo")
    def test_safe_add_default_ignores(
        self, mock_git_repo_class, config_manager, temp_dir
    ):
        """Test safe addition of default ignore patterns."""
        # Mock GitRepo
        mock_repo = Mock()
        mock_repo.repo = Mock()
        mock_repo.get_tracked_files.return_value = ["README.md", "src/main.py"]
        mock_git_repo_class.return_value = mock_repo

        success = config_manager.safe_add_default_ignores()

        assert success
        gitignore_path = temp_dir / ".gitignore"
        assert gitignore_path.exists()

        content = gitignore_path.read_text()
        # Should add patterns that don't conflict with tracked files
        assert "node_modules/" in content
        assert "__pycache__/" in content
        assert "*.log" in content

    @patch("src.config_manager.GitRepo")
    def test_safe_add_default_ignores_with_conflicts(
        self, mock_git_repo_class, config_manager, temp_dir
    ):
        """Test safe addition when tracked files would conflict."""
        # Mock GitRepo with tracked files that match some default patterns
        mock_repo = Mock()
        mock_repo.repo = Mock()
        mock_repo.get_tracked_files.return_value = [
            "build/config.py",
            "dist/package.tar.gz",
        ]
        mock_git_repo_class.return_value = mock_repo

        # Mock the pattern matching to return True for conflicting patterns
        with patch.object(
            config_manager, "_has_tracked_files_matching_pattern"
        ) as mock_match:
            mock_match.side_effect = lambda repo, pattern: pattern in [
                "build/",
                "dist/",
            ]

            success = config_manager.safe_add_default_ignores()

        assert success
        gitignore_path = temp_dir / ".gitignore"
        content = gitignore_path.read_text()

        # Should not add conflicting patterns
        assert "build/" not in content
        assert "dist/" not in content
        # Should add non-conflicting patterns
        assert "node_modules/" in content

    def test_clear_cache(self, config_manager, temp_dir):
        """Test cache clearing."""
        config_file = temp_dir / ".gitignore"
        config_file.write_text("*.log")

        # Populate cache
        config_manager._parse_config_file(config_file)
        assert len(config_manager._config_cache) > 0

        # Clear cache
        config_manager.clear_cache()
        assert len(config_manager._config_cache) == 0

    def test_get_stats(self, config_manager, temp_dir):
        """Test getting configuration statistics."""
        config_file = temp_dir / ".gitignore"
        config_file.write_text("*.log")

        # Populate cache
        config_manager._parse_config_file(config_file)

        stats = config_manager.get_stats()

        assert "watch_directory" in stats
        assert "cached_config_files" in stats
        assert "cache_files" in stats
        assert stats["cached_config_files"] == 1
        assert str(config_file) in stats["cache_files"]
