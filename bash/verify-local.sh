#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python --version
python -m compileall -q app/src app/tests
PYTHONPATH=app/src python -m unittest discover -s app/tests -v

if command -v ruff >/dev/null 2>&1; then
    ruff check app/src app/tests
else
    printf '%s\n' 'ruff is not installed; install it with: python -m pip install -r app/requirements-dev.txt' >&2
    exit 1
fi

printf '%s\n' 'Local verification passed.'
