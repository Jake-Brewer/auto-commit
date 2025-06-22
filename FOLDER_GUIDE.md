# Root Directory Guide

## Purpose
This is the root directory for the `auto-commit` utility project.

## In-Scope
- Core configuration files for LLM behavior (`_llm_primer.md`).
- Project-level documentation and task tracking.
- Subdirectories containing specialized LLM instructions.

## Out-of-Scope
- Application source code (should be in a `src` or similar directory).
- Docker or MCP-related utilities (belong in the `docker-command-center` project).

## Files
- `_llm_primer.md`: Core behavioral standards and critical instructions for LLM agents working on this project.
- `REQUIREMENTS.md`: The functional and non-functional requirements for the `auto-commit` agent.
- `DESIGN.md`: The high-level system design for the `auto-commit` agent.
- `requirements.txt`: A list of Python packages required to run the project.
- `.gitignore`: A list of file patterns for Git to ignore.

## Subfolders
- `docs/`: Contains supplementary design documents, such as UI mockups.
- `for_llm/`: Contains specialized primer files for different LLM agent functions.
- `src/`: Contains all the Python source code for the `auto-commit` agent.

## Files
- `for_llm_todo.md`: A real-time task list for the AI assistant. 