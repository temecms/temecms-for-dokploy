#!/bin/sh
# Checks that need no server. Exits 1 if any check fails.
# Usage: scripts/check.sh
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
fail=0
bad() { echo "FAIL: $*" >&2; fail=1; }

# 1. The compose file parses (placeholder values only, to satisfy interpolation).
if command -v docker >/dev/null 2>&1; then
  if TEME_IMAGE=x TEME_UPDATER_IMAGE=x APP_URL=x APP_KEY=x DB_PASSWORD=x POSTGRES_PASSWORD=x \
     docker compose -f docker-compose.yml config >/dev/null 2>&1; then
    echo "ok: docker compose config parses"
  else
    bad "docker compose config fails"
  fi
else
  echo "note: docker is not installed; the compose file was not parsed"
fi

# 2. Every variable used in the compose file is defined in template.toml or .env.example.
vars=$(grep -o '\${[A-Z][A-Z0-9_]*' docker-compose.yml | sed 's/^\${//' | sort -u)
for v in $vars; do
  if grep -Eq "\"$v=" template.toml || grep -Eq "^#? ?$v=" .env.example; then :; else
    bad "$v is used in docker-compose.yml but defined in neither template.toml nor .env.example"
  fi
done
echo "ok: variable check done ($(echo "$vars" | wc -w | tr -d ' ') variables)"

# 3. The pinned tag is the same everywhere (lines marked teme-pin, and meta.json).
pin=$(sed -n 's/^teme_tag = "\([^"]*\)".*/\1/p' template.toml)
[ -n "$pin" ] || bad "no teme_tag in template.toml"
case "$pin" in *latest*) bad "pinned tag is a floating tag" ;; esac
for f in template.toml docker-compose.yml .env.example README.md; do
  for found in $(grep 'teme-pin' "$f" | grep -Eo 'v?[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.]+)?' | sed 's/^v//'); do
    [ "$found" = "$pin" ] || bad "$f has $found, template.toml pins $pin"
  done
done
meta=$(sed -n 's/.*"version": "\([^"]*\)".*/\1/p' meta.json)
[ "$meta" = "$pin" ] || bad "meta.json says $meta, template.toml pins $pin"
if grep -Eq ':latest' docker-compose.yml template.toml; then bad "a :latest tag appears"; fi
echo "ok: pinned tag $pin"

# 4. No value that looks like a real credential.
pattern='(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|base64:[A-Za-z0-9+/]{43}=)'
if grep -rEn "$pattern" --exclude-dir=.git --exclude=check.sh . ; then
  bad "something looks like a real secret (above)"
else
  echo "ok: no secret-looking values"
fi
if grep -En '^(APP_KEY|DB_PASSWORD|POSTGRES_PASSWORD|TEME_DOKPLOY_TOKEN|TEME_GITHUB_TOKEN)=.+' .env.example; then
  bad ".env.example gives a value to a secret"
fi

if [ "$fail" -eq 0 ]; then echo "all checks passed"; else echo "checks failed" >&2; exit 1; fi
