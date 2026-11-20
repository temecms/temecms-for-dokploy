# Changelog

Each entry says whether the compose file changed. A site made from the template keeps the compose file it was made with until Teme's updater replaces it, which it does only for a file listed in `compose-hashes.json`.

## Unreleased

- Installs Teme 1.3.2.

- Installs Teme 1.1.1.

- Installs Teme 1.1.0.

### Changed (the compose file changed)

- No part swaps: each has a swap limit equal to its memory limit, so a part at its limit can't slow the other sites on the server.
- `web` starts at most 10 PHP workers by default (`PHP_FPM_PM_MAX_CHILDREN`), which fit in its 1g.
- The scheduler's memory is 512m by default (was 256m), so a backup run fits.

- Installs Teme 1.0.1.

### Added

- Install Teme from Dokploy's template list: paste one address, choose TemeCMS, and deploy, with every setting filled for you.
- Each part's CPU and memory limit can be changed on Dokploy's Environment tab.
- `compose-hashes.json` lists every compose file released, so Teme's updater can bring a new compose file to an existing site, unless the file was edited on the server.
- A daily workflow opens a pull request that moves the template to Teme's newest release, once its image is published.
- Checks and tests for the template, run on every change.

### Changed

- The template now lives where Dokploy's Base URL expects it: `meta.json`, and `blueprints/teme/` with the compose file, `template.toml` and the icon.
- Server folders are named after the site, and existing installs keep the folders they have.
- Settings typed on Dokploy's Environment tab now reach the site, but never the plugin installer or the updater.
- The plugin installer and the updater get only Teme's address, its app key, its database login and their own settings: no media storage keys, no mail, and not the database's own password.
- The updater finds its Dokploy service by the service's name, and its Dokploy API key is entered in Teme's Settings › Updates.
- The README is rewritten as step-by-step instructions for every way to install.

Compose file: changed. Sites made from Teme's `docker/compose.dokploy.yml` get this file at their next update from the admin.

## 2026-11-15

### Changed

- Pins Teme v0.8.0-alpha.1.
- Teme is public: the image is `ghcr.io/temecms/teme`, pulled with no sign-in; the private-repository steps and the GitHub token text are gone (the token is optional).

Compose file: unchanged since Teme v0.7.0-alpha.1.

## 2026-11-13

### Added

- First files. Pins Teme v0.7.0-alpha.1.

Compose file: first version.
