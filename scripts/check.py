#!/usr/bin/env python3
"""Checks the template before it is published: meta.json, template.toml, the compose file, compose-hashes.json and
the README agree, and the compose file keeps its promises. Needs Python 3.11 or later and Docker Compose.

  python3 scripts/check.py [--previous OLD-compose-hashes.json]

--previous names the list as it was before this change: every hash in it must still be listed.
"""

import base64
import json
import re
import secrets
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bump import VERSION  # noqa: E402
from hashes import BLUEPRINT, LIST, hash_of  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "blueprints" / "teme" / "template.toml"
README = ROOT / "README.md"

SITE_PARTS = ["deploy", "web", "worker", "worker-long", "scheduler"]
LIMITS = {
    "teme-postgres": ("TEME_POSTGRES", "1", "1g"),
    "web": ("TEME_WEB", "1", "1g"),
    "worker": ("TEME_WORKER", "0.5", "768m"),
    "worker-long": ("TEME_WORKER_LONG", "0.5", "1536m"),
    "scheduler": ("TEME_SCHEDULER", "0.25", "512m"),
    "installer": ("TEME_INSTALLER", "0.5", "1g"),
    "updater": ("TEME_UPDATER", "0.25", "256m"),
}
# The settings Teme's media disks read: every part that runs the site needs each, empty when unset, so a worker
# writes where web reads.
MEDIA = [
    "MEDIA_STORAGE", "MEDIA_DISK", "MEDIA_ORIGINALS_DISK", "MEDIA_URL",
    "MEDIA_BUCKET", "MEDIA_ORIGINALS_BUCKET", "MEDIA_BUCKET_ROOT", "MEDIA_ORIGINALS_BUCKET_ROOT",
    "MEDIA_BUCKET_ENDPOINT", "MEDIA_BUCKET_REGION", "MEDIA_BUCKET_PATH_STYLE",
    "MEDIA_BUCKET_ACCESS_KEY_ID", "MEDIA_BUCKET_SECRET_ACCESS_KEY", "MEDIA_BUCKET_URL", "MEDIA_BUCKET_ACL",
]
VOLUME_NAME = "${STACK_SLUG:-${COMPOSE_PROJECT_NAME:-teme}}_"
# The whole environment of the two parts that never read the Environment tab: the core, and what each one needs.
CORE = ["APP_NAME", "APP_URL", "APP_KEY", "DB_HOST", "DB_PORT", "DB_DATABASE", "DB_USERNAME", "DB_PASSWORD", "PGCONNECT_TIMEOUT"]
INSTALLER_ENVIRONMENT = sorted([*CORE, "PAGE_CACHE_DRIVER", "TEME_EXTENSIONS_PATH", "TEME_EXTENSIONS_ROLE"])
UPDATER_ENVIRONMENT = sorted([
    *CORE, "TEME_IMAGE_REPOSITORY", "TEME_GITHUB_TOKEN", "TEME_UPDATER_PLATFORM",
    "TEME_DOKPLOY_URL", "TEME_DOKPLOY_TOKEN", "TEME_DOKPLOY_COMPOSE_ID", "TEME_DOKPLOY_APP_NAME",
])
MAKERS_TALK = re.compile(r"\bI-\d+|\bwe\b|decided|the owner|for now|not prov|not finished|\b20\d\d-\d\d-\d\d\b", re.I)
EXAMPLE_VALUES = {
    "TEME_IMAGE": "ghcr.io/temecms/teme:0.0.0",
    "TEME_UPDATER_IMAGE": "ghcr.io/temecms/teme:0.0.0",
    "APP_URL": "https://example.test",
    "APP_KEY": "base64:x",
    "DB_PASSWORD": "x",
    "POSTGRES_PASSWORD": "y",
}

problems = []


def problem(sentence: str) -> None:
    problems.append(sentence)


def compose(*options: str, environment: dict | None = None, env_file: Path | None = None) -> dict:
    """The compose file as Docker Compose reads it, with anchors and merges resolved."""
    files = ["--env-file", str(env_file)] if env_file is not None else []
    command = ["docker", "compose", "-p", "teme-abc123", *files, "-f", str(BLUEPRINT), "config", "--format", "json", *options]
    found = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", env={**base_environment(), **(environment or {})})
    if found.returncode != 0:
        raise SystemExit(f"docker compose config failed: {found.stderr.strip()}")
    return json.loads(found.stdout)


