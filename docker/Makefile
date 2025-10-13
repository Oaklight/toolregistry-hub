DOCKER_REPO = oaklight/toolregistry-hub-server
VERSION := $(shell cat ../pyproject.toml | grep '^version' | cut -d'"' -f2)

.PHONY: build push

build:
	docker build -f Dockerfile -t $(DOCKER_REPO):$(VERSION) -t $(DOCKER_REPO):latest ..

push:
	docker push $(DOCKER_REPO):$(VERSION)
	docker push $(DOCKER_REPO):latest