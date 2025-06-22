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