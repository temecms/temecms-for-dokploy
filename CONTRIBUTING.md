# Contributing

## What this repository holds

| File | What it is |
|---|---|
| `meta.json` | The template list Dokploy reads at the Base URL. |
| `blueprints/teme/docker-compose.yml` | The compose file, for the template, Raw and Git alike. |
| `blueprints/teme/template.toml` | The settings the template fills, and the domain. |
| `blueprints/teme/teme.svg` | Teme's icon in the list. |
| `compose-hashes.json` | Every compose file this repository and Teme have released, by SHA-256. Teme's updater replaces a site's compose file only when its hash is listed. |
| `scripts/check.py` | Checks the template before it is published. |
| `scripts/bump.py` | Sets the Teme release the template installs. |
| `scripts/hashes.py` | Keeps `compose-hashes.json`. |

## Changing the compose file

A site made from the template keeps the compose file it was made with. Teme's updater brings it the new one at the site's next update, but only when the site's file is listed in `compose-hashes.json`. So every change to `blueprints/teme/docker-compose.yml` comes with the list updated:

1. Change the file.
2. Run `python3 scripts/hashes.py update`. It names the new file as `current` and adds it to `released`. Nothing is ever removed from `released`: a site may still run any file listed there.
3. Run the checks:

   ```sh
   python3 -m unittest discover -s tests
   python3 scripts/check.py
   ```

4. Add a line to `CHANGELOG.md` under **Unreleased**, and say that the compose file changed.

The checks need Python 3.11 or later and Docker Compose 2.24 or later. The **check** workflow runs them on every pull request, with `main`'s list, so a change that drops a listed file fails.

## Moving the template to a new Teme release

The **follow-teme** workflow does this each day. By hand: `python3 scripts/bump.py 0.9.0` sets the release in `meta.json`, `template.toml` and the README's block for the Environment tab.

## How a compose file is hashed

Teme compares hashes made from a compose file's bytes, in four steps:

1. Replace every CR LF (`0x0D 0x0A`) with LF (`0x0A`).
2. Remove space, tab, LF, CR, NUL and vertical tab (`0x20 0x09 0x0A 0x0D 0x00 0x0B`) from the end.
3. Add one LF.
4. Take SHA-256, written as 64 lowercase hex digits.

For example, the bytes `services:\r\n  web: {}\r\n\r\n` hash to `78ae680a3841176cc921326a7837fc012f1f21701a4f5a4d6943f9e6c20b8af8`. Teme's own test checks the same pair.

## Following Teme's releases

A scheduled workflow reads Teme's newest release each day. When its image is published, the workflow opens a pull request that moves the template to it, and the pull request merges itself once the checks pass. GitHub pauses scheduled workflows in a repository with no activity for 60 days; run **follow-teme** by hand from the Actions tab to start it again.

