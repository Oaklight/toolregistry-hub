# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim AS base

# Accept PyPI mirror as optional build argument
ARG PYPI_MIRROR
# Accept local wheel file path as build argument
ARG LOCAL_WHEEL
# Accept package version as build argument
ARG PACKAGE_VERSION

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    # --home "/nonexistent" \
    # --shell "/sbin/nologin" \
    # --no-create-home \
    --uid "${UID}" \
    appuser

# Create temporary directory for potential local wheels
RUN mkdir -p /tmp/dist/

# Copy the entire project context and extract dist if it exists
COPY . /tmp/build/
RUN if [ -d "/tmp/build/dist" ] && [ "$(ls -A /tmp/build/dist 2>/dev/null)" ]; then \
        cp /tmp/build/dist/*.whl /tmp/dist/ 2>/dev/null || true; \
    fi

# Configure pip mirror based on geographic location
# RUN pip config set global.index-url https://mirrors.cernet.edu.cn/pypi/web/simple;

# Install the package with server extras - prioritize local wheel + deps, then specific version from PyPI, then latest
RUN if [ -n "$LOCAL_WHEEL" ] && [ -f "/tmp/dist/$LOCAL_WHEEL" ]; then \
        echo "Installing from local wheel: $LOCAL_WHEEL + server deps"; \
        if [ -n "$PYPI_MIRROR" ]; then \
            pip install -i "$PYPI_MIRROR" --no-cache-dir "/tmp/dist/$LOCAL_WHEEL" "fastapi>=0.119.0" "uvicorn[standard]>=0.24.0" "fastmcp>=2.12.4"; \
        else \
            pip install --no-cache-dir "/tmp/dist/$LOCAL_WHEEL" "fastapi>=0.119.0" "uvicorn[standard]>=0.24.0" "fastmcp>=2.12.4"; \
        fi; \
    elif [ -n "$PACKAGE_VERSION" ]; then \
        echo "Installing toolregistry-hub[server] version: $PACKAGE_VERSION"; \
        if [ -n "$PYPI_MIRROR" ]; then \
            pip install -i "$PYPI_MIRROR" --no-cache-dir "toolregistry-hub[server]==$PACKAGE_VERSION"; \
        else \
            pip install --no-cache-dir "toolregistry-hub[server]==$PACKAGE_VERSION"; \
        fi; \
    else \
        echo "Installing latest toolregistry-hub[server] from PyPI"; \
        if [ -n "$PYPI_MIRROR" ]; then \
            pip install -i "$PYPI_MIRROR" --no-cache-dir "toolregistry-hub[server]"; \
        else \
            pip install --no-cache-dir "toolregistry-hub[server]"; \
        fi; \
    fi && \
    rm -rf /tmp/dist/ /tmp/build/

# Switch to the non-privileged user to run the application.
USER appuser

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application using the installed console script
CMD ["toolregistry-server", "--host=0.0.0.0", "--port=8000", "--mode=openapi"]