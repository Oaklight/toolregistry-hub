DOCKER_REPO = oaklight/toolregistry-hub-server
VERSION := $(shell cat ../pyproject.toml | grep '^version' | cut -d'"' -f2)

# Optional variables
MIRROR ?=

.PHONY: build push help

build:
	@echo "Building Docker image $(DOCKER_REPO):$(VERSION)..."
	@if [ -n "$(MIRROR)" ]; then \
		echo "Using PyPI mirror: $(MIRROR)"; \
		docker build -f Dockerfile --build-arg PYPI_MIRROR=$(MIRROR) -t $(DOCKER_REPO):$(VERSION) -t $(DOCKER_REPO):latest ..; \
	else \
		docker build -f Dockerfile -t $(DOCKER_REPO):$(VERSION) -t $(DOCKER_REPO):latest ..; \
	fi
	@echo "Docker image built successfully."

push:
	@echo "Pushing Docker images $(DOCKER_REPO):$(VERSION) and $(DOCKER_REPO):latest..."
	docker push $(DOCKER_REPO):$(VERSION)
	docker push $(DOCKER_REPO):latest
	@echo "Docker images pushed successfully."

help:
	@echo "Available targets:"
	@echo ""
	@echo "  build  - Build Docker image"
	@echo "  push   - Push Docker image to registry"
	@echo "  help   - Show this help message"
	@echo ""
	@echo "Usage examples:"
	@echo "  make build                                              # Build with default PyPI"
	@echo "  make build MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple"
	@echo "  make build MIRROR=https://mirrors.cernet.edu.cn/pypi/web/simple"
	@echo ""
	@echo "Variables:"
	@echo "  MIRROR=<url>   - Specify PyPI mirror URL"