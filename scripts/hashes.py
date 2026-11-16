#!/usr/bin/env python3
"""The list of every Dokploy compose file this project has released: compose-hashes.json.

Teme's updater reads the list before it replaces a site's compose file: it replaces the file only when its hash is in
`released`, and only with the file whose hash is `current`. A hash is SHA-256 of the file with Windows line endings
made plain, trailing whitespace removed and one newline added, as Teme's App\\Domain\\Updates\\Updater\\ComposeHash makes it.

  python3 scripts/hashes.py add FILE...   adds each file's hash to `released`
  python3 scripts/hashes.py update        sets `current` to the blueprint's hash, and adds it to `released`
  python3 scripts/hashes.py of FILE       prints a file's hash
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "compose-hashes.json"
BLUEPRINT = ROOT / "blueprints" / "teme" / "docker-compose.yml"

# PHP's rtrim() without a second argument: space, tab, newline, carriage return, NUL and vertical tab.
TRIMMED = " \t\n\r\0\x0b"


def hash_of(text: str) -> str:
    """The hash Teme compares, of a compose file's text."""
    plain = text.replace("\r\n", "\n").rstrip(TRIMMED) + "\n"
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def read_list(path: Path = LIST) -> dict:
    if not path.exists():
        return {"format": 1, "current": None, "released": []}
    return json.loads(path.read_text(encoding="utf-8"))


def write_list(data: dict, path: Path = LIST) -> None:
    path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8", newline="\n")


def add(data: dict, hashes: list) -> dict:
    """The list with each hash added to `released` once, in the order first seen; nothing is ever removed."""
    released = list(data.get("released", []))
    for found in hashes:
        if found not in released:
            released.append(found)
    return {"format": 1, "current": data.get("current"), "released": released}


def update(data: dict, blueprint: Path = BLUEPRINT) -> dict:
    current = hash_of(blueprint.read_text(encoding="utf-8"))
    data = add(data, [current])
    data["current"] = current
    return data


def main(argv: list) -> int:
    if len(argv) >= 2 and argv[0] == "of":
        print(hash_of(Path(argv[1]).read_text(encoding="utf-8")))
        return 0
    if len(argv) >= 2 and argv[0] == "add":
        write_list(add(read_list(), [hash_of(Path(name).read_text(encoding="utf-8")) for name in argv[1:]]))
        return 0
    if argv == ["update"]:
        write_list(update(read_list()))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
