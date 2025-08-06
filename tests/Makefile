# Makefile for testing toolregistry-hub

# Default target
all: test

# Test targets
test:
	@echo "Running all tests..."
	python run_tests.py
	@echo "All tests completed."

test-unit:
	@echo "Running unit tests..."
	python run_tests.py --unit
	@echo "Unit tests completed."

test-integration:
	@echo "Running integration tests..."
	python run_tests.py --integration
	@echo "Integration tests completed."

test-fast:
	@echo "Running fast tests..."
	python run_tests.py --fast
	@echo "Fast tests completed."

test-coverage:
	@echo "Running tests with coverage..."
	python run_tests.py --coverage
	@echo "Coverage tests completed."

test-verbose:
	@echo "Running tests in verbose mode..."
	python run_tests.py --verbose
	@echo "Verbose tests completed."

# Module-specific test targets
test-calculator:
	@echo "Running calculator tests..."
	python run_tests.py --module calculator
	@echo "Calculator tests completed."

test-fileops:
	@echo "Running file operations tests..."
	python run_tests.py --module fileops
	@echo "File operations tests completed."

test-filesystem:
	@echo "Running filesystem tests..."
	python run_tests.py --module filesystem
	@echo "Filesystem tests completed."

test-unitconverter:
	@echo "Running unit converter tests..."
	python run_tests.py --module unitconverter
	@echo "Unit converter tests completed."

test-utils:
	@echo "Running utils tests..."
	python run_tests.py --module utils
	@echo "Utils tests completed."

test-websearch:
	@echo "Running websearch tests..."
	python run_tests.py --module websearch
	@echo "Websearch tests completed."

test-websearch-google:
	@echo "Running Google websearch tests..."
	python run_tests.py --module websearch-google
	@echo "Google websearch tests completed."

test-websearch-bing:
	@echo "Running Bing websearch tests..."
	python run_tests.py --module websearch-bing
	@echo "Bing websearch tests completed."

test-websearch-searxng:
	@echo "Running SearXNG websearch tests..."
	python run_tests.py --module websearch-searxng
	@echo "SearXNG websearch tests completed."

# Code quality targets
lint:
	@echo "Running code linting..."
	python run_tests.py --lint
	@echo "Linting completed."

format:
	@echo "Formatting code..."
	python run_tests.py --format
	@echo "Code formatting completed."

# Setup targets
install-deps:
	@echo "Installing test dependencies..."
	python run_tests.py --install-deps
	@echo "Dependencies installed."

# Cleanup targets
clean:
	@echo "Cleaning up test artifacts..."
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Test cleanup complete."

# Help target
help:
	@echo "Available test targets:"
	@echo ""
	@echo "General testing:"
	@echo "  test              - Run all tests"
	@echo "  test-unit         - Run unit tests only"
	@echo "  test-integration  - Run integration tests only"
	@echo "  test-fast         - Run fast tests (exclude slow ones)"
	@echo "  test-coverage     - Run tests with coverage report"
	@echo "  test-verbose      - Run tests in verbose mode"
	@echo ""
	@echo "Module-specific tests:"
	@echo "  test-calculator   - Run calculator tests"
	@echo "  test-fileops      - Run file operations tests"
	@echo "  test-filesystem   - Run filesystem tests"
	@echo "  test-unitconverter - Run unit converter tests"
	@echo "  test-utils        - Run utils tests"
	@echo "  test-websearch    - Run all websearch tests"
	@echo "  test-websearch-google  - Run Google websearch tests"
	@echo "  test-websearch-bing    - Run Bing websearch tests"
	@echo "  test-websearch-searxng - Run SearXNG websearch tests"
	@echo ""
	@echo "Code quality:"
	@echo "  lint              - Run code linting"
	@echo "  format            - Format code"
	@echo ""
	@echo "Setup and cleanup:"
	@echo "  install-deps      - Install test dependencies"
	@echo "  clean             - Clean up test artifacts"
	@echo "  help              - Show this help message"

.PHONY: all test test-unit test-integration test-fast test-coverage test-verbose \
        test-calculator test-fileops test-filesystem test-unitconverter test-utils \
        test-websearch test-websearch-google test-websearch-bing test-websearch-searxng \
        lint format install-deps clean help