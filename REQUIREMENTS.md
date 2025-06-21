# Project Requirements: auto-commit Agent

## 1. Introduction

This document outlines the functional and non-functional requirements for the `auto-commit` agent. The purpose of this agent is to provide autonomous version control by monitoring specified directories and intelligently committing changes with high-quality, LLM-generated messages.

## 2. Functional Requirements

### 2.1. File System Monitoring
- **REQ-F-01**: The system **shall** monitor a configurable list of local directories for file changes (creation, deletion, modification).
- **REQ-F-02**: File change events **shall** be added to a thread-safe queue for asynchronous processing.

### 2.2. Git Repository Management
- **REQ-F-03**: For any given file change, the system **shall** identify the correct parent Git repository.
- **REQ-F-04**: If a monitored folder is not already a Git repository, the system **shall** automatically initialize a new repository (`git init`) within it.

### 2.3. Commit Generation
- **REQ-F-05**: The system **shall** analyze the file changes (`diff`) to gather context for a commit.
- **REQ-F-06**: The system **shall** interface with an LLM, providing the `diff` and style guide, to generate a structured commit message compliant with the Conventional Commits specification.
- **REQ-F-07**: The system **shall** intelligently manage a `.gitignore` file, adding rules for common temporary or build-related files rather than committing them.

### 2.4. Execution
- **REQ-F-08**: The system **shall** stage the relevant changes using `git add`.
- **REQ-F-09**: The system **shall** execute the commit using the LLM-generated message.

## 3. Non-Functional Requirements

- **REQ-NF-01**: **Performance**: The file monitoring process must be lightweight and have minimal impact on system performance.
- **REQ-NF-02**: **Reliability**: The system must be resilient to LLM API failures, falling back to a default commit message and logging the error if necessary.
- **REQ-NF-03**: **Security**: The system must not expose any sensitive information, such as API keys, in its logs or commit history.
- **REQ-N-04**: The system **shall** be designed in a modular fashion to allow for future expansion, such as supporting different version control systems or LLM providers.

## 4. File Inclusion/Exclusion Logic

This section details the logic for determining whether a new, untracked file should be committed, ignored, or flagged for user review.

### 4.1. Configuration File Hierarchy
The system will use a hierarchy of configuration files to make decisions. The order of precedence is as follows:
1.  **Project `.gitinclude`**: Highest priority. Patterns in this file force inclusion.
2.  **Global `.gitinclude`**: Second priority.
3.  **Project `.gitignore`**: Third priority.
4.  **Global `.gitignore`**: Lowest priority.

### 4.2. Default Ignore Patterns
- **REQ-F-07**: The system **shall** maintain a hardcoded list of common file/folder patterns to ignore (e.g., `node_modules/`, `__pycache__/`, `*.log`, `data/`, `log/`).
- **REQ-F-08**: A default ignore pattern **shall only** be added to a project's `.gitignore` if no files currently tracked in the repository match that pattern.

### 4.3. Human-in-the-Loop for Ambiguous Files
- **REQ-F-09**: If a new, untracked file is not covered by any pattern in the configuration hierarchy, it **shall** be added to a queue for human review.
- **REQ-F-10**: The system **shall** provide a user interface for reviewing ambiguous files.
- **REQ-F-11**: The review UI **shall** present the user with the following options for each file:
    - Add a pattern to `project.gitignore` or `project.gitinclude`.
    - Add a pattern to `global.gitignore` or `global.gitinclude`.
    - Take no action for that file at either the project or global level (the default state, `gitdefault`).
- **REQ-F-12**: Once a pattern covering a file is added to any of the four configuration files, the user **shall not** be prompted to review that file again.

## 5. Assumptions and Constraints

- **A-01**: The agent will run on the user's local machine with access to the file system and the ability to run Git commands.
- **A-02**: A local Docker-hosted LLM (`sequentialthought`) is available and is the primary choice for generating commit messages.
- **A-03**: The system will assume it has primary control over the repositories. It will halt operations on a given repository if the working directory is not clean for reasons other than its own changes.

## 3. File Inclusion/Exclusion Logic

This section details the logic for determining whether a new, untracked file should be committed, ignored, or flagged for user review.

### 3.1. Configuration File Hierarchy
The system will use a hierarchy of configuration files to make decisions. The order of precedence is as follows:
1.  **Project `.gitinclude`**: Highest priority. Patterns in this file force inclusion.
2.  **Global `.gitinclude`**: Second priority.
3.  **Project `.gitignore`**: Third priority.
4.  **Global `.gitignore`**: Lowest priority.

### 3.2. Default Ignore Patterns
- **REQ-F-07**: The system **shall** maintain a hardcoded list of common file/folder patterns to ignore (e.g., `node_modules/`, `__pycache__/`, `*.log`, `data/`, `log/`).
- **REQ-F-08**: A default ignore pattern **shall only** be added to a project's `.gitignore` if no files currently tracked in the repository match that pattern.

### 3.3. Human-in-the-Loop for Ambiguous Files
- **REQ-F-09**: If a new, untracked file is not covered by any pattern in the configuration hierarchy, it **shall** be added to a queue for human review.
- **REQ-F-10**: The system **shall** provide a user interface for reviewing ambiguous files.
- **REQ-F-11**: The review UI **shall** present the user with the following options for each file:
    - Add a pattern to `project.gitignore` or `project.gitinclude`.
    - Add a pattern to `global.gitignore` or `global.gitinclude`.
    - Take no action for that file at either the project or global level (the default state, `gitdefault`).
- **REQ-F-12**: Once a pattern covering a file is added to any of the four configuration files, the user **shall not** be prompted to review that file again. 