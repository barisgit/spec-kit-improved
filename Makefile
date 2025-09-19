.PHONY: help lint format format-check test coverage pre-commit all ci ci-windows ci-ubuntu ci-macos

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z0-9][a-zA-Z0-9_-]+:.*##/ {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

lint: ## Run Ruff lint
	uv run ruff check

format: ## Run Ruff formatter
	uv run ruff format

format-check: ## Check formatting with Ruff
	uv run ruff format --check

test: ## Run pytest
	uv run pytest

coverage: ## Run tests with coverage
	uv run pytest --cov=src --cov-report=term-missing

pre-commit: ## Run all pre-commit hooks on all files
	pre-commit run --all-files

all: lint format-check test coverage ## Run lint, format-check, tests, and coverage

ci: ## Run full CI pipeline locally using act
	@echo "Running full CI pipeline locally..."
	act -j test --container-architecture linux/amd64

ci-fast: ## Run fast CI using pre-built containers
	@echo "Running fast CI with pre-built containers..."
	act -j test --use-gitignore --artifact-server-path /tmp/artifacts --container-architecture linux/amd64

ci-ubuntu: ## Run CI tests on Ubuntu environment  
	@echo "Running CI tests on Ubuntu environment..."
	act -j test --matrix os:ubuntu-latest --container-architecture linux/amd64

ci-ubuntu-311: ## Run CI tests on Ubuntu environment for Python 3.11
	@echo "Running CI tests on Ubuntu environment for Python 3.11..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.11 --container-architecture linux/amd64

ci-ubuntu-312: ## Run CI tests on Ubuntu environment for Python 3.12
	@echo "Running CI tests on Ubuntu environment for Python 3.12..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.12 --container-architecture linux/amd64

ci-ubuntu-313: ## Run CI tests on Ubuntu environment for Python 3.13
	@echo "Running CI tests on Ubuntu environment for Python 3.13..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.13 --container-architecture linux/amd64

ci-macos: ## Run CI tests on macOS environment
	@echo "Running CI tests on macOS environment..."
	act -j test --matrix os:macos-latest --matrix python-version:3.11 --container-architecture linux/amd64