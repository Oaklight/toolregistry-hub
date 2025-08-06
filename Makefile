# Makefile for toolregistry-hub package

# Variables
PACKAGE_NAME := toolregistry-hub
DIST_DIR := dist

# Default target
all: build

# Build the package
build: clean
	@echo "Building $(PACKAGE_NAME) package..."
	python -m build
	@echo "Build complete. Distribution files are in $(DIST_DIR)/"

# Push the package to PyPI
push:
	@echo "Pushing $(PACKAGE_NAME) to PyPI..."
	twine upload $(DIST_DIR)/*
	@echo "Package pushed to PyPI."

# Push the package to Test PyPI
push-test:
	@echo "Pushing $(PACKAGE_NAME) to Test PyPI..."
	twine upload --repository testpypi $(DIST_DIR)/*
	@echo "Package pushed to Test PyPI."

# Release workflow
release: clean build push clean
	@echo "Release completed successfully!"

# Test release workflow
release-test: clean build push-test clean
	@echo "Test release completed successfully!"

# Install development dependencies
install-dev:
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"
	@echo "Development dependencies installed."

# Clean up build and distribution files
clean:
	@echo "Cleaning up build and distribution files..."
	rm -rf $(DIST_DIR) *.egg-info build/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Cleanup complete."

# Check package integrity
check:
	@echo "Checking package..."
	python -m build --check
	twine check $(DIST_DIR)/*
	@echo "Package check completed."

# Show package info
info:
	@echo "Package: $(PACKAGE_NAME)"
	@echo "Version: $$(python -c 'import tomllib; print(tomllib.load(open(\"pyproject.toml\", \"rb\"))[\"project\"][\"version\"])')"
	@echo "Distribution directory: $(DIST_DIR)"

# Run tests (delegates to tests/Makefile)
test:
	@echo "Running tests..."
	$(MAKE) -C tests test
	@echo "Tests completed."

# Help target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Build and release:"
	@echo "  build         - Build the package"
	@echo "  push          - Push to PyPI"
	@echo "  push-test     - Push to Test PyPI"
	@echo "  release       - Full release workflow (build + push)"
	@echo "  release-test  - Test release workflow (build + push-test)"
	@echo ""
	@echo "Development:"
	@echo "  install-dev   - Install development dependencies"
	@echo "  test          - Run tests (delegates to tests/Makefile)"
	@echo ""
	@echo "Utilities:"
	@echo "  clean         - Clean up build and distribution files"
	@echo "  check         - Check package integrity"
	@echo "  info          - Show package information"
	@echo "  help          - Show this help message"
	@echo ""
	@echo "For testing options, run: make -C tests help"

.PHONY: all build push push-test release release-test install-dev clean check info test help