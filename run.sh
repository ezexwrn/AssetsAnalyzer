#!/bin/sh
BASE="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$BASE/analyzer.py" "$@"