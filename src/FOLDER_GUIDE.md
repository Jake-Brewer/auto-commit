# Folder Guide: src/

## Purpose
This directory contains all the Python source code for the `auto-commit` agent.

## In-Scope
- Core application logic.
- Modules for file watching, Git interaction, configuration management, and LLM communication.
- The main application entry point.

## Out-of-Scope
- Documentation (belongs in the root `docs/` folder or other documentation folders).
- Test code (will belong in a separate `tests/` directory).
- Configuration files (belong in the root directory).

## Files
- `main.py`: The main entry point for the `auto-commit` agent application.
- `watcher.py`: Contains the file system monitoring logic using the `watchdog` library.
- `config.py`: Handles loading and validation of the application's YAML configuration.
- `config_manager.py`: Manages hierarchical .gitinclude and .gitignore files for advanced file filtering rules.
- `commit_worker.py`: Worker thread pool for processing file change events. Implements CommitWorker and CommitWorkerPool classes.
- `file_filter.py`: Implements the logic for including/excluding file paths based on glob patterns.
- `git_ops.py`: Provides a wrapper for Git operations using the GitPython library.
- `llm_comm.py`: Handles communication with a Large Language Model for commit message generation. 