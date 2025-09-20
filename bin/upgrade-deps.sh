#!/usr/bin/env bash

set -o nounset # -u
set -o errexit # -e
set -o xtrace # -x
set -o pipefail

pip-compile --generate-hashes --strip-extras --allow-unsafe --upgrade --output-file requirements.txt requirements.in
pip-compile --generate-hashes --strip-extras --allow-unsafe --upgrade --output-file dev-requirements.txt dev-requirements.in
