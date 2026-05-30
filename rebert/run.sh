#!/usr/bin/env bash
# Run any Rebert prototype from repo root.
# Usage: ./rebert/run.sh <version> [port]
# Examples:
#   ./rebert/run.sh 5.0
#   ./rebert/run.sh 7.1 5000
#   REBERT_EXPLANATION_MODE=modified ./rebert/run.sh 7.1 5001

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${1:?Usage: ./rebert/run.sh <version> [port]  e.g. 7.1 or 5.0}"
PORT="${2:-5000}"

case "$VERSION" in
  2.0) DIR="_prototype_2_" ; ENTRY="recommender_2.0.py" ;;
  3.0) DIR="_prototype_3_" ; ENTRY="recommender_3.0.py" ;;
  4.0) DIR="_prototype_4_" ; ENTRY="recommender_4.0.py" ;;
  5.0) DIR="_prototype_5_" ; ENTRY="recommender_5.0.py" ;;
  6.0) DIR="_prototype_6_" ; ENTRY="recommender_6.0.py" ;;
  7.0) DIR="_prototype_7_" ; ENTRY="recommender_7.0.py" ;;
  7.1) DIR="_prototype_7_1_" ; ENTRY="recommender_7.1.py" ;;
  *)
    echo "Unknown prototype version: $VERSION"
    echo "Supported: 2.0 3.0 4.0 5.0 6.0 7.0 7.1"
    exit 1
    ;;
esac

if [[ -d "$ROOT/.venv/bin" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

export PYTHONPATH="$ROOT"
cd "$ROOT/rebert/$DIR"

echo "Running Rebert p$VERSION from rebert/$DIR on http://127.0.0.1:$PORT"
python "$ENTRY" -port "$PORT"
