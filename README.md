# TemeCMS for Dokploy

Install [Teme](https://github.com/temecms/teme) on a [Dokploy](https://dokploy.com) server from Dokploy's template list. Teme is a content management system built on Laravel and PostgreSQL. This repository holds its Dokploy template: one Compose service that runs the site, its own PostgreSQL, two queue workers, the scheduler, the plugin installer and the updater behind the admin's Update button.

These instructions are written for Dokploy v0.31.2. The server needs Docker Compose 2.24 or later, which reads an `env_file` marked `required: false`. The image, `ghcr.io/temecms/teme`, is public, so Dokploy needs no registry sign-in.

## Ways to install

Dokploy can make a service in several ways. This table says which ones run Teme, and what each needs from you.

| Route | What you do | What Teme needs |
|---|---|---|
| **Template**, with this repository's Base URL | Create Service › Template, paste the Base URL, choose TemeCMS, Deploy | Nothing: the template fills every setting. See [Install from the template list](#install-from-the-template-list). |
| **Compose**, provider **Raw** | Create Service › Compose, paste the compose file | A short block of settings pasted once on the Environment tab. This is the only route where you paste values. See [Install by pasting the compose file](#install-by-pasting-the-compose-file). |
| **Compose**, provider **GitHub**, **GitLab**, **Bitbucket**, **Gitea** or **Git** | Create Service › Compose, point it at this repository and the compose path | The same block of settings as Raw. See [Install from Git](#install-from-git). |
| **Compose**, Compose Type **Stack** (Docker Swarm) | Not supported | Teme's file needs Docker Compose: its `deploy` step runs once and the other parts wait for it to finish, which Swarm can't do, and Swarm ignores the order the parts start in. Choose Compose Type **Docker Compose**. |
| **Application**: Docker image, GitHub, GitLab, Bitbucket, Gitea or Git with the Dockerfile, or Drop (a ZIP) | Teme as one container | See *Install as one Application* in [Teme's Dokploy page](https://github.com/temecms/teme/blob/main/docs/guides/operators/platforms/dokploy.md). |
| **Database**, and Dokploy's scheduled jobs | Not used with the Compose file | The file brings its own PostgreSQL, and Teme runs its own schedule. |

## Install from the template list

1. **Open the template list.** In your Dokploy project, choose **Create Service**, then **Template**.
2. **Point it at Teme.** In **Base URL**, paste:

   ```text
   https://raw.githubusercontent.com/temecms/temecms-for-dokploy/main
   ```

   The list now shows **TemeCMS**. Your Dokploy user needs the permission to create services to use a Base URL.
3. **Make the service.** Choose **TemeCMS**, then **Create**. Dokploy makes a Compose service with every setting filled: the image at the newest Teme release, the site's address, a new app key and two new database passwords. You type nothing.
4. **Deploy.** Open the new service and choose **Deploy**. The first deploy takes a few minutes: Dokploy pulls the images, PostgreSQL starts, then `deploy` migrates the database, then the rest start.
5. **Read the setup code.** Open **Logs** and choose the `deploy` container. Its log ends with the setup page's address and a setup code.
6. **Make the first account.** Open that address, enter the code, and fill in the form. You are signed in as the site's administrator, and the site opens to readers.

The site's address is the one Dokploy made, ending in `sslip.io`, on the **Domains** tab. To use your own domain, see [Use your own domain](#use-your-own-domain). To update from the admin, see [Switch on Update from the admin](#switch-on-update-from-the-admin).

## Install by pasting the compose file

1. **Make the service.** Choose **Create Service**, then **Compose**. Set the provider to **Raw** and the Compose Type to **Docker Compose**, and paste the whole of [`blueprints/teme/docker-compose.yml`](blueprints/teme/docker-compose.yml).
2. **Paste the settings.** Open the **Environment** tab and paste this block, then fill the four empty values:

   ```env
   TEME_IMAGE=ghcr.io/temecms/teme:0.8.0-alpha.1
   TEME_UPDATER_IMAGE=ghcr.io/temecms/teme:0.8.0-alpha.1
   TEME_IMAGE_REPOSITORY=ghcr.io/temecms/teme
   APP_URL=
   APP_KEY=
   DB_PASSWORD=
   POSTGRES_PASSWORD=
   ```

   - `TEME_IMAGE` and `TEME_UPDATER_IMAGE`: the same release, never `latest`. [Teme's releases](https://github.com/temecms/teme/releases) lists them; the tag has no `v`.
   - `APP_URL`: your site's address, with `https://`.
   - `APP_KEY`: make it once and keep it. On Linux or macOS: `echo "base64:$(openssl rand -base64 32)"`. On Windows PowerShell: `$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); "base64:" + [Convert]::ToBase64String($b)`.
   - `DB_PASSWORD` and `POSTGRES_PASSWORD`: two different passwords of letters and digits only, since Compose rewrites a `$`. On Linux or macOS, run `openssl rand -hex 32` once for each. On Windows PowerShell: `$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); -join ($b | ForEach-Object { $_.ToString('x2') })`.

   Save.
3. **Set the domain.** On the **Domains** tab, add your site's address with the service `web`, port `8080`, and HTTPS on.
4. **Deploy**, then read the setup code and make the first account as steps 4 to 6 of [the template](#install-from-the-template-list) say.

## Install from Git

1. **Make the service.** Choose **Create Service**, then **Compose**, Compose Type **Docker Compose**. Choose your Git provider, or **Git** with `https://github.com/temecms/temecms-for-dokploy.git`, the branch `main`, and the **Compose Path** `blueprints/teme/docker-compose.yml`.
2. **Paste the settings, set the domain, deploy and make the first account** as steps 2 to 4 of [pasting the compose file](#install-by-pasting-the-compose-file) say.

Each **Deploy** reads the compose file from Git again, so a new compose file arrives with it. An update from the admin changes only the images on a service that reads its file from Git.

## Use your own domain

1. On the **Domains** tab, edit the domain: set the host to your domain, keep the service `web` and port `8080`, and turn HTTPS on with Let's Encrypt. Point your domain's DNS at the server first.
2. On the **Environment** tab, set `APP_URL` to the same address, with `https://`, and save.
3. **Deploy.**

Teme makes every address from `APP_URL`, so nothing in your content changes.

## Switch on Update from the admin

1. **Make a key in Dokploy.** Open your profile settings in Dokploy, find **API/CLI**, and generate a key. Copy it.
2. **Paste it into Teme.** In Teme's admin, open **Settings › Updates**, paste the key into **Dokploy API key**, and save. Teme asks for your password again. The key is kept encrypted and never shown again.
3. **Check it.** Within two minutes the updater tries the key. If it can't use it, Settings › Updates says why in one sentence, and what to do.

Then **Tools › Updates › Update to …** updates the site. When this template's compose file has changed since your site was made, the update replaces the site's file too, as long as it is one this repository released ([`compose-hashes.json`](compose-hashes.json) lists them). A file edited on the server stops the update before anything changes, and Tools › Updates says to paste the new file first. [Teme's Dokploy page](https://github.com/temecms/teme/blob/main/docs/guides/operators/platforms/dokploy.md) says what the updater does, how long the site is down, and which permissions the key needs.

## Your site's folders

The site's data is in four Docker volumes: `pgdata` (the database), `media`, `page-cache` and `extensions`. Each is named for the site: `STACK_SLUG` and the volume's name, such as `my-site-teme-k3x9qa_media`. The template sets `STACK_SLUG` to the service's **App Name**; without it, the App Name is used. To use a shorter name, set `STACK_SLUG` on the **Environment** tab before the first deploy. Never change it afterwards: the site would start with empty volumes, and its data would stay in the old ones.

## Your site's settings

Everything on the **Environment** tab reaches `deploy`, `web`, the workers and the scheduler: [Configuring Teme](https://github.com/temecms/teme/blob/main/docs/guides/operators/configure.md) lists them, such as mail and `TRUSTED_PROXIES`. Two never do: `POSTGRES_PASSWORD` stays with the database, and `TEME_DOKPLOY_TOKEN` with the updater.

The plugin installer and the updater never read the Environment tab. Each has only Teme's address, its app key and its database login, and its own settings, such as Dokploy's for the updater. The installer needs the app key to open a key you saved for a private plugin source, and the database to keep its requests; Composer, which it runs, gets neither. The updater needs the app key to open the Dokploy API key Teme keeps encrypted. Neither has the media storage keys, mail, or the database's own password.

Each part's CPU and memory limit is a setting too, with these defaults:

| Service | CPUs | Memory |
|---|---|---|
| `teme-postgres` | `TEME_POSTGRES_CPUS=1` | `TEME_POSTGRES_MEMORY=1g` |
| `web` | `TEME_WEB_CPUS=1` | `TEME_WEB_MEMORY=1g` |
| `worker` | `TEME_WORKER_CPUS=0.5` | `TEME_WORKER_MEMORY=512m` |
| `worker-long` | `TEME_WORKER_LONG_CPUS=0.5` | `TEME_WORKER_LONG_MEMORY=512m` |
| `scheduler` | `TEME_SCHEDULER_CPUS=0.25` | `TEME_SCHEDULER_MEMORY=256m` |
| `installer` | `TEME_INSTALLER_CPUS=0.5` | `TEME_INSTALLER_MEMORY=1g` |
| `updater` | `TEME_UPDATER_CPUS=0.25` | `TEME_UPDATER_MEMORY=256m` |

`TEME_GITHUB_TOKEN` is optional: a read-only token that raises GitHub's limit when Teme asks for new releases.

## Moving an existing install to the template

A site installed from Teme's older `docker/compose.dokploy.yml` keeps its data when it moves to this file: its volumes already carry the names this file gives them.

1. On the service's **General** tab, note its **App Name**.
2. On the **Environment** tab, add `STACK_SLUG=` followed by that App Name, exactly, and save.
3. Replace the compose file with [`blueprints/teme/docker-compose.yml`](blueprints/teme/docker-compose.yml), and save.
4. **Deploy.** Your posts and media are there as before.
5. [Paste a Dokploy API key](#switch-on-update-from-the-admin) in Settings › Updates. You can then remove `TEME_DOKPLOY_TOKEN` and `TEME_DOKPLOY_COMPOSE_ID` from the **Environment** tab.

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

### How a compose file is hashed

Teme compares hashes made from a compose file's bytes, in four steps:

1. Replace every CR LF (`0x0D 0x0A`) with LF (`0x0A`).
2. Remove space, tab, LF, CR, NUL and vertical tab (`0x20 0x09 0x0A 0x0D 0x00 0x0B`) from the end.
3. Add one LF.
4. Take SHA-256, written as 64 lowercase hex digits.

For example, the bytes `services:\r\n  web: {}\r\n\r\n` hash to `78ae680a3841176cc921326a7837fc012f1f21701a4f5a4d6943f9e6c20b8af8`. Teme's own test checks the same pair.

### Following Teme's releases

A scheduled workflow reads Teme's newest release each day. When its image is published, the workflow opens a pull request that moves the template to it, and the pull request merges itself once the checks pass. GitHub pauses scheduled workflows in a repository with no activity for 60 days; run **follow-teme** by hand from the Actions tab to start it again. [CONTRIBUTING.md](CONTRIBUTING.md) says how to change the compose file.

## Licence

MIT, as Teme. See [LICENSE](LICENSE).
