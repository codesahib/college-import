#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  echo "Create the virtualenv and install backend/requirements.txt first (see README)." >&2
  exit 1
fi
.venv/bin/python scripts/reset.py "$@"
