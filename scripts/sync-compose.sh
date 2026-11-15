#!/bin/sh
# Shows how this project's docker-compose.yml differs from Teme's
# docker/compose.dokploy.yml at a tag. Read-only: it only runs "git show"
# in the Teme checkout and diff; it changes nothing.
# Usage: scripts/sync-compose.sh /path/to/teme-checkout v0.7.0-alpha.1
# Expect differences only on lines marked "TemeCMS:" (and the header).
set -eu

[ $# -eq 2 ] || { echo "usage: $0 <teme-checkout> <tag>" >&2; exit 2; }
repo=$1
tag=$2
root=$(cd "$(dirname "$0")/.." && pwd)

git -C "$repo" rev-parse --git-dir >/dev/null 2>&1 || { echo "not a git checkout: $repo" >&2; exit 1; }
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
git -C "$repo" show "$tag:docker/compose.dokploy.yml" > "$tmp" \
  || { echo "cannot read docker/compose.dokploy.yml at $tag (git fetch --tags?)" >&2; exit 1; }

echo "--- Teme $tag docker/compose.dokploy.yml"
echo "+++ $root/docker-compose.yml"
diff -u "$tmp" "$root/docker-compose.yml" || true
echo
echo "Read every changed line. A line Teme changed that has no 'TemeCMS:' note"
echo "here is a change to bring over by hand."
