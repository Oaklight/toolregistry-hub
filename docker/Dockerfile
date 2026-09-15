# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10
ARG REGISTRY_MIRROR
FROM ${REGISTRY_MIRROR:-docker.io}/python:${PYTHON_VERSION}-slim AS base

# PyPI configuration
ARG PYPI_MIRROR
ARG EXTRA_INDEX_URL
# Install source: local wheel or PyPI
ARG LOCAL_WHEEL
ARG PACKAGE_VERSION

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --uid "${UID}" \
    appuser

RUN mkdir -p /tmp/dist/

# Copy only dist/ for local wheels (never COPY the full tree).
COPY dist/ /tmp/dist/

# Build pip flags from optional build args
RUN PIP_FLAGS="--no-cache-dir"; \
    if [ -n "$PYPI_MIRROR" ]; then \
        PIP_FLAGS="$PIP_FLAGS -i $PYPI_MIRROR"; \
    fi; \
    if [ -n "$EXTRA_INDEX_URL" ]; then \
        PIP_FLAGS="$PIP_FLAGS --extra-index-url $EXTRA_INDEX_URL"; \
    fi; \
    if [ -n "$LOCAL_WHEEL" ] && [ -f "/tmp/dist/$LOCAL_WHEEL" ]; then \
        echo "Installing from local wheel: $LOCAL_WHEEL[server]"; \
        pip install $PIP_FLAGS "/tmp/dist/${LOCAL_WHEEL}[server]"; \
    elif [ -n "$PACKAGE_VERSION" ]; then \
        echo "Installing toolregistry-hub[server]==$PACKAGE_VERSION"; \
        pip install $PIP_FLAGS "toolregistry-hub[server]==$PACKAGE_VERSION"; \
    else \
        echo "Installing latest toolregistry-hub[server] from PyPI"; \
        pip install $PIP_FLAGS "toolregistry-hub[server]"; \
    fi && \
    rm -rf /tmp/dist/

USER appuser

EXPOSE 8000
EXPOSE 8001

CMD ["toolregistry-hub", "openapi", "--host=0.0.0.0", "--port=8000", "--admin-port=8001"]
