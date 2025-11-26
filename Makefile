# Makefile for toolregistry-hub package

# Variables
PACKAGE_NAME := toolregistry-hub
DIST_DIR := dist
DOCKER_IMAGE := oaklight/toolregistry-hub-server
VERSION := $(shell python -c "try:\n    import tomllib\nexcept ImportError:\n    import tomli as tomllib\nwith open('pyproject.toml', 'rb') as f:\n    print(tomllib.load(f)['project']['version'])" 2>/dev/null || echo "0.1.0")

# Optional variables
V ?= $(VERSION)
MIRROR ?=

# Build the Python package
build-package: clean-package
	@echo "Building $(PACKAGE_NAME) package..."
	python -m build
	@echo "Build complete. Distribution files are in $(DIST_DIR)/"

# Push the package to PyPI
push-package:
	@echo "Pushing $(PACKAGE_NAME) to PyPI..."
	twine upload $(DIST_DIR)/*
	@echo "Package pushed to PyPI."

# Clean up build and distribution files
clean-package:
	@echo "Cleaning up build and distribution files..."
	rm -rf $(DIST_DIR) *.egg-info build/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Cleanup complete."

# Build Docker image
build-docker:
	@echo "Building Docker image $(DOCKER_IMAGE):$(V)..."
	@# Check for local wheel file first
	@LOCAL_WHEEL=""; \
	BUILD_ARGS=""; \
	if [ -d "$(DIST_DIR)" ] && [ -n "$$(ls -A $(DIST_DIR)/*.whl 2>/dev/null)" ]; then \
		LOCAL_WHEEL=$$(ls $(DIST_DIR)/*.whl | head -n 1 | xargs basename); \
		echo "🎯 Found local wheel: $$LOCAL_WHEEL"; \
		BUILD_ARGS="--build-arg LOCAL_WHEEL=$$LOCAL_WHEEL"; \
	else \
		echo "📦 No local wheel found, will install from PyPI"; \
		BUILD_ARGS="--build-arg PACKAGE_VERSION=$(V)"; \
	fi; \
	if [ -n "$(MIRROR)" ]; then \
		echo "🌐 Using PyPI mirror: $(MIRROR)"; \
		BUILD_ARGS="$$BUILD_ARGS --build-arg PYPI_MIRROR=$(MIRROR)"; \
	fi; \
	echo "🐳 Building with args: $$BUILD_ARGS"; \
	cd docker && docker build -f Dockerfile $$BUILD_ARGS -t $(DOCKER_IMAGE):$(V) -t $(DOCKER_IMAGE):latest ..
	@echo "✅ Docker image built successfully."

# Push Docker image to registry
push-docker:
	@echo "Pushing Docker image $(DOCKER_IMAGE):$(V) and $(DOCKER_IMAGE):latest..."
	docker push $(DOCKER_IMAGE):$(V)
	docker push $(DOCKER_IMAGE):latest
	@echo "Docker images pushed successfully."

# Clean Docker images and containers
clean-docker:
	@echo "Cleaning Docker images and containers..."
	docker rmi $(DOCKER_IMAGE):latest 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(V) 2>/dev/null || true
	docker system prune -f

# Run tests (delegates to tests/Makefile)
test:
	@echo "Running tests..."
	$(MAKE) -C tests test
	@echo "Tests completed."

# Help target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Package targets:"
	@echo "  build-package  - Build the Python package"
	@echo "  push-package   - Push the package to PyPI"
	@echo "  clean-package  - Clean up build and distribution files"
	@echo ""
	@echo "Docker targets:"
	@echo "  build-docker   - Build Docker image"
	@echo "  push-docker    - Push Docker image to registry"
	@echo "  clean-docker   - Clean Docker images and containers"
	@echo ""
	@echo "Development:"
	@echo "  test           - Run tests (delegates to tests/Makefile)"
	@echo ""
	@echo "Usage examples:"
	@echo "  make build-docker                                       # Build with auto-detected version"
	@echo "  make build-docker V=1.0.0                              # Build with specific version"
	@echo "  make build-docker MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple"
	@echo "  make build-docker V=1.0.0 MIRROR=https://mirrors.cernet.edu.cn/pypi/web/simple"
	@echo ""
	@echo "Variables:"
	@echo "  V=<version>    - Specify version (default: auto-detected)"
	@echo "  MIRROR=<url>   - Specify PyPI mirror URL"

.PHONY: build-package push-package clean-package build-docker push-docker clean-docker test help