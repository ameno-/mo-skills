#!/usr/bin/env bash
set -euo pipefail

# webread.sh — fetch a URL and output readable plain text.
#
# Prefers:
#   lynx -dump
# Then:
#   w3m -dump
# Fallback:
#   raw curl
#
# Usage:
#   ./webread.sh https://example.com/

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <url>" >&2
  exit 2
fi

URL="$1"

if command -v lynx >/dev/null 2>&1; then
  lynx -dump -nolist -width=120 "$URL"
  exit 0
fi

if command -v w3m >/dev/null 2>&1; then
  w3m -dump -cols 120 "$URL"
  exit 0
fi

curl -fsSL "$URL"
