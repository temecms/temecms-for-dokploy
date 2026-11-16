# Changelog

Each entry says whether the compose file changed. A site made from the template keeps the compose file it was made with until Teme's updater replaces it, which it does only for a file listed in `compose-hashes.json`.

## Unreleased

### Added

- Install Teme from Dokploy's template list: paste one address, choose TemeCMS, and deploy, with every setting filled for you.
- Each part's CPU and memory limit can be changed on Dokploy's Environment tab.
- `compose-hashes.json` lists every compose file released, so Teme's updater can bring a new compose file to an existing site, unless the file was edited on the server.
- A daily workflow moves the template to Teme's newest release.
- Checks and tests for the template, run on every change.

### Changed

- The template now lives where Dokploy's Base URL expects it: `meta.json`, and `blueprints/teme/` with the compose file, `template.toml` and the icon.
- Server folders are named after the site, and existing installs keep the folders they have.
- Settings typed on Dokploy's Environment tab now reach the site, but never the plugin installer or the updater.
- The updater finds its Dokploy service by the service's name, and its Dokploy API key is entered in Teme's Settings › Updates.
- The README is rewritten as step-by-step instructions for every way to install.

Compose file: changed. Sites made from Teme's `docker/compose.dokploy.yml` get this file at their next update from the admin, or by the steps in *Moving an existing install to the template*.

## 2026-11-15

- Pins Teme v0.8.0-alpha.1. Teme's compose file is unchanged since v0.7.0-alpha.1.
- Teme is public: the image is `ghcr.io/temecms/teme`, pulled with no sign-in; the private-repository steps and the GitHub token text are gone (the token is optional).

## 2026-11-13

- First files. Pins Teme v0.7.0-alpha.1.
