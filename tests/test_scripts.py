"""Tests for scripts/bump.py, scripts/hashes.py and scripts/check.py.

  python3 -m unittest discover -s tests
"""

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import bump  # noqa: E402
import check  # noqa: E402
import hashes  # noqa: E402


def copy_of_repository() -> Path:
    """The files the scripts read, in a folder of their own."""
    root = Path(tempfile.mkdtemp())
    (root / "blueprints" / "teme").mkdir(parents=True)
    for name in ("meta.json", "compose-hashes.json", "README.md", "CHANGELOG.md"):
        shutil.copy(ROOT / name, root / name)
    for name in ("docker-compose.yml", "template.toml", "teme.svg"):
        shutil.copy(ROOT / "blueprints" / "teme" / name, root / "blueprints" / "teme" / name)
    return root


class BumpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = copy_of_repository()
        self.template = json.loads((ROOT / "meta.json").read_text(encoding="utf-8"))[0]["version"]
        self.was = check.tomllib.loads((ROOT / "blueprints" / "teme" / "template.toml").read_text(encoding="utf-8"))["variables"]["teme_version"]
        major, minor, patch = (int(part) for part in self.template.split("."))
        self.next = f"{major}.{minor}.{patch + 1}"

    def read(self) -> tuple:
        meta = (self.root / "meta.json").read_text(encoding="utf-8")
        toml = (self.root / "blueprints" / "teme" / "template.toml").read_text(encoding="utf-8")
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        return meta, toml, readme

    def test_sets_the_release_and_makes_a_new_patch_version_of_the_template(self) -> None:
        meta, toml, readme = self.read()

        said = bump.bump("99.0.0", self.root)

        new_meta, new_toml, new_readme = self.read()
        self.assertEqual("The template installs 99.0.0 now.", said)
        self.assertEqual(
            meta.replace(f'"version": "{self.template}"', f'"version": "{self.next}"').replace(f" Installs Teme {self.was}.", " Installs Teme 99.0.0."),
            new_meta,
        )
        self.assertEqual(toml.replace(f'teme_version = "{self.was}"', 'teme_version = "99.0.0"'), new_toml)
        self.assertEqual(readme.replace(f"ghcr.io/temecms/teme:{self.was}", "ghcr.io/temecms/teme:99.0.0"), new_readme)

    def test_leaves_a_template_that_passes_its_checks(self) -> None:
        bump.bump("99.0.0", self.root)
        saved = (check.BLUEPRINT, check.TEMPLATE, check.README, check.LIST, check.ROOT)
        check.BLUEPRINT = self.root / "blueprints" / "teme" / "docker-compose.yml"
        check.TEMPLATE = self.root / "blueprints" / "teme" / "template.toml"
        check.README = self.root / "README.md"
        check.LIST = self.root / "compose-hashes.json"
        check.ROOT = self.root
        check.problems.clear()
        try:
            check.main([])
            self.assertEqual([], check.problems)
        finally:
            check.BLUEPRINT, check.TEMPLATE, check.README, check.LIST, check.ROOT = saved
            check.problems.clear()

    def test_says_so_in_the_changelog_under_the_new_version(self) -> None:
        (self.root / "CHANGELOG.md").write_text(f"# Changelog\n\nIntro.\n\n## {self.template} — 2026-11-15\n\n- Old.\n", encoding="utf-8")

        bump.bump("99.0.0", self.root, today="2026-11-21")

        self.assertEqual(
            f"# Changelog\n\nIntro.\n\n## {self.next} — 2026-11-21\n\n- Installs Teme 99.0.0.\n\n## {self.template} — 2026-11-15\n\n- Old.\n",
            (self.root / "CHANGELOG.md").read_text(encoding="utf-8"),
        )

    def test_leaves_a_newer_template_as_it_is(self) -> None:
        before = self.read()

        said = bump.bump("0.0.1", self.root)

        self.assertIn("already", said)
        self.assertEqual(before, self.read())

    def test_orders_versions_as_teme_does(self) -> None:
        ordered = ["1.0.0-alpha.1", "1.0.0-alpha.2", "1.0.0-beta.1", "1.0.0-rc.1", "1.0.0", "1.0.1", "1.1.0-alpha.1", "10.0.0"]

        self.assertEqual(ordered, sorted(reversed(ordered), key=bump.key))

    def test_refuses_a_version_that_isnt_a_releases_and_writes_nothing(self) -> None:
        before = self.read()

        for version in ("latest", "v1.0.0", "1.0", "1.0.0-RC.1", "1.0.0\n", '1.0.0"; x = "y'):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    bump.bump(version, self.root)
                self.assertEqual(before, self.read())


