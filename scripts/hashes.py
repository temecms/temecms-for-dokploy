#!/usr/bin/env python3
"""The list of every Dokploy compose file this project has released: compose-hashes.json.

Teme's updater reads the list before it replaces a site's compose file: it replaces the file only when its hash is in
`released`, and only with the file whose hash is `current`. A hash is made from the file's bytes, as Teme's
App\\Domain\\Updates\\Updater\\ComposeHash makes it:

  1. replace every CR LF (0x0D 0x0A) with LF (0x0A);
  2. remove trailing space, tab, LF, CR, NUL and vertical tab (0x20 0x09 0x0A 0x0D 0x00 0x0B) from the end;
  3. add one LF;
  4. SHA-256, written as 64 lowercase hex digits.

Test vector: the bytes `services:\r\n  web: {}\r\n\r\n` hash to
78ae680a3841176cc921326a7837fc012f1f21701a4f5a4d6943f9e6c20b8af8.

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
TRIMMED = b" \t\n\r\0\x0b"

# The bytes in and the hash out that this script and Teme's ComposeHash test both use.
TEST_VECTOR = (b"services:\r\n  web: {}\r\n\r\n", "78ae680a3841176cc921326a7837fc012f1f21701a4f5a4d6943f9e6c20b8af8")


def hash_of(data: bytes | str) -> str:
    """The hash Teme compares, of a compose file's bytes (a str is taken as UTF-8)."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    plain = raw.replace(b"\r\n", b"\n").rstrip(TRIMMED) + b"\n"
    return hashlib.sha256(plain).hexdigest()


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
    current = hash_of(blueprint.read_bytes())
    data = add(data, [current])
    data["current"] = current
    return data


def main(argv: list) -> int:
    if len(argv) >= 2 and argv[0] == "of":
        print(hash_of(Path(argv[1]).read_bytes()))
        return 0
    if len(argv) >= 2 and argv[0] == "add":
        write_list(add(read_list(), [hash_of(Path(name).read_bytes()) for name in argv[1:]]))
        return 0
    if argv == ["update"]:
        write_list(update(read_list()))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
