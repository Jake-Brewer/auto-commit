# Folder Guide: .github/workflows

## Purpose

This directory contains all the GitHub Actions workflow definitions for the project. These workflows automate tasks such as running tests, linting code, building artifacts, and deploying the application.

## In-Scope

- YAML files (`.yml`) defining GitHub Actions workflows.
- Scripts that are called directly and exclusively by the workflows in this directory.

## Out-of-Scope

- General-purpose scripts (these should be in a `scripts/` directory at the project root).
- Configuration files for tools run by the workflows (e.g., `pytest.ini`).

## Files

- **`ci.yml`**: The main Continuous Integration (CI) workflow. It runs on every push and pull request to the `master` branch. It installs dependencies, runs tests, and performs static analysis. 