# TemeCMS for Dokploy

This project is not finished: see [STEPS.md](STEPS.md) for where it stands.

## What this is

A one-click stack that puts a new site of [Teme](https://github.com/temecms/teme) on a Dokploy server, with everything set up.

Teme is a content management system built on Laravel and PostgreSQL. Dokploy is a hosting panel you run on your own server.

Pinned Teme release: v0.8.0-alpha.1 (teme-pin).

Every Teme release so far is an alpha, and so is this stack. Nothing here has been deployed yet: see [NOT-YET-PROVED.md](NOT-YET-PROVED.md). Written against Dokploy v0.31.2.

## What you get

One Dokploy service that runs:

- the Teme site (`web`),
- its PostgreSQL database (`teme-postgres`),
- two queue workers and a scheduler,
- a one-time `deploy` step that brings the database up to date,
- an `updater`, which carries out the Update button.

The panel generates the app key and both database passwords. It sets the domain. You type nothing secret to get a running site.

## Before you start

- A Dokploy server (v0.31.2 or newer; see "What is not yet proved").
- A domain whose address points at that server.

## Importing the template

Teme and its image (`ghcr.io/temecms/teme`) are public, so the image pulls with no sign-in. Until this template is in Dokploy's own list, you paste it in by hand: in your project choose Create Service, then Compose, then Advanced, then Import. Paste the Base64 text of this template (`template.toml` and `docker-compose.yml` together) and press Import. A box shows the compose file, the variables and the domain. Check them, then confirm. The exact text to paste is not made by a script yet: see item 2 of NOT-YET-PROVED.md.

The template holds no secrets. The panel makes them when you deploy.

## Deploy, step by step

1. Import the template (above).
2. Look at the Environment tab. You will see `APP_KEY`, `DB_PASSWORD`, `POSTGRES_PASSWORD`, the image names and `APP_URL`, already filled in. Leave them.
3. Open the Domains tab. The template made a random address. Replace the host with your real domain. Keep service `web`, port `8080`, HTTPS on.
4. In the Environment tab, change `APP_URL` to `https://` and the same domain. The two must match. Teme refuses requests for any other host.
5. Press Deploy.
6. Wait. The database starts, then `teme-db-setup` runs, then `deploy`, then the rest. The first deploy pulls a large image, so give it a few minutes.

## First run

1. Open your site's address. You see a holding page (a 503). That is right: Teme waits for its first administrator.
2. Find the setup code. In Dokploy open the service, then Logs, and choose the `deploy` container. The end of its log shows the address of the setup page and a code. Or open the Terminal of the `web` container, run `cd /var/www/html` and then `php artisan teme:setup-code`.
3. Open `https://your-domain/admin/setup`.
4. Enter the code. Fill in your name, email and password. You are the first administrator.
5. The public pages now answer. Sign in at `/admin/login`.
6. Run Teme's doctor once: in the `web` terminal, `cd /var/www/html` then `php artisan teme:doctor`. It first checks that the site address is right.

Never change `APP_KEY` after this point. It encrypts what Teme stores.

## Switching on the Update button

A template cannot make a Dokploy API token, so you type three values by hand. Without them the site works. You update by hand instead (see "Updating").

Set these in the service's Environment tab, then Deploy:

| Value | Where it comes from |
|---|---|
| `TEME_DOKPLOY_URL` | The template sets `http://dokploy:3000`. This works only if the updater can reach the panel on Dokploy's internal network. If it cannot, type the panel's own `https://` address. |
| `TEME_DOKPLOY_COMPOSE_ID` | Open the service in the panel. The address bar reads `.../services/compose/<this-id>`. Copy the id. |
| `TEME_DOKPLOY_TOKEN` | In Dokploy open your profile, then API keys, and make a key. |

Take care with the key. It can act as you in the panel. Make it as narrow as your Dokploy version allows: a Member key limited to this one service, with read on the service, write on its environment variables, and create and read on its deployments. Dokploy v0.31.1 added an "Access to API" permission when keys are made, so the narrow key must be re-proved on v0.31.2.

`TEME_GITHUB_TOKEN` is optional: Teme's releases are public, and a token only raises GitHub's limit on requests.

Only the scheduler and the updater receive the two tokens. The other services get them blanked on purpose.

Do not edit the Environment tab while an update is running. The updater rewrites that text.

Do not use Dokploy's scheduled jobs for Teme. The `scheduler` service runs Teme's schedule.

## Mail

Teme cannot send mail until you set it. In the Environment tab add `MAIL_MAILER`, `MAIL_HOST`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM_ADDRESS` and `MAIL_FROM_NAME`. Deploy again. The stack passes every such setting to every Teme service. Teme's doctor warns until mail is set.

All other settings (trusted proxies, update channel, AI keys, size limits) work the same way. Teme's own guide, `docs/guides/operators/configure.md`, lists them.

## Backups

Backups are not switched on by default. After your first administrator exists, open Tools, then Backups, and set up a destination that is not on the same server. Keep the recovery key somewhere safe and offline. Then run `teme:backup:verify`.

Teme's backup guide, `docs/guides/operators/backups.md`, has the steps and says what a backup holds. Dokploy's own database backups do not see the database inside this service.

## Updating

**From the admin.** After you set the three values above: Tools, then Updates, then Update to the new release. Teme asks for your password. The site is down for a short while as the service deploys.

**By hand.** Set `TEME_IMAGE` and `TEME_UPDATER_IMAGE` in the Environment tab to the new exact release tag, and Deploy.

**Updating this template.** The Teme release this template pins is only for new sites. A site already deployed keeps the compose text it was made with. Teme's release notes should say when a release changes `compose.dokploy.yml`. When one does, copy the change into the service's compose text by hand.

The maintainer bumps the pin with `scripts/bump.sh <tag>`, compares with `scripts/sync-compose.sh`, and runs `scripts/check.sh`.

## The image's home

The image lives at `ghcr.io/temecms/teme`, its permanent home. It is set in one place: the line `image_repository` at the top of `template.toml`. Sites also hold it in `TEME_IMAGE_REPOSITORY`, and their Update button builds image names from it.

## Running two sites on one server

NOT YET PROVED. Watch for:

- Both stacks put a service called `web` on Dokploy's shared network, and Teme's updater looks for it by that name.
- Each stack's database is called `teme-postgres`. Service names must be unique on a shared network. A `postgres` on that network was once reached by mistake.
- Dokploy's "Isolated Deployment" setting may make this safe. Test it before you rely on it.

## Troubleshooting

| What you see | What to do |
|---|---|
| The deploy fails pulling the image. | Check the tag in `TEME_IMAGE` exists on `ghcr.io/temecms/teme` (no leading `v`), and that the server can reach `ghcr.io`. |
| The whole deploy stops with a message about `TEME_UPDATER_IMAGE`. | That variable must always be set, to the same image as `TEME_IMAGE`. The template sets it. Do not delete it. |
| You see a redirect to a wrong address, or Teme refuses the request. | `APP_URL` and the Domains tab disagree. Set both to the same host. |
| After changing the domain, the site stops answering. | You changed the Domains tab but not `APP_URL`. Change `APP_URL` too, Deploy, then run `teme:doctor`. |
| The site shows a holding page for a long time. | No administrator exists yet. Read the setup code (see "First run"). |
| The site shows "bad gateway" while the service looks healthy. | A health check may be answering without PHP. Teme's `web` checks `/up`, through PHP and the database. Do not replace it with a lighter check. Redeploy the service. |
| The deploy warns about empty variables. | Harmless for optional ones. Only `TEME_UPDATER_IMAGE` is required. |
| A new setting does not seem to reach the site. | Deploy again after saving the Environment tab. Settings are read when containers start. |
| A security release came out. | Restarting does not change the PHP inside an image. Update to the new release through the Update button or by hand, the same day. |
| Two sites on one server confuse each other. | See "Running two sites on one server". |
| A password with a `$` in it breaks. | Use letters and digits only. Compose rewrites `$`. |

Teme's own troubleshooting guide is `docs/guides/operators/troubleshooting.md` in Teme's repository.

## What is not yet proved

- That the panel's `base64` helper gives a valid app key.
- That a deploy from the import reaches the holding page.
- That the setup code can be read as described.
- That the first account can be made.
- That the Update button works with the typed values, and with `http://dokploy:3000`.
- That a backup can be set up and verified.
- That two sites run side by side on one server.
- Which Dokploy version it all works on.
- That blanking the tokens on the services that should not hold them does not upset Teme.

NOT-YET-PROVED.md says how to prove each one and what to change if it fails.

## How this relates to Teme's own guide

This README holds the panel's steps and the template. Teme's guide, `docs/guides/operators/platforms/dokploy.md` in Teme's repository, holds the by-hand install and what Teme does. Teme's other operator guides (configure, updates, backups, troubleshooting) hold everything else. This project links to them and does not copy them.

## Thanks

The idea of a one-click stack for a CMS on Dokploy comes from DokployPress, a WordPress stack for Dokploy, itself forked and extended from `itsmereal/dokploy-wp`. No code is copied from either.
