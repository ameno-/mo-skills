#!/usr/bin/env bash
set -euo pipefail

# websearch.sh — basic web search without paid APIs.
#
# Prefers:
#   ddgr (DuckDuckGo CLI)
# Falls back to:
#   ddg_search.py (minimal DuckDuckGo HTML scraper)
#
# Usage:
#   ./websearch.sh "query" [n]
#   ./websearch.sh "query" [n] --json

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"query\" [n] [--json]" >&2
  exit 2
fi

QUERY="$1"
N="${2:-5}"
MODE="${3:-}"

if command -v ddgr >/dev/null 2>&1; then
  if [[ "$MODE" == "--json" ]]; then
    ddgr --json -n "$N" "$QUERY"
  else
    ddgr -n "$N" "$QUERY"
  fi
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FALLBACK="$SCRIPT_DIR/ddg_search.py"

if [[ ! -f "$FALLBACK" ]]; then
  echo "ddgr is not installed and fallback is missing: $FALLBACK" >&2
  exit 1
fi

if [[ "$MODE" == "--json" ]]; then
  python3 "$FALLBACK" "$QUERY" -n "$N" --json
else
  python3 "$FALLBACK" "$QUERY" -n "$N"
fi
