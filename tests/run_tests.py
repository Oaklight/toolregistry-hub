#!/usr/bin/env python3
"""Test runner script for toolregistry-hub project.

This script provides convenient ways to run different types of tests
with various configurations and reporting options.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"\n🔄 {description}")

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description or 'Command'} completed successfully")
        return True


def run_all_tests(verbose=False, coverage=False):
    """Run all tests."""
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(
            ["--cov=../src/toolregistry_hub", "--cov-report=html", "--cov-report=term-missing"]
        )

    return run_command(cmd, "Running all tests")


def run_unit_tests(verbose=False):
    """Run only unit tests."""
    cmd = ["python", "-m", "pytest", "-m", "unit"]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run only integration tests."""
    cmd = ["python", "-m", "pytest", "-m", "integration"]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, "Running integration tests")


def run_specific_module_tests(module, verbose=False):
    """Run tests for a specific module."""
    module_map = {
        "calculator": "test_calculator.py",
        "fileops": "test_file_ops.py",
        "filesystem": "test_filesystem.py",
        "unitconverter": "test_unit_converter.py",
        "utils": "test_utils.py",
        "websearch": "websearch/",
        "websearch-google": "websearch/test_websearch_google.py",
        "websearch-bing": "websearch/test_websearch_bing.py",
        "websearch-searxng": "websearch/test_websearch_searxng.py",
    }

    if module not in module_map:
        print(f"❌ Unknown module: {module}")
        print(f"Available modules: {', '.join(module_map.keys())}")
        return False

    test_path = module_map[module]
    cmd = ["python", "-m", "pytest", test_path]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, f"Running tests for {module}")


def run_fast_tests(verbose=False):
    """Run fast tests (excluding slow ones)."""
    cmd = ["python", "-m", "pytest", "-m", "not slow"]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, "Running fast tests")


def run_with_coverage():
    """Run tests with coverage report."""
    return run_all_tests(coverage=True)


def lint_code():
    """Run code linting."""
    commands = [
        (["python", "-m", "flake8", "../src/", "."], "Running flake8 linting"),
        (
            ["python", "-m", "black", "--check", "../src/", "."],
            "Checking code formatting with black",
        ),
        (
            ["python", "-m", "isort", "--check-only", "../src/", "."],
            "Checking import sorting with isort",
        ),
    ]

    all_passed = True
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False

    return all_passed


def format_code():
    """Format code using black and isort."""
    commands = [
        (["python", "-m", "black", "../src/", "."], "Formatting code with black"),
        (["python", "-m", "isort", "../src/", "."], "Sorting imports with isort"),
    ]

    all_passed = True
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False

    return all_passed


def install_test_dependencies():
    """Install test dependencies."""
    dependencies = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "black>=22.0.0",
        "flake8>=5.0.0",
        "isort>=5.10.0",
    ]

    cmd = ["python", "-m", "pip", "install"] + dependencies
    return run_command(cmd, "Installing test dependencies")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test runner for toolregistry-hub project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                          # Run all tests
  python run_tests.py --module calculator     # Run calculator tests only
  python run_tests.py --coverage              # Run tests with coverage
  python run_tests.py --fast                  # Run fast tests only
  python run_tests.py --lint                  # Run code linting
  python run_tests.py --format                # Format code
  python run_tests.py --install-deps          # Install test dependencies
        """,
    )

    parser.add_argument(
        "--module",
        "-m",
        help="Run tests for specific module",
        choices=[
            "calculator",
            "fileops",
            "filesystem",
            "unitconverter",
            "utils",
            "websearch",
            "websearch-google",
            "websearch-bing",
            "websearch-searxng",
        ],
    )

    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run tests with coverage report"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Run tests in verbose mode"
    )

    parser.add_argument(
        "--fast",
        "-f",
        action="store_true",
        help="Run fast tests only (exclude slow tests)",
    )

    parser.add_argument("--unit", action="store_true", help="Run unit tests only")

    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )

    parser.add_argument("--lint", action="store_true", help="Run code linting")

    parser.add_argument(
        "--format", action="store_true", help="Format code using black and isort"
    )

    parser.add_argument(
        "--install-deps", action="store_true", help="Install test dependencies"
    )

    args = parser.parse_args()

    # Check if we're in the right directory (now running from tests directory)
    if not Path("../src/toolregistry_hub").exists():
        print("❌ Error: This script should be run from the tests directory")
        print("   Make sure you're in the tests directory of the project")
        sys.exit(1)

    success = True

    if args.install_deps:
        success = install_test_dependencies()
    elif args.lint:
        success = lint_code()
    elif args.format:
        success = format_code()
    elif args.module:
        success = run_specific_module_tests(args.module, args.verbose)
    elif args.coverage:
        success = run_with_coverage()
    elif args.fast:
        success = run_fast_tests(args.verbose)
    elif args.unit:
        success = run_unit_tests(args.verbose)
    elif args.integration:
        success = run_integration_tests(args.verbose)
    else:
        success = run_all_tests(args.verbose)

    if success:
        print("\n🎉 All operations completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some operations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
