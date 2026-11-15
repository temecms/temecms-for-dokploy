# Steps: from today's files to a published one-click entry

Pick this up at any step. Tick a box when its proof is done. "Maintainer" means a person with their own Dokploy panel; no assistant ever handles a Dokploy token.

## Stage 1. Files written

- [x] README.md, docker-compose.yml (Teme's `compose.dokploy.yml` plus changes marked `TemeCMS:`), template.toml, meta.json, logo.svg, .env.example, CHANGELOG.md, NOT-YET-PROVED.md. Proof: `scripts/sync-compose.sh` shows only `TemeCMS:` lines and the header.
- [x] scripts/bump.sh, sync-compose.sh, check.sh. Proof: `sh -n` on each.
- [x] The repository, `temecms/temecms-for-dokploy`, and its first commit, pinned to Teme v0.8.0-alpha.1.
- [x] Run `scripts/check.sh` once (needs Docker for the compose parse). Proof: "all checks passed" (2026-11-15).

## Stage 2. First deploy on a scratch Dokploy project

Detail for every item: [NOT-YET-PROVED.md](NOT-YET-PROVED.md). Who: a maintainer, on the panel.

- [ ] Make the import text and import it (item 2). Proof: the box shows compose, variables and domain.
- [ ] App key format (item 1). Proof: 44 characters after `base64:`.
- [ ] Deploy reaches the holding page (items 2 and 9). Proof: `/` 503, `/admin/setup` 200, and the image pulled with no registry sign-in.
- [ ] Settings pass-through (item 3). Proof: a test variable is seen in `web`; the token is blank there.
- [ ] Read the setup code (item 4) and make the first account (item 5). Proof: `/` answers 200; `teme:doctor` has no error.
- [ ] Update button with the three typed values (item 6). Proof: one real update, and a bad tag rolls back.
- [ ] A backup (item 7). Proof: `teme:backup:verify` passes both ways.
- [ ] Two sites on one server (item 8). Proof: both run, each updates itself.

## Stage 3. Fix what the first deploy finds; record the version

- [ ] Fix each failed item the way its entry in NOT-YET-PROVED.md says, re-run it, and write the result under "Results" with the date.
- [ ] Write the proved Dokploy version in the README ("Written against") and template.toml's header.
- [ ] Move proved items out of the README's "What is not yet proved" list, and add a CHANGELOG entry with its operator note.

## Stage 4. The image's home: settled

- [x] The image lives at `ghcr.io/temecms/teme`, Teme's public organisation, and `template.toml` points there.

## Stage 5. Teme is public: settled

- [x] The private-repository steps, the registry sign-in and the token text are gone from the README and `.env.example`.
- [x] meta.json's links are filled in.
- [x] Add a licence file: MIT, as Teme (2026-11-15).

## Stage 6. Publish in Dokploy's public templates list

What their repository asks for (CONTRIBUTING of `Dokploy/templates`, read 2026-11-13; re-read before you start, it changes):

- A folder `blueprints/<id>/` holding `docker-compose.yml`, `template.toml`, `meta.json` and a logo (SVG preferred). The `id` in meta.json must equal the folder name (`temecms`).
- meta.json fields: `id`, `name`, `version`, `description`, `logo`, `links` (`github`, `website`, `docs`; `""` when none), `tags`.
- The compose file must not publish ports, must not use `container_name`, and must not define networks such as `dokploy-network`. It should use persistent volumes. The domain goes in `template.toml` as `[[config.domains]]` with `serviceName`, `port`, `host`; `serviceName` must match a service.
- Do not edit the root `meta.json`; it is generated. Run `node build-scripts/generate-meta.js --check` before pushing.
- Import the preview's Base64 into a Compose service and test: starts, reachable by its domain, restarts, volumes persist, variables work.

Steps:

- [ ] Remove `dokploy-network` from `web` and `updater` in the compose copy (their rule), after stage 2 item 8 showed whether it is needed. The updater's internal address may then need the panel's own `https://` address. Proof: item 6 re-run.
- [ ] Put the files in `blueprints/temecms/` of a fork of `Dokploy/templates` (this project keeps them at the top level; the fork copy is generated, never edited).
- [ ] Run their check and import the preview's Base64 on a scratch project. Proof: the test list above passes.
- [ ] Open the pull request. Waits on: stage 2 passing.

## Stage 7. Each Teme release after that

- [ ] Read Teme's release notes: do they say the compose file changed?
- [ ] `scripts/bump.sh vX.Y.Z`. Proof: it prints what changed.
- [ ] `scripts/sync-compose.sh <teme checkout> vX.Y.Z`. Proof: only `TemeCMS:` lines differ; bring over any other change by hand.
- [ ] `scripts/check.sh`. Proof: all checks passed.
- [ ] Deploy to a test project and reach the holding page; for an update-path change, run one update.
- [ ] CHANGELOG entry with the operator note, then tag. A security release: do this the same day.

## Stage 8. The same road for Coolify (`temecms-for-coolify`)

- [ ] Start from the same compose file, not from Teme's `compose.yml` (it needs `./secrets` files a pasted resource lacks).
- [ ] Secrets and the domain go inside the compose file as Coolify's magic variables (`SERVICE_PASSWORD_*`, `SERVICE_REALBASE64_32_*`, `SERVICE_URL_WEB_8080`), not in a `template.toml`.
- [ ] Coolify has no Teme updater driver yet, so sites update by hand until Teme gains one; its one-click catalogue is closed to outside contributions for now, so it ships as a Compose-from-Git resource first.
- [ ] Re-do stage 2 on a scratch Coolify, then stages 3 to 7 with its own notes.
