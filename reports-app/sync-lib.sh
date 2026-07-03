#!/usr/bin/env bash
#
# Resync the vendored copy of the `bloodwork` package from the library source
# at the repo root. This app is self-contained: it carries its own copy of
# `bloodwork/` so it can be deployed on its own (no `pip install -e ..`).
#
# Run this ONLY when you have changed the library source in ../bloodwork and
# want the app to pick up those changes. It is a one-way, deterministic mirror.
#
# Usage:  ./sync-lib.sh
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$(cd "$HERE/.." && pwd)/bloodwork/"
DST="$HERE/bloodwork/"

if [ ! -d "$SRC" ]; then
    echo "error: library source not found at $SRC" >&2
    echo "(this script only works inside the full repo, not a standalone deploy)" >&2
    exit 1
fi

echo "Syncing $SRC -> $DST"
rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' "$SRC" "$DST"
echo "Done. Review with: git status reports-app/bloodwork"
