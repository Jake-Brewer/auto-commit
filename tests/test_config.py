"""
Unit tests for the config module.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import AppConfig, LLMConfig, load_config


class TestLLMConfig:
    """Test cases for LLMConfig dataclass."""

    def test_llm_config_defaults(self):
        """Test LLMConfig default values."""
        config = LLMConfig()
        assert config.base_url == "http://localhost:11434"
        assert config.model_name == "sequentialthought"
        assert config.timeout_seconds == 30
        assert config.enable_linear_fallback is True
        assert config.fallback_team_id == "b5f1d099-acc2-4e51-a415-76c00c00f23b"
        assert config.fallback_project_id is None

    def test_llm_config_custom_values(self):
        """Test LLMConfig with custom values."""
        config = LLMConfig(
            base_url="http://custom:8080",
            model_name="custom-model",
            timeout_seconds=60,
            enable_linear_fallback=False,
            fallback_team_id="custom-team",
            fallback_project_id="custom-project",
        )
        assert config.base_url == "http://custom:8080"
        assert config.model_name == "custom-model"
        assert config.timeout_seconds == 60
        assert config.enable_linear_fallback is False
        assert config.fallback_team_id == "custom-team"
        assert config.fallback_project_id == "custom-project"


class TestAppConfig:
    """Test cases for AppConfig dataclass."""

    def test_app_config_creation(self):
        """Test AppConfig creation with all fields."""
        llm_config = LLMConfig()
        config = AppConfig(
            watch_directory="/test/path",
            log_level="DEBUG",
            include_patterns=["*.py"],
            exclude_patterns=["*.log"],
            llm=llm_config,
        )
        assert config.watch_directory == "/test/path"
        assert config.log_level == "DEBUG"
        assert config.include_patterns == ["*.py"]
        assert config.exclude_patterns == ["*.log"]
        assert config.llm == llm_config


class TestLoadConfig:
    """Test cases for load_config function."""

    def test_load_config_success(self):
        """Test successful config loading."""
        config_data = {
            "watch_directory": "/test/dir",
            "log_level": "DEBUG",
            "include_patterns": ["*.py", "*.md"],
            "exclude_patterns": ["*.log", "*.tmp"],
            "llm": {
                "base_url": "http://test:1234",
                "model_name": "test-model",
                "timeout_seconds": 45,
                "enable_linear_fallback": False,
                "fallback_team_id": "test-team",
                "fallback_project_id": "test-project",
            },
        }

        yaml_content = yaml.dump(config_data)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = load_config("test_config.yml")

        assert config.watch_directory == "/test/dir"
        assert config.log_level == "DEBUG"
        assert config.include_patterns == ["*.py", "*.md"]
        assert config.exclude_patterns == ["*.log", "*.tmp"]
        assert config.llm.base_url == "http://test:1234"
        assert config.llm.model_name == "test-model"
        assert config.llm.timeout_seconds == 45
        assert config.llm.enable_linear_fallback is False
        assert config.llm.fallback_team_id == "test-team"
        assert config.llm.fallback_project_id == "test-project"

    def test_load_config_minimal(self):
        """Test config loading with minimal required fields."""
        config_data = {"watch_directory": "/minimal/dir"}

        yaml_content = yaml.dump(config_data)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = load_config("minimal_config.yml")

        assert config.watch_directory == "/minimal/dir"
        assert config.log_level == "INFO"  # Default
        assert config.include_patterns == ["*"]  # Default
        assert config.exclude_patterns == []  # Default
        assert config.llm.base_url == "http://localhost:11434"  # Default

    def test_load_config_missing_watch_directory(self):
        """Test config loading fails without watch_directory."""
        config_data = {"log_level": "INFO"}

        yaml_content = yaml.dump(config_data)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with pytest.raises(
                ValueError, match="Configuration must define 'watch_directory'"
            ):
                load_config("invalid_config.yml")

    def test_load_config_file_not_found(self):
        """Test config loading with missing file."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_config.yml")

    def test_load_config_invalid_yaml(self):
        """Test config loading with invalid YAML."""
        invalid_yaml = "invalid: yaml: content: ["

        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(ValueError, match="Error parsing YAML file"):
                load_config("invalid_yaml.yml")

    def test_load_config_empty_file(self):
        """Test config loading with empty file."""
        with patch("builtins.open", mock_open(read_data="")):
            with pytest.raises(
                ValueError, match="Configuration must define 'watch_directory'"
            ):
                load_config("empty_config.yml")

    def test_load_config_partial_llm_config(self):
        """Test config loading with partial LLM configuration."""
        config_data = {
            "watch_directory": "/test/dir",
            "llm": {"model_name": "custom-model"},
        }

        yaml_content = yaml.dump(config_data)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = load_config("partial_llm_config.yml")

        assert config.llm.model_name == "custom-model"
        assert config.llm.base_url == "http://localhost:11434"  # Default
        assert config.llm.timeout_seconds == 30  # Default

    def test_load_config_with_real_file(self, temp_dir):
        """Test config loading with actual file I/O."""
        config_data = {
            "watch_directory": str(temp_dir),
            "log_level": "WARNING",
            "include_patterns": ["*.txt"],
            "exclude_patterns": ["*.bak"],
        }

        config_file = temp_dir / "test_config.yml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(str(config_file))

        assert config.watch_directory == str(temp_dir)
        assert config.log_level == "WARNING"
        assert config.include_patterns == ["*.txt"]
        assert config.exclude_patterns == ["*.bak"]
