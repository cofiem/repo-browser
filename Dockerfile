# syntax=docker/dockerfile:1

# Build and install 'python-apt'.
# Check which version of debian this image is: https://hub.docker.com/_/python/
# Get the version of python-apt in that debian release: https://packages.debian.org/source/bookworm/python-apt
# Find the tag name in the git repo: https://salsa.debian.org/apt-team/python-apt/-/commits/main/?ref_type=HEADS
# See also: https://github.com/drakkar-lig/python-apt-binary/blob/main/scripts/build.sh

FROM debian:bookworm AS build

# Update apt cache and install apt dependencies.
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
      git \
      python3 \
      python3-dev \
      python3-venv

# Clone git repo and checkout relevant tag or commit.
RUN git clone https://salsa.debian.org/apt-team/python-apt.git /opt/python-apt \
    && cd /opt/python-apt \
    && git checkout $(apt search python3-apt | grep 'python3-apt/' | awk '{print $2}') \
      || git checkout $(git log --oneline | grep -i "Release $(apt search python3-apt | grep 'python3-apt/' | awk '{print $2}')" | awk '{print $1}')

# Install the build requirements.
RUN cd /opt/python-apt \
    && DEBIAN_FRONTEND=noninteractive apt build-dep -y --no-install-recommends ./

# Create virtualenv to build the package.
RUN cd /opt/python-apt \
    && mkdir /opt/python-apt-wheels \
    && python3 -m venv .venv \
    && .venv/bin/python -m pip install -U pip

# Build the wheel
RUN cd /opt/python-apt \
    && DEBVAR=$(apt search python3-apt | grep 'python3-apt/' | awk '{print $2}') \
      .venv/bin/python setup.py build

RUN cd /opt/python-apt \
    && .venv/bin/python -m pip install -U build \
    && .venv/bin/python -m build --wheel

FROM python:3.11 AS run

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY --from=build /opt/python-apt/dist/python_apt* /tmp/
RUN pip install --no-cache-dir -r requirements.txt /tmp/python_apt*

COPY . .

EXPOSE 8001

CMD ["python", "-m", "daphne", "-b", "0.0.0.0", "-p", "8001", "examine.asgi:application"]
