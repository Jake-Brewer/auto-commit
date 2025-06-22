"""
Pytest configuration and common fixtures for auto-commit tests.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch
import sqlite3
from git import Repo

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import AppConfig, LLMConfig
from config_manager import ConfigurationManager
from review_queue import ReviewQueue
from git_ops import GitRepo


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_git_repo(temp_dir):
    """Create a temporary git repository for testing."""
    repo = Repo.init(temp_dir)
    
    # Configure git user for testing
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    
    # Create initial commit
    test_file = temp_dir / "README.md"
    test_file.write_text("# Test Repository")
    repo.index.add([str(test_file)])
    repo.index.commit("Initial commit")
    
    yield temp_dir, repo


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    llm_config = LLMConfig()
    return AppConfig(
        watch_directory=".",
        log_level="INFO", 
        include_patterns=["*.py", "*.md"],
        exclude_patterns=["*.log", "__pycache__"],
        llm=llm_config
    )


@pytest.fixture
def config_manager(temp_dir):
    """Create a ConfigurationManager instance for testing."""
    return ConfigurationManager(str(temp_dir))


@pytest.fixture
def review_queue(temp_dir):
    """Create a ReviewQueue instance with temporary database."""
    db_path = temp_dir / "test_review.db"
    queue = ReviewQueue(str(db_path))
    yield queue
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def mock_git_repo():
    """Create a mock GitRepo for testing."""
    mock_repo = Mock(spec=GitRepo)
    mock_repo.repo = Mock()
    mock_repo.get_status.return_value = "M  test.py\nA  new_file.py"
    mock_repo.get_diff.return_value = "diff --git a/test.py b/test.py\n+new line"
    mock_repo.get_tracked_files.return_value = ["test.py", "README.md"]
    return mock_repo


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = {
        "test.py": "print('hello world')",
        "README.md": "# Test Project",
        "config.yml": "test: true",
        ".gitignore": "*.log\n__pycache__/",
        ".gitinclude": "*.py\n*.md"
    }
    
    created_files = {}
    for filename, content in files.items():
        file_path = temp_dir / filename
        file_path.write_text(content)
        created_files[filename] = file_path
    
    return created_files


@pytest.fixture
def mock_llm_response():
    """Mock LLM API response for testing."""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "feat: add new functionality"
        }
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_linear_api():
    """Mock Linear API calls for testing."""
    with patch('src.linear_integration.create_linear_issue') as mock_create, \
         patch('src.linear_integration.get_issue_comments') as mock_comments, \
         patch('src.linear_integration.update_linear_issue') as mock_update:
        
        mock_create.return_value = "test-issue-id"
        mock_comments.return_value = [
            {"body": "feat: implement new feature"}
        ]
        mock_update.return_value = True
        
        yield {
            'create': mock_create,
            'comments': mock_comments, 
            'update': mock_update
        }


# Test data constants
SAMPLE_DIFF = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
     print("hello")
+    print("world")
     return True
"""

SAMPLE_FILE_PATHS = ["test.py", "README.md", "config.yml"] 