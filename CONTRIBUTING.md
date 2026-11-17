# Contributing

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
