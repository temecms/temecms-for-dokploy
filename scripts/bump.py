#!/usr/bin/env python3
"""Sets the Teme release the template installs: `teme_version` in template.toml, the two image lines of the README's
block for the Environment tab and the "Installs Teme X." at the end of meta.json's description; and makes a new
patch version of the template (meta.json's `version`), with "Installs Teme X." under its own heading in CHANGELOG.md.

A template that installs a newer release already is left as it is, so a patch to an older line never moves it back.
Nothing else in either file changes.

  python3 scripts/bump.py 0.9.0
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Teme's own pattern for a release's version: never "latest", never a "v".
VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-(alpha|beta|rc)\.(0|[1-9]\d*))?\Z")
STAGES = {"alpha": 0, "beta": 1, "rc": 2}


def key(version: str) -> tuple:
    """Orders versions as Teme does: 1.0.0-alpha.1 < 1.0.0-beta.1 < 1.0.0-rc.1 < 1.0.0."""
    found = VERSION.match(version)
    if found is None:
        raise ValueError(f"{version} isn’t a release’s version.")
    major, minor, patch = (int(found.group(i)) for i in (1, 2, 3))
    if found.group(5) is None:
        return (major, minor, patch, 3, 0)
    return (major, minor, patch, STAGES[found.group(5)], int(found.group(6)))


def bump(version: str, root: Path = ROOT, today: str | None = None) -> str:
    today = today or date.today().isoformat()
    """Rewrites both files for the version, and says what happened."""
    key(version)
    meta_file = root / "meta.json"
    toml_file = root / "blueprints" / "teme" / "template.toml"
    meta = meta_file.read_text(encoding="utf-8")
    toml = toml_file.read_text(encoding="utf-8")

    entries = json.loads(meta)
    meta_lines = re.findall(r'^\s*"version": "[^"]*",$', meta, re.M)
    toml_lines = re.findall(r'^teme_version = "[^"]*"$', toml, re.M)
    installs = re.findall(r' Installs Teme [^"]*\.",$', meta, re.M)
    if not isinstance(entries, list) or len(entries) != 1 or len(meta_lines) != 1 or len(toml_lines) != 1 or len(installs) != 1:
        raise RuntimeError("The template doesn’t hold its versions once in each file; nothing was changed.")

    was = re.search(r'^teme_version = "([^"]*)"$', toml, re.M).group(1)
    if key(was) >= key(version):
        return f"The template installs {was} already; nothing was changed."

    major, minor, patch = (int(part) for part in str(entries[0]["version"]).split("."))
    template_version = f"{major}.{minor}.{patch + 1}"
    meta = re.sub(r'^(\s*"version": ")[^"]*(",)$', rf"\g<1>{template_version}\g<2>", meta, count=1, flags=re.M)
    meta = re.sub(r' Installs Teme [^"]*\.(",)$', rf" Installs Teme {version}.\g<1>", meta, count=1, flags=re.M)
    meta_file.write_text(meta, encoding="utf-8", newline="\n")
    toml_file.write_text(re.sub(r'^(teme_version = ")[^"]*(")$', rf"\g<1>{version}\g<2>", toml, count=1, flags=re.M), encoding="utf-8", newline="\n")

    # The README's block for the Environment tab names the same release.
    readme_file = root / "README.md"
    if readme_file.exists():
        readme = readme_file.read_text(encoding="utf-8")
        readme = re.sub(r"^(\s*TEME_(?:UPDATER_)?IMAGE=ghcr\.io/temecms/teme:)\S+$", rf"\g<1>{version}", readme, flags=re.M)
        readme_file.write_text(readme, encoding="utf-8", newline="\n")

    # And the changelog says so, under the new version's own heading, newest first.
    changelog_file = root / "CHANGELOG.md"
    if changelog_file.exists():
        changelog = changelog_file.read_text(encoding="utf-8")
        entry = f"## {template_version} — {today}\n\n- Installs Teme {version}.\n\n"
        first = changelog.find("\n## ")
        changelog = changelog[: first + 1] + entry + changelog[first + 1:] if first != -1 else changelog.rstrip("\n") + "\n\n" + entry
        changelog_file.write_text(changelog, encoding="utf-8", newline="\n")

    return f"The template installs {version} now."


def main(argv: list) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        print(bump(argv[0]))
    except ValueError as refused:
        print(refused, file=sys.stderr)
        return 2
    except RuntimeError as refused:
        print(refused, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
