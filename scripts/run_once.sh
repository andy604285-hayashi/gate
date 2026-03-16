#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/run_once.sh /path/to/project
# If no path is provided, current directory is used.

PROJECT_DIR="${1:-$(pwd)}"
cd "$PROJECT_DIR"

# Optional: activate virtual environment when present
if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python main.py --once --log-level INFO