def base_environment() -> dict:
    import os

    # Dokploy runs Compose with a clean environment: none of the names the compose file reads come from the shell.
    named = set(re.findall(r"\$\{([A-Z][A-Z0-9_]*)", BLUEPRINT.read_text(encoding="utf-8")))
    return {name: value for name, value in os.environ.items() if name not in named}


def fill(text: str, variables: dict, domain: str) -> str:
    """Fills a template value as Dokploy does: its generators, then the variables made before it."""

    def one(found: re.Match) -> str:
        name = found.group(1)
        if name == "domain":
            return domain
        if match := re.fullmatch(r"base64:(\d+)", name):
            return base64.b64encode(secrets.token_bytes(int(match.group(1)))).decode()
        if match := re.fullmatch(r"hash:(\d+)", name):
            length = int(match.group(1))
            return secrets.token_hex((length + 1) // 2)[:length]
        if match := re.fullmatch(r"password:(\d+)", name):
            return secrets.token_hex(int(match.group(1)))[: int(match.group(1))]
        return variables.get(name, found.group(0))

    return re.sub(r"\$\{([^}]+)\}", one, text)


def template_environment(template: dict, app_name: str | None = "teme-abc123", domain: str = "teme-1a2b3c-203-0-113-9.sslip.io") -> list:
    """The Environment tab's lines for a new service.

    ASSUMPTION: Dokploy's deployTemplate passes the service's App Name to the template as the variable APP_NAME
    (apps/dokploy/server/api/routers/compose.ts, v0.31.2: `variables: { APP_NAME: appName, ...}`; DokployPress's
    `stack_slug = "${APP_NAME}"` resolves the same way). This function assumes it, so a green check does not prove it:
    the live run checks the stored Environment tab. Pass app_name=None for Dokploy leaving ${APP_NAME} as it is.
    """
    variables = {} if app_name is None else {"APP_NAME": app_name}
    for name, value in template["variables"].items():
        variables[name] = fill(value, variables, domain)
    return [fill(line, variables, domain) for line in template["config"]["env"]]


def settings_lines(lines: list) -> list:
    """The lines that set something: the Environment tab without its comment lines and blank lines, which Dokploy's
    .env parser skips."""
    return [line for line in lines if line.strip() != "" and not line.lstrip().startswith("#")]


def check_meta(template: dict) -> None:
    meta = json.loads((ROOT / "meta.json").read_text(encoding="utf-8"))
    if not isinstance(meta, list) or len(meta) != 1:
        problem("meta.json must be a list of one template.")
        return
    entry = meta[0]
    if list(entry.keys()) != ["id", "name", "version", "description", "logo", "links", "tags"]:
        problem("meta.json's entry must have id, name, version, description, logo, links and tags, in that order.")
    if entry.get("id") != "teme" or entry.get("name") != "TemeCMS":
        problem("meta.json's entry must be id teme, name TemeCMS.")
    if not (ROOT / "blueprints" / "teme" / str(entry.get("logo"))).is_file():
        problem("meta.json's logo isn't in blueprints/teme/.")
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", str(entry.get("version"))):
        problem("meta.json's version isn't the template's own version, such as 1.0.3.")
    if not str(entry.get("description", "")).endswith(f" Installs Teme {template['variables'].get('teme_version')}."):
        problem("meta.json's description must end with the Teme release template.toml installs.")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    newest = re.search(r"^## (\S+)", changelog, re.M)
    if newest is None or newest.group(1) != entry.get("version"):
        problem("CHANGELOG.md's newest heading must be meta.json's version.")


def check_template(template: dict, compose_text: str) -> None:
    every = template_environment(template)
    for line in every:
        if line.lstrip().startswith("#") and re.match(r"#\s*TEME_(UPDATER_)?IMAGE\s*[=:]", line.lstrip()):
            problem("template.toml's comments must not set TEME_IMAGE or TEME_UPDATER_IMAGE, even commented out.")
    env = settings_lines(every)
    for line in env:
        if re.search(r"\s#", line.split("=", 1)[-1]):
            problem(f"template.toml's env entry {line!r} has a comment after its value; a comment goes on a line of its own.")
    names = [line.split("=", 1)[0] for line in env]
    settings = dict(line.split("=", 1) for line in env)
    if len(names) != len(set(names)):
        problem("template.toml sets a setting twice; the updater needs one line per setting.")
    for line in env:
        if "\n" in line or "=" not in line:
            problem(f"template.toml's env entry {line!r} isn't one plain KEY=value line.")

    required = set(re.findall(r"\$\{([A-Z][A-Z0-9_]*):\?", compose_text)) - {"COMPOSE_PROJECT_NAME"}
    for name in sorted(required):
        if not settings.get(name):
            problem(f"template.toml doesn't fill {name}, which the compose file requires.")

    version = template["variables"].get("teme_version")
    for name in ("TEME_IMAGE", "TEME_UPDATER_IMAGE"):
        if settings.get(name) != f"ghcr.io/temecms/teme:{version}":
            problem(f"template.toml's {name} isn't ghcr.io/temecms/teme at teme_version.")
        if not re.fullmatch(r"[a-z0-9./-]+:[0-9A-Za-z.+-]+", settings.get(name, "")):
            problem(f"template.toml's {name} isn't a plain image name the updater can change.")
    if settings.get("TEME_IMAGE_REPOSITORY") != "ghcr.io/temecms/teme":
        problem("template.toml's TEME_IMAGE_REPOSITORY isn't ghcr.io/temecms/teme.")

    key = settings.get("APP_KEY", "")
    try:
        decoded = base64.b64decode(key.removeprefix("base64:"), validate=True) if key.startswith("base64:") else b""
    except ValueError:
        decoded = b""
    if len(decoded) != 32:
        problem("template.toml's APP_KEY isn't base64: and 32 random bytes.")
    if settings_lines(template_environment(template)) == env:
        problem("template.toml makes the same secrets twice; they must be generated.")

    for name in ("db_password", "postgres_password"):
        if template["variables"].get(name) != "${hash:64}":
            problem(f"template.toml's {name} must be ${{hash:64}}: letters and digits, from a secure source.")
    if settings.get("DB_PASSWORD") == settings.get("POSTGRES_PASSWORD"):
        problem("The two database passwords must differ.")
    for name in ("STACK_SLUG", "TEME_DOKPLOY_APP_NAME"):
        if settings.get(name) != "teme-abc123":
            problem(f"template.toml's {name} must be the App Name, ${{APP_NAME}}.")
    if settings.get("APP_URL") != "https://teme-1a2b3c-203-0-113-9.sslip.io":
        problem("template.toml's APP_URL must be https:// and the domain.")
    if template["config"].get("domains") != [{"serviceName": "web", "port": 8080, "host": "${main_domain}"}]:
        problem("template.toml must serve web on port 8080 at ${main_domain}.")
    if template["variables"].get("main_domain") != "${domain}":
        problem("template.toml's main_domain must be ${domain}.")


def check_compose(compose_text: str) -> None:
    raw = compose("--no-interpolate")
    services = raw["services"]
    if re.search(r"^name:", compose_text, re.M):
        problem("The compose file names its project; Dokploy names it after the App Name.")

    for name, service in services.items():
        env_file = service.get("env_file")
        if name in SITE_PARTS:
            paths = [entry.get("path") if isinstance(entry, dict) else entry for entry in env_file or []]
            if len(paths) != 1 or not str(paths[0]).replace("\\", "/").endswith(".env") or env_file[0].get("required") is not False:
                problem(f"{name} must read the Environment tab: env_file .env, not required.")
            environment = service.get("environment", {})
            for blank in ("POSTGRES_PASSWORD", "TEME_DOKPLOY_TOKEN"):
                if environment.get(blank) != "":
                    problem(f"{name} must set {blank} empty, so the Environment tab's never reaches it.")
            if environment.get("APP_NAME") != "Teme":
                problem(f"{name} must keep APP_NAME: Teme; Dokploy writes its App Name there.")
            for media in MEDIA:
                default = "server" if media == "MEDIA_STORAGE" else ""
                if environment.get(media) != f"${{{media}:-{default}}}":
                    problem(f"{name} must pass {media}, defaulting to {default or 'empty'}.")
        elif env_file:
            problem(f"{name} must not read the Environment tab.")

    if services["installer"].get("user") != "9990:9990":
        problem("The installer must run as its own user, 9990.")
    if sorted(services["installer"].get("environment", {}).keys()) != INSTALLER_ENVIRONMENT:
        problem(f"The installer's environment must be the core and its own settings alone: {', '.join(INSTALLER_ENVIRONMENT)}.")
    if sorted(services["updater"].get("environment", {}).keys()) != UPDATER_ENVIRONMENT:
        problem(f"The updater's environment must be the core and the platform's settings alone: {', '.join(UPDATER_ENVIRONMENT)}.")
    updater = services["updater"]
    if sorted(updater.get("networks", {}).keys()) != ["default", "dokploy-network"]:
        problem("The updater must join default and dokploy-network.")
    expected = {
        "TEME_DOKPLOY_URL": "${TEME_DOKPLOY_URL:-http://dokploy:3000}",
        "TEME_DOKPLOY_TOKEN": "${TEME_DOKPLOY_TOKEN:-}",
        "TEME_DOKPLOY_APP_NAME": "${TEME_DOKPLOY_APP_NAME:-${COMPOSE_PROJECT_NAME:-}}",
        "TEME_UPDATER_PLATFORM": "dokploy",
    }
    for name, value in expected.items():
        if updater["environment"].get(name) != value:
            problem(f"The updater's {name} must be {value}.")
    if set(re.findall(r"\$\{TEME_GITHUB_TOKEN[^}]*\}", compose_text)) != {"${TEME_GITHUB_TOKEN:-}"}:
        problem("TEME_GITHUB_TOKEN must have an empty default wherever it is named.")
    if ":latest" in compose_text:
        problem("The compose file names a latest tag.")

    for name, (prefix, cpus, memory) in LIMITS.items():
        limits = services[name]["deploy"]["resources"]["limits"]
        if str(limits.get("cpus")) != f"${{{prefix}_CPUS:-{cpus}}}" or str(limits.get("memory")) != f"${{{prefix}_MEMORY:-{memory}}}":
            problem(f"{name}'s limits must be {prefix}_CPUS and {prefix}_MEMORY, defaulting to {cpus} and {memory}.")

    for key, volume in raw["volumes"].items():
        if volume.get("name") != VOLUME_NAME + key:
            problem(f"The volume {key} must be named {VOLUME_NAME}{key}.")

    # Interpolated as Dokploy runs it, without STACK_SLUG: the names Docker gave the unnamed volumes before.
    resolved = compose(environment={**EXAMPLE_VALUES, "COMPOSE_PROJECT_NAME": "teme-abc123"})
    for key, volume in resolved["volumes"].items():
        if volume.get("name") != f"teme-abc123_{key}":
            problem(f"Without STACK_SLUG the volume {key} must keep Docker's name teme-abc123_{key}.")
    slug = compose(environment={**EXAMPLE_VALUES, "COMPOSE_PROJECT_NAME": "teme-abc123", "STACK_SLUG": "my-site"})
    for key, volume in slug["volumes"].items():
        if volume.get("name") != f"my-site_{key}":
            problem(f"With STACK_SLUG the volume {key} must be my-site_{key}.")

    # Neither part that keeps out of the Environment tab gets the media keys, the database's own password, or mail.
    for name in ("installer", "updater"):
        for secret in ("MEDIA_BUCKET_SECRET_ACCESS_KEY", "MEDIA_BUCKET_ACCESS_KEY_ID", "POSTGRES_PASSWORD", "MAIL_PASSWORD"):
            if secret in resolved["services"][name].get("environment", {}):
                problem(f"The {name} must not receive {secret}.")
    if "TEME_GITHUB_TOKEN" in resolved["services"]["installer"].get("environment", {}):
        problem("The installer must not receive TEME_GITHUB_TOKEN.")


def dokploy_env_file(lines: list, folder: Path) -> Path:
    """A .env as Dokploy writes one for a Compose service: its own two lines first, then the Environment tab, each
    value quoted, with a $ that doesn't open a ${NAME} escaped."""
    path = folder / "dokploy.env"
    written = ['APP_NAME="teme-abc123"', 'COMPOSE_PROJECT_NAME="teme-abc123"']
    for line in settings_lines(lines):
        key, value = line.split("=", 1)
        value = re.sub(r"\$(?!\{[A-Za-z_][A-Za-z0-9_]*\})", r"\\$", value.replace("\\", "\\\\").replace('"', '\\"'))
        written.append(f'{key}="{value}"')
    path.write_text("\n".join(written) + "\n", encoding="utf-8", newline="\n")
    return path


def check_dokploy_env(template: dict) -> None:
    """The site's folders and the updater's App Name, from the .env Dokploy writes: whether Dokploy fills ${APP_NAME}
    in the template (the assumption template_environment makes) or leaves it as it is, Compose reads APP_NAME from the
    line Dokploy writes first, so neither gives a folder named after a literal ${APP_NAME}."""
    import tempfile

    for app_name, case in (("teme-abc123", "Dokploy fills ${APP_NAME}"), (None, "Dokploy leaves ${APP_NAME} as it is")):
        with tempfile.TemporaryDirectory() as folder:
            env = dokploy_env_file(template_environment(template, app_name=app_name), Path(folder))
            try:
                resolved = compose(env_file=env)
            except SystemExit as refused:
                problem(f"{case}: Compose refuses the template's settings: {refused}")
                continue
        for key, volume in resolved["volumes"].items():
            if volume.get("name") != f"teme-abc123_{key}":
                problem(f"{case}: the volume {key} must be teme-abc123_{key}, not {volume.get('name')}.")
        if resolved["services"]["updater"]["environment"].get("TEME_DOKPLOY_APP_NAME") != "teme-abc123":
            problem(f"{case}: the updater's TEME_DOKPLOY_APP_NAME must be the App Name.")


def check_hashes(previous: Path | None) -> None:
    data = json.loads(LIST.read_text(encoding="utf-8"))
    current = hash_of(BLUEPRINT.read_bytes())
    released = data.get("released", [])
    if data.get("format") != 1:
        problem("compose-hashes.json must be format 1.")
    if data.get("current") != current:
        problem("compose-hashes.json's current isn't the blueprint's hash: run python3 scripts/hashes.py update.")
    if current not in released:
        problem("compose-hashes.json doesn't list the blueprint as released: run python3 scripts/hashes.py update.")
    if any(not re.fullmatch(r"[0-9a-f]{64}", str(found)) for found in released) or len(released) != len(set(released)):
        problem("compose-hashes.json's released list must be distinct SHA-256 hashes.")
    if previous is not None and previous.exists():
        before = json.loads(previous.read_text(encoding="utf-8")).get("released", [])
        if [found for found in before if found not in released]:
            problem("compose-hashes.json dropped a released hash; a site may still run that file.")


def check_words(compose_text: str) -> None:
    for path in (BLUEPRINT, TEMPLATE):
        comments = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if line.lstrip().startswith("#"))
        if MAKERS_TALK.search(comments):
            problem(f"{path.name}'s comments read as notes between its makers.")
    readme = README.read_text(encoding="utf-8")
    if MAKERS_TALK.search(readme):
        problem("README.md reads as notes between its makers.")
    if "https://raw.githubusercontent.com/temecms/temecms-for-dokploy/main" not in readme:
        problem("README.md doesn't give the Base URL.")
    block = re.search(r"```env\n(.*?)```", readme, re.S)
    pasted = dict(line.strip().split("=", 1) for line in block.group(1).splitlines() if "=" in line) if block else {}
    required = set(re.findall(r"\$\{([A-Z][A-Z0-9_]*):\?", compose_text)) - {"COMPOSE_PROJECT_NAME"}
    if set(pasted) != required | {"TEME_IMAGE_REPOSITORY"}:
        problem("README.md's block for the Environment tab must name every setting the compose file requires.")
    version = tomllib.loads(TEMPLATE.read_text(encoding="utf-8"))["variables"]["teme_version"]
    for name in ("TEME_IMAGE", "TEME_UPDATER_IMAGE"):
        if pasted.get(name) != f"ghcr.io/temecms/teme:{version}":
            problem(f"README.md's {name} must be the template's release.")
    for prefix, cpus, memory in LIMITS.values():
        if f"`{prefix}_CPUS={cpus}`" not in readme or f"`{prefix}_MEMORY={memory}`" not in readme:
            problem(f"README.md must give {prefix}'s limits with their defaults.")


def main(argv: list) -> int:
    previous = Path(argv[argv.index("--previous") + 1]) if "--previous" in argv else None
    compose_text = BLUEPRINT.read_text(encoding="utf-8")
    template = tomllib.loads(TEMPLATE.read_text(encoding="utf-8"))
    check_meta(template)
    check_template(template, compose_text)
    check_compose(compose_text)
    check_dokploy_env(template)
    check_hashes(previous)
    check_words(compose_text)
    for sentence in problems:
        print(f"FAIL: {sentence}", file=sys.stderr)
    if problems:
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
