.PHONY: test test-all test-unit test-integration test-fast test-coverage test-verbose clean install-deps lint format help

# Default target
help:
	@echo "Available targets:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-fast      - Run fast tests (exclude slow ones)"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  test-verbose   - Run tests in verbose mode"
	@echo "  test-calculator - Run calculator tests"
	@echo "  test-fileops   - Run file operations tests"
	@echo "  test-filesystem - Run filesystem tests"
	@echo "  test-unitconverter - Run unit converter tests"
	@echo "  test-utils     - Run utils tests"
	@echo "  test-websearch - Run websearch tests"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code"
	@echo "  install-deps   - Install test dependencies"
	@echo "  clean          - Clean test artifacts"

# Test targets
test:
	python run_tests.py

test-all: test

test-unit:
	python run_tests.py --unit

test-integration:
	python run_tests.py --integration

test-fast:
	python run_tests.py --fast

test-coverage:
	python run_tests.py --coverage

test-verbose:
	python run_tests.py --verbose

# Module-specific tests
test-calculator:
	python run_tests.py --module calculator

test-fileops:
	python run_tests.py --module fileops

test-filesystem:
	python run_tests.py --module filesystem

test-unitconverter:
	python run_tests.py --module unitconverter

test-utils:
	python run_tests.py --module utils

test-websearch:
	python run_tests.py --module websearch

test-websearch-google:
	python run_tests.py --module websearch-google

test-websearch-bing:
	python run_tests.py --module websearch-bing

test-websearch-searxng:
	python run_tests.py --module websearch-searxng

# Code quality targets
lint:
	python run_tests.py --lint

format:
	python run_tests.py --format

# Setup targets
install-deps:
	python run_tests.py --install-deps

# Cleanup targets
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete