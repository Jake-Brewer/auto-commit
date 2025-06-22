# Folder Guide: tests

## Purpose

This directory contains all the automated tests for the `auto-commit` project. The goal is to ensure code quality, prevent regressions, and validate the functionality of all components, both in isolation and as an integrated system.

## In-Scope

- Unit tests for individual modules and functions.
- Integration tests for component interactions and end-to-end workflows.
- Test fixtures, configurations, and helper utilities.
- Mocks for external services like Git, LLMs, and the Linear API.

## Out-of-Scope

- The main application source code (which resides in `/src`).
- Manual testing scripts.

## Subfolders

There are no subfolders in this directory.

## Files

- **`__init__.py`**: Initializes the `tests` directory as a Python package.
- **`conftest.py`**: Contains shared pytest fixtures used across multiple test files. This is where common setup and teardown logic resides (e.g., creating temporary repositories, mocking APIs).
- **`README.md`**: Provides a detailed guide on how to run tests, write new tests, and understand the testing framework for this project.
- **`test_config.py`**: Unit tests for the configuration loading and validation logic in `src/config.py`.
- **`test_config_manager.py`**: Unit tests for the `ConfigurationManager` class in `src/config_manager.py`.
- **`test_git_ops.py`**: Unit tests for the Git-related operations in `src/git_ops.py`.
- **`test_integration.py`**: Integration tests that cover the end-to-end workflow, from file system events to a final Git commit.
- **`test_review_queue.py`**: Unit tests for the `ReviewQueue` class in `src/review_queue.py`. 