class HashesTest(unittest.TestCase):
    def test_hashes_as_teme_does_whatever_the_line_endings(self) -> None:
        self.assertEqual(hashes.hash_of(b"a: 1\r\nb: 2\r\n\r\n"), hashes.hash_of(b"a: 1\nb: 2\n"))
        self.assertEqual(hashlib.sha256(b"a: 1\nb: 2\n").hexdigest(), hashes.hash_of(b"a: 1\nb: 2"))
        self.assertEqual(hashes.hash_of(b"a: 1 \t\x00\x0b\n"), hashes.hash_of(b"a: 1"))
        self.assertNotEqual(hashes.hash_of(b"a: 1\n"), hashes.hash_of(b"a: 2\n"))

    def test_gives_the_test_vector_teme_checks_too(self) -> None:
        data, expected = hashes.TEST_VECTOR

        self.assertEqual(b"services:\r\n  web: {}\r\n\r\n", data)
        self.assertEqual("78ae680a3841176cc921326a7837fc012f1f21701a4f5a4d6943f9e6c20b8af8", expected)
        self.assertEqual(expected, hashes.hash_of(data))
        self.assertIn(expected, (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"))

    def test_adds_a_hash_once_and_never_removes_one(self) -> None:
        listed = {"format": 1, "current": "a" * 64, "released": ["a" * 64, "b" * 64]}

        added = hashes.add(listed, ["b" * 64, "c" * 64])

        self.assertEqual(["a" * 64, "b" * 64, "c" * 64], added["released"])
        self.assertEqual("a" * 64, added["current"])

    def test_names_the_blueprint_current_and_released(self) -> None:
        root = copy_of_repository()
        blueprint = root / "blueprints" / "teme" / "docker-compose.yml"

        updated = hashes.update({"format": 1, "current": None, "released": ["b" * 64]}, blueprint)

        expected = hashes.hash_of(blueprint.read_bytes())
        self.assertEqual(expected, updated["current"])
        self.assertEqual(["b" * 64, expected], updated["released"])

    def test_the_published_list_names_the_blueprint(self) -> None:
        listed = json.loads((ROOT / "compose-hashes.json").read_text(encoding="utf-8"))

        self.assertEqual(hashes.hash_of(hashes.BLUEPRINT.read_bytes()), listed["current"])
        self.assertIn(listed["current"], listed["released"])


class CheckTest(unittest.TestCase):
    """The checks pass on the repository, and each catches what it is for in a broken copy."""

    def setUp(self) -> None:
        self.root = copy_of_repository()
        self.saved = (check.BLUEPRINT, check.TEMPLATE, check.README, check.LIST, check.ROOT)
        check.BLUEPRINT = self.root / "blueprints" / "teme" / "docker-compose.yml"
        check.TEMPLATE = self.root / "blueprints" / "teme" / "template.toml"
        check.README = self.root / "README.md"
        check.LIST = self.root / "compose-hashes.json"
        check.ROOT = self.root
        check.problems.clear()

    def tearDown(self) -> None:
        check.BLUEPRINT, check.TEMPLATE, check.README, check.LIST, check.ROOT = self.saved
        check.problems.clear()

    def edit(self, path: Path, old: str, new: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")

    def run_check(self) -> list:
        check.main([])
        return list(check.problems)

    def test_passes_on_the_repository(self) -> None:
        self.assertEqual([], self.run_check())

    def test_catches_the_environment_tab_reaching_the_installer(self) -> None:
        self.edit(check.BLUEPRINT, "    installer:\n        <<: *teme\n", "    installer:\n        <<: *teme\n        env_file: *site-settings\n")

        self.assertIn("installer must not read the Environment tab.", self.run_check())

    def test_catches_a_volume_that_loses_its_old_name(self) -> None:
        self.edit(check.BLUEPRINT, "}}_page-cache", "}}_page_cache")

        self.assertTrue(any("page-cache" in sentence for sentence in self.run_check()))

    def test_catches_a_site_secret_reaching_the_installer(self) -> None:
        self.edit(check.BLUEPRINT, "            TEME_EXTENSIONS_ROLE: installer\n", "            TEME_EXTENSIONS_ROLE: installer\n            MEDIA_BUCKET_SECRET_ACCESS_KEY: ${MEDIA_BUCKET_SECRET_ACCESS_KEY:-}\n")

        found = self.run_check()

        self.assertIn("The installer must not receive MEDIA_BUCKET_SECRET_ACCESS_KEY.", found)
        self.assertTrue(any(sentence.startswith("The installer's environment must be the core") for sentence in found))

    def test_catches_the_site_settings_reaching_the_updater(self) -> None:
        self.edit(check.BLUEPRINT, "        environment:\n            <<: *teme-core\n            TEME_IMAGE_REPOSITORY", "        environment:\n            <<: *teme-environment\n            TEME_IMAGE_REPOSITORY")

        self.assertTrue(any(sentence.startswith("The updater's environment must be the core") for sentence in self.run_check()))

    def test_the_environment_tab_is_grouped_with_comments_that_set_nothing(self) -> None:
        template = check.tomllib.loads(check.TEMPLATE.read_text(encoding="utf-8"))
        every = check.template_environment(template)
        settings = check.settings_lines(every)

        self.assertTrue(any(line.startswith("#") for line in every))
        self.assertTrue(all("=" in line and not line.startswith("#") for line in settings))
        self.assertNotIn("MAIL_MAILER", {line.split("=", 1)[0] for line in settings})

    def test_catches_a_comment_after_a_value(self) -> None:
        self.edit(check.TEMPLATE, '"APP_URL=https://${main_domain}",', '"APP_URL=https://${main_domain} # the address",')

        self.assertTrue(any("has a comment after its value" in sentence for sentence in self.run_check()))

    def test_assumes_dokploy_fills_app_name_and_names_the_folders_without_it_too(self) -> None:
        """ASSUMPTION: Dokploy passes the App Name to the template as APP_NAME; the live run checks it. The check
        also holds when Dokploy leaves ${APP_NAME} as it is, through the APP_NAME line Dokploy writes first."""
        template = check.tomllib.loads(check.TEMPLATE.read_text(encoding="utf-8"))
        unfilled = dict(line.split("=", 1) for line in check.settings_lines(check.template_environment(template, app_name=None)))

        self.assertEqual("${APP_NAME}", unfilled["STACK_SLUG"])

        check.check_dokploy_env(template)

        self.assertEqual([], check.problems)

    def test_catches_a_media_setting_left_out(self) -> None:
        self.edit(check.BLUEPRINT, "    MEDIA_BUCKET_ACL: ${MEDIA_BUCKET_ACL:-}\n", "")

        self.assertIn("web must pass MEDIA_BUCKET_ACL, defaulting to empty.", self.run_check())

    def test_catches_a_fixed_limit(self) -> None:
        self.edit(check.BLUEPRINT, "cpus: '${TEME_WEB_CPUS:-1}'", "cpus: '1'")

        self.assertTrue(any(sentence.startswith("web's limits") for sentence in self.run_check()))

    def test_catches_a_compose_file_the_list_doesnt_name(self) -> None:
        self.edit(check.BLUEPRINT, "    web:\n", "    web:\n        init: true\n")

        self.assertTrue(any("run python3 scripts/hashes.py update" in sentence for sentence in self.run_check()))

    def test_catches_a_dropped_hash(self) -> None:
        previous = self.root / "previous.json"
        listed = json.loads(check.LIST.read_text(encoding="utf-8"))
        previous.write_text(json.dumps({**listed, "released": listed["released"] + ["f" * 64]}), encoding="utf-8")

        check.main(["--previous", str(previous)])

        self.assertIn("compose-hashes.json dropped a released hash; a site may still run that file.", check.problems)

    def test_catches_a_setting_the_template_leaves_out(self) -> None:
        self.edit(check.TEMPLATE, '    "DB_PASSWORD=${db_password}",\n', "")

        self.assertIn("template.toml doesn't fill DB_PASSWORD, which the compose file requires.", self.run_check())

    def test_catches_a_description_that_names_another_release(self) -> None:
        self.edit(check.TEMPLATE, 'teme_version = "', 'teme_version = "9')

        self.assertIn("meta.json's description must end with the Teme release template.toml installs.", self.run_check())

    def test_catches_a_changelog_that_doesnt_open_with_the_templates_version(self) -> None:
        self.edit(check.ROOT / "CHANGELOG.md", "## ", "## 9", )

        self.assertIn("CHANGELOG.md's newest heading must be meta.json's version.", self.run_check())


if __name__ == "__main__":
    unittest.main()
