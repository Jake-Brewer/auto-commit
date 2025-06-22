.PHONY: help install test test-unit test-integration lint format type-check clean coverage pre-commit setup-dev

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

setup-dev: ## Setup development environment
	pip install -r requirements.txt
	pre-commit install
	@echo "Development environment setup complete!"

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest -m "not integration" tests/

test-integration: ## Run integration tests only
	pytest -m integration tests/

test-verbose: ## Run tests with verbose output
	pytest -v

coverage: ## Run tests with coverage report
	pytest --cov=src --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	flake8 src/ tests/
	mypy src/

format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/

format-check: ## Check code formatting without making changes
	black --check src/ tests/
	isort --check-only src/ tests/

type-check: ## Run type checking
	mypy src/

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf build/
	rm -rf dist/

quality: ## Run all quality checks
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test

ci: ## Run CI pipeline locally
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) quality

# Development workflow targets
dev-test: ## Quick development test (unit tests only)
	pytest -x tests/ -m "not integration"

dev-check: ## Quick development check (format + lint + unit tests)
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) dev-test

# File watching for development
watch-tests: ## Watch for changes and run tests
	pytest-watch -- tests/

# Security checks
security: ## Run security checks
	bandit -r src/
	safety check

# Documentation
docs: ## Generate documentation
	@echo "Documentation generation not yet implemented"

# Docker targets (if needed)
docker-build: ## Build Docker image
	@echo "Docker build not yet implemented"

docker-test: ## Run tests in Docker
	@echo "Docker test not yet implemented" 