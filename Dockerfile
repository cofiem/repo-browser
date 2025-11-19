# syntax=docker/dockerfile:1@sha256:b6afd42430b15f2d2a4c5a02b919e98a525b785b1aaff16747d2f623364e39b6
FROM python:3.13.7-trixie@sha256:a7f3b1fe09b0845ef2e7b675ea3539062dc286bdc82d17da0caae58b03b67543 AS base

# Prevents Python from writing pyc files to reudce issues from pyc files not being updated.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /opt/repo-browser/src

ENV PIP_CACHE_DIR=/opt/repo-browser/.pip-cache
ENV PIP_TOOLS_CACHE_DIR=/opt/repo-browser/.pip-tools-cache

RUN --mount=type=cache,target=/opt/repo-browser/.pip-cache \
    --mount=type=cache,target=/opt/repo-browser/.pip-tools-cache \
    python -m pip --disable-pip-version-check install --root-user-action ignore --upgrade pip pip-tools


FROM base AS build_deps

# Build and install 'python-apt'.
# Check which version of debian this image is: https://hub.docker.com/_/python/
# Get the version of python-apt in that debian release: https://packages.debian.org/source/bookworm/python-apt
# Find the tag name in the git repo: https://salsa.debian.org/apt-team/python-apt/-/commits/main/?ref_type=HEADS
# See also: https://github.com/drakkar-lig/python-apt-binary/blob/main/scripts/build.sh

ENV DEBIAN_FRONTEND=noninteractive

# Update apt cache and install apt dependencies.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends \
      git \
      python3 \
      python3-dev \
      python3-venv

# Clone git repo.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    git clone https://salsa.debian.org/apt-team/python-apt.git /opt/python-apt

# checkout relevant tag or commit
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    cd /opt/python-apt  \
    && git checkout $(apt search python3-apt | grep 'python3-apt/' | awk '{print $2}') \
      || git checkout $(git log --oneline | grep -i "Release $(apt search python3-apt | grep 'python3-apt/' | awk '{print $2}')" | awk '{print $1}')

# Install the build requirements.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    cd /opt/python-apt \
    && apt-get build-dep -y --no-install-recommends ./

# Create virtualenv to build the package.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    cd /opt/python-apt \
    && mkdir /opt/python-apt-wheels \
    && python3 -m venv .venv \
    && .venv/bin/python -m pip install -U pip setuptools wheel

# Build the wheel
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    cd /opt/python-apt \
    && DEBVAR=$(apt search python3-apt | grep 'python3-apt/' | awk '{print $2}') \
      .venv/bin/python setup.py build

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    cd /opt/python-apt \
    && .venv/bin/python -m pip install -U build \
    && .venv/bin/python -m build --wheel \
    && .venv/bin/python -m wheel unpack --dest /tmp/python-apt /opt/python-apt/dist/python_apt*

FROM scratch AS export_deps

COPY --from=build_deps /opt/python-apt/dist /tmp/python-apt ./export_deps/

FROM base AS base_app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
ARG GID=10001
RUN addgroup \
    --gid "${GID}" \
    appgroup \
    && adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --comment "python app user" \
    --no-create-home \
    --uid "${UID}" \
    --gid "${GID}" \
    appuser

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/opt/repo-browser/.pip-cache \
    --mount=type=cache,target=/opt/repo-browser/.pip-tools-cache \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip-sync requirements.txt

# Copy the built python-apt wheel
COPY --from=build_deps /opt/python-apt/dist/python_apt* /tmp/
RUN --mount=type=cache,target=/opt/repo-browser/.pip-cache \
    --mount=type=cache,target=/opt/repo-browser/.pip-tools-cache \
    pip install --root-user-action ignore --no-cache-dir /tmp/python_apt*

# Switch to the non-privileged user to run the application.
USER appuser

FROM base_app AS dev_app

USER root

RUN --mount=type=cache,target=/opt/repo-browser/.pip-cache \
    --mount=type=cache,target=/opt/repo-browser/.pip-tools-cache \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    --mount=type=bind,source=dev-requirements.txt,target=dev-requirements.txt \
    pip-sync requirements.txt dev-requirements.txt

# Copy the source code into the container.
COPY --chown=appuser:appgroup . /opt/repo-browser/src/

USER appuser

# Run the application.
CMD ["manage.py", "runserver", "0.0.0.0:80"]

FROM base_app AS prod_app

USER root

# Copy the source code into the container.
COPY --chown=appuser:appgroup . /opt/repo-browser/src/

USER appuser

# Run the application.
CMD ["daphne", "examine.asgi:application", "-b=0.0.0.0", "-p=80"]
