# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim AS base

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

# Configure pip mirror based on geographic location
RUN pip config set global.index-url https://mirrors.cernet.edu.cn/pypi/web/simple;
    
# Install the package with server dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    # --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application using the installed console script
CMD ["toolregistry-server", "--host=0.0.0.0", "--port=8000", "--mode=openapi"]