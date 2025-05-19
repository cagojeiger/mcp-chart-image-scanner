# Makefile for mcp-chart-image-scanner
# Allows running CI checks locally

.PHONY: setup lint test build all clean helm venv help

PYTHON_VERSION := 3.10
PROJECT_DIR := mcp_chart_scanner
TEST_DIR := tests
VENV_DIR := venv

# Default target
help:
	@echo "Available targets:"
	@echo "  setup    - Install dependencies and Helm"
	@echo "  lint     - Run linting checks (black, isort, flake8)"
	@echo "  test     - Run tests with pytest"
	@echo "  build    - Build the package"
	@echo "  all      - Run lint, test, and build"
	@echo "  clean    - Remove build artifacts"
	@echo "  helm     - Install Helm CLI if not already installed"
	@echo "  venv     - Create virtual environment"
	@echo "  help     - Show this help message"

# Run all CI checks
all: lint test build

# Setup virtual environment
venv:
	@echo "Creating virtual environment..."
	python -m venv $(VENV_DIR)
	@echo "Virtual environment created at $(VENV_DIR)"

# Setup target - install dependencies and Helm
setup: venv helm
	@echo "Setting up development environment..."
	. $(VENV_DIR)/bin/activate && \
	python -m pip install --upgrade pip && \
	pip install flake8 black isort pytest pytest-cov pytest-asyncio build && \
	pip install -e .
	@echo "Setup complete."

# Install Helm CLI
helm:
	@echo "Checking for Helm installation..."
	@if ! command -v helm &> /dev/null; then \
		echo "Installing Helm..."; \
		curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3; \
		chmod 700 get_helm.sh; \
		./get_helm.sh; \
		rm get_helm.sh; \
	else \
		echo "Helm already installed: $$(helm version)"; \
	fi

# Lint target - check code formatting with black, isort, and flake8
lint: venv
	@echo "Checking code formatting with Black..."
	. $(VENV_DIR)/bin/activate && black --check $(PROJECT_DIR) $(TEST_DIR)
	@echo "Checking imports with isort..."
	. $(VENV_DIR)/bin/activate && isort --check $(PROJECT_DIR) $(TEST_DIR)
	@echo "Linting with flake8..."
	. $(VENV_DIR)/bin/activate && flake8 $(PROJECT_DIR) $(TEST_DIR) --max-line-length=120

# Test target - run pytest with coverage
test: venv helm
	@echo "Running tests with pytest..."
	. $(VENV_DIR)/bin/activate && pytest --cov=$(PROJECT_DIR) $(TEST_DIR)

# Build target - build the package
build: venv
	@echo "Building package..."
	. $(VENV_DIR)/bin/activate && python -m build

# Clean target - remove build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf dist/
	rm -rf build/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete."

# This help target is now at the beginning of the file as the default target
