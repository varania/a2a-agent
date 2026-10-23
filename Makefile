.DEFAULT_GOAL := help
UV ?= uv

.PHONY: help sync install run dev test cov lint format typecheck check docker-build docker-run clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

sync: ## Install/sync dependencies (including dev)
	$(UV) sync

install: sync ## Alias for `sync`

run: ## Run the A2A server
	$(UV) run a2a-agent

dev: ## Run the server with auto-reload
	$(UV) run a2a-agent --reload

test: ## Run the test suite
	$(UV) run pytest

cov: ## Run tests with coverage report
	$(UV) run pytest --cov --cov-report=term-missing

lint: ## Lint with ruff
	$(UV) run ruff check .

format: ## Format with ruff
	$(UV) run ruff format .

typecheck: ## Type-check with mypy
	$(UV) run mypy

check: lint typecheck test ## Lint + types + tests

docker-build: ## Build the container image
	docker build -t a2a-agent .

docker-run: ## Run the container (requires .env)
	docker run --rm -p 9999:9999 --env-file .env a2a-agent

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
