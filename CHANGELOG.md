# Changelog

The template has its own version, shown on Dokploy's template list; every change other than to its documentation is a new version. New sites install from this repository's main branch, so a version is live the day it lands. Each entry says whether the compose file changed. A site made from the template keeps the compose file it was made with until Teme's updater replaces it, which it does only for a file listed in `compose-hashes.json`.

## 1.0.10 — 2026-11-27

- Installs Teme 1.7.1.

## 1.0.9 — 2026-11-26

- Installs Teme 1.6.1.

## 1.0.8 — 2026-11-25

- Installs Teme 1.5.0.

## 1.0.7 — 2026-11-24

- Installs Teme 1.4.2.

## 1.0.6 — 2026-11-23

- Installs Teme 1.4.0.

## 1.0.5 — 2026-11-23

### Changed (the compose file changed)

- `worker-long` can use 1.5 GB by default (was 512 MB), `worker` 768 MB (was 512 MB). Making the resized copies of a large photo needs up to 1 GB, and at 512 MB the long worker was stopped partway through, so a large photo got no resized copies. These are ceilings, not reservations: an idle worker uses far less.
- Both workers restart themselves after a job once they hold 512 MB (`--memory=512`), below their part's limit, instead of Laravel's 128 MB.

## 1.0.4 — 2026-11-22

- Installs Teme 1.3.3.

## 1.0.3 — 2026-11-21

### Changed

- A new site's Environment tab is grouped, with a comment above each group saying what it is for and what must never change after the first deploy. The mail settings are there too, commented out, ready to fill in.
- The comment above `TEME_DOKPLOY_APP_NAME` says not to edit it.
- The template has its own version, shown on the template list (this is 1.0.3); the Teme release it installs is named in its description.

Compose file: unchanged.

## 1.0.2 — 2026-11-20

- Installs Teme 1.3.2.

## 1.0.1 — 2026-11-18

- Installs Teme 1.1.1.
- Installs Teme 1.1.0.

### Changed (the compose file changed)

- No part swaps: each has a swap limit equal to its memory limit, so a part at its limit can't slow the other sites on the server.
- `web` starts at most 10 PHP workers by default (`PHP_FPM_PM_MAX_CHILDREN`), which fit in its 1g.
- The scheduler's memory is 512m by default (was 256m), so a backup run fits.

## 1.0.0 — 2026-11-17

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

## Before 1.0.0

### 2026-11-15

### Changed

- Pins Teme v0.8.0-alpha.1.
- Teme is public: the image is `ghcr.io/temecms/teme`, pulled with no sign-in; the private-repository steps and the GitHub token text are gone (the token is optional).

Compose file: unchanged since Teme v0.7.0-alpha.1.

### 2026-11-13

### Added

- First files. Pins Teme v0.7.0-alpha.1.

Compose file: first version.
