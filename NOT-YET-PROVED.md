# Not yet proved

Only a real Dokploy deploy can settle these. Do them in this order, on a scratch Dokploy project, and write the result next to each item with the Dokploy version and the date. [STEPS.md](STEPS.md) stage 2 points here.

Written against Dokploy v0.31.2 (latest seen 2026-11-13). Nothing below has been run.

## 1. The app key's format

- **Question:** does `app_key = "base64:${base64:32}"` give `base64:` plus base64 of 32 random bytes? Dokploy's templates repository says the helper's number is a count of bytes, so it should. The study could not confirm it.
- **Prove it:** deploy, open the Environment tab, read `APP_KEY`. Count: 44 characters after `base64:`, ending in one `=`. Then open `/admin/setup`: Teme refuses to start with a bad key.
- **If it fails:** use `${password:32}` and tell Teme's side, or document a manual step in the README: make the key on a computer (`echo "base64:$(openssl rand -base64 32)"`) and paste it into `APP_KEY` before the first deploy. Mark that step in the README. Also check that the key stays the same across a redeploy (Dokploy's docs hint that redeploying a template may regenerate values).

## 2. A deploy from the import reaches the holding page

- **Question:** what exactly does the Base64 import (Compose service, Advanced, Import) take? Not confirmed: believed to be JSON holding the compose text and the template text, then Base64. Does `${domain}` become a random address? Does the Domains tab show `web`, port 8080?
- **Prove it:** make the import text, import, deploy. `web` is healthy, `deploy` exited 0, `/` answers 503 and `/admin/setup` answers 200.
- **If it fails:** work out the real payload from the Dokploy source or by exporting a known template; write `scripts/make-import.sh` to build it; fix the README step. If import cannot work, use Dokploy's Git provider.

## 3. The pass-through of settings

- **Question:** does Dokploy write the Environment tab to a `.env` beside the compose file, so `env_file` finds it? Does blanking the tokens on non-updater services upset Teme?
- **Prove it:** add `TEME_AI=off` or a mail variable to the tab, deploy, run `printenv` in `web`. `TEME_DOKPLOY_TOKEN` must be empty there and set in `updater`.
- **If it fails:** try Dokploy's own convention for passing the whole environment; otherwise list every variable in `x-teme-environment`.

## 4. Reading the setup code

- **Prove it:** the `deploy` container's log shows the setup page address and a code; `php artisan teme:setup-code` in `/var/www/html` of `web` shows it again.
- **If it fails:** change the README's words to where it really is.

## 5. The first account

- **Prove it:** enter the code at `/admin/setup`, make the administrator; `/` then answers 200; `teme:doctor` shows no error, and its SiteAddress check passes.
- **If it fails:** most likely `APP_URL` and the domain disagree. Otherwise a Teme bug: file it in Teme.

## 6. The Update button with the typed values

- **Question:** does it work with the hand-typed three values, with `http://dokploy:3000` and `dokploy-network` on the updater, and with a narrow API key on v0.31.2 (which added an "Access to API" permission)?
- **Prove it:** make the key, set the values, Deploy, update to the next Teme tag; every part healthy. Then try a bad tag: Teme must switch back.
- **If it fails:** try the panel's `https://` address; widen the key one permission at a time and record which are needed; remove `dokploy-network` from the updater if the address does not matter.

## 7. A backup

- **Prove it:** Tools, Backups, a destination off the server; `teme:backup:verify --read-back` and `--test-restore` both pass.
- **If it fails:** the README's backup paragraph is wrong or Teme has a bug. Decide after reading the error. Also settle whether a local `backups` volume is needed (parked in the study).

## 8. Two sites on one server

- **Prove it:** deploy the template twice on one Dokploy, with and without "Isolated Deployment". Both reach their holding pages; each updater finds its own `web`; neither database is reached by the other.
- **If it fails:** the compose file changes: remove `dokploy-network` from `web` (Dokploy adds it itself) and use isolation, or give services names that carry the project. Teme's updater needs `-web-1` style names, so any rename is a Teme change.

## 9. The image pulls with no sign-in

- **Prove it:** on a Dokploy with no registry sign-in for `ghcr.io`, the first deploy pulls `ghcr.io/temecms/teme` (public since 2026-11-14).
- **If it fails:** check the tag exists (no leading `v`) and that the server reaches `ghcr.io`.

## 10. The Dokploy version

- **Prove it:** run items 1 to 9 on one Dokploy version and record it here and in the README's "Written against" line.
- **If it fails:** record the oldest version that works. Read Dokploy's release notes for template changes.

## Results

Nothing recorded yet.
