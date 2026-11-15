#!/bin/sh
# Sets a new pinned Teme release everywhere it appears, and prints what changed.
# Usage: scripts/bump.sh v0.8.0-alpha.1
# It touches only lines marked "teme-pin", and the "version" line of meta.json.
set -eu
# POSIX sh has no pipefail everywhere; turn it on where it exists.
# shellcheck disable=SC3040
(set -o pipefail) 2>/dev/null && set -o pipefail

[ $# -eq 1 ] || { echo "usage: $0 vX.Y.Z[-prerelease]" >&2; exit 2; }
tag=$1
printf '%s\n' "$tag" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z]+(\.[0-9A-Za-z]+)*)?$' \
  || { echo "refused: '$tag' is not an exact version like v0.7.0-alpha.1" >&2; exit 2; }
new=${tag#v}

root=$(cd "$(dirname "$0")/.." && pwd)
old=$(sed -n 's/^teme_tag = "\([^"]*\)".*/\1/p' "$root/template.toml")
[ -n "$old" ] || { echo "cannot find teme_tag in template.toml" >&2; exit 1; }
[ "$old" != "$new" ] || { echo "already pinned to $new; nothing to do"; exit 0; }

# Escape dots for sed.
old_re=$(printf '%s' "$old" | sed 's/\./\\./g')

for f in template.toml docker-compose.yml .env.example README.md; do
  tmp=$(mktemp)
  sed "/teme-pin/ s/$old_re/$new/g" "$root/$f" > "$tmp"
  if ! cmp -s "$tmp" "$root/$f"; then
    echo "changed $f:"
    diff "$root/$f" "$tmp" | grep '^[<>]' || true
    cat "$tmp" > "$root/$f"
  fi
  rm -f "$tmp"
done

tmp=$(mktemp)
sed "s/\"version\": \"$old_re\"/\"version\": \"$new\"/" "$root/meta.json" > "$tmp"
if ! cmp -s "$tmp" "$root/meta.json"; then
  echo "changed meta.json:"
  diff "$root/meta.json" "$tmp" | grep '^[<>]' || true
  cat "$tmp" > "$root/meta.json"
fi
rm -f "$tmp"

echo
echo "Pinned Teme $old -> $new."
echo "Next: scripts/sync-compose.sh <teme checkout> $tag, then scripts/check.sh,"
echo "add a CHANGELOG entry with its operator note, deploy to a test project."
