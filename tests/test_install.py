"""Regression tests for release-to-install payload verification."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY_INSTALL = ROOT / "scripts" / "verify_install.py"


def _load_verifier():
    spec = importlib.util.spec_from_file_location("install_verifier", VERIFY_INSTALL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


install_verifier = _load_verifier()


class InstallVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        base = Path(self.temp_dir.name)
        self.source = base / "source"
        self.install = base / "install"
        self.source.mkdir()
        (self.source / "SKILL.md").write_text(
            "---\nname: fixture\ndescription: fixture\n---\n\n# Fixture\n",
            encoding="utf-8",
        )
        scripts = self.source / "scripts"
        scripts.mkdir()
        tool = scripts / "tool.py"
        tool.write_text("#!/usr/bin/env python3\nprint('ok')\n", encoding="utf-8")
        tool.chmod(0o755)
        self._git("init", "-q")
        self._git("add", "SKILL.md", "scripts/tool.py")
        self._git(
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "fixture",
        )
        shutil.copytree(self.source, self.install, ignore=shutil.ignore_patterns(".git"))

    def _git(self, *args: str):
        subprocess.run(
            ["git", *args],
            cwd=self.source,
            check=True,
            capture_output=True,
            text=True,
        )

    def _verify(self, ref: str = "HEAD", install: Path | None = None):
        return subprocess.run(
            [
                sys.executable,
                str(VERIFY_INSTALL),
                str(self.source),
                str(install or self.install),
                "--ref",
                ref,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_reports_content_drift(self):
        self.assertTrue(VERIFY_INSTALL.is_file(), "install verifier is missing")
        (self.install / "SKILL.md").write_text("drifted\n", encoding="utf-8")

        result = self._verify()

        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("mismatch", payload["status"])
        self.assertEqual(
            [{"issues": ["content"], "path": "SKILL.md"}],
            payload["differences"],
        )

    def test_reports_executable_mode_drift(self):
        (self.install / "scripts" / "tool.py").chmod(0o644)

        result = self._verify()

        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [{"issues": ["mode"], "path": "scripts/tool.py"}],
            payload["differences"],
        )

    def test_reports_untracked_payload_files(self):
        (self.install / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")

        result = self._verify()

        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(["unexpected.txt"], payload["extra_files"])

    def test_matching_install_passes(self):
        result = self._verify()

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.source, text=True
        ).strip()
        self.assertEqual("match", payload["status"])
        self.assertIn("source_commit", payload)
        self.assertEqual(source_commit, payload["source_commit"])
        self.assertEqual([], payload["differences"])
        self.assertEqual([], payload["extra_files"])

    def test_comparison_tree_is_pinned_to_the_resolved_commit(self):
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.source, text=True
        ).strip()
        observed_refs: list[str] = []
        original = install_verifier.tracked_blobs

        def record_ref(source: Path, ref: str):
            observed_refs.append(ref)
            return original(source, ref)

        install_verifier.tracked_blobs = record_ref
        self.addCleanup(setattr, install_verifier, "tracked_blobs", original)

        result = install_verifier.verify_install(self.source, self.install, "HEAD")

        self.assertEqual("match", result["status"])
        self.assertEqual([source_commit], observed_refs)

    def test_reports_missing_tracked_file(self):
        (self.install / "SKILL.md").unlink()

        result = self._verify()

        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [{"issues": ["missing"], "path": "SKILL.md"}],
            payload["differences"],
        )

    def test_runtime_cache_files_do_not_count_as_payload_drift(self):
        cache = self.install / "scripts" / "__pycache__"
        cache.mkdir()
        (cache / "tool.cpython-314.pyc").write_bytes(b"runtime cache")
        (self.install / ".DS_Store").write_bytes(b"finder metadata")

        result = self._verify()

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([], payload["extra_files"])
        self.assertEqual(
            [".DS_Store", "scripts/__pycache__/tool.cpython-314.pyc"],
            payload["ignored_runtime_files"],
        )

    def test_non_pyc_file_inside_pycache_is_not_ignored(self):
        cache = self.install / "scripts" / "__pycache__"
        cache.mkdir()
        (cache / "unexpected.sh").write_text("echo unexpected\n", encoding="utf-8")

        result = self._verify()

        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(["scripts/__pycache__/unexpected.sh"], payload["extra_files"])

    def test_invalid_git_ref_returns_clean_error(self):
        result = self._verify("missing-release-ref")

        self.assertEqual(2, result.returncode)
        self.assertIn("verify_install:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual("", result.stdout)

    def test_regular_payload_replaced_by_symlink_is_rejected(self):
        expected = (self.install / "SKILL.md").read_bytes()
        outside = Path(self.temp_dir.name) / "outside-skill.md"
        outside.write_bytes(expected)
        (self.install / "SKILL.md").unlink()
        (self.install / "SKILL.md").symlink_to(outside)

        result = self._verify()

        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [{"issues": ["type"], "path": "SKILL.md"}],
            payload["differences"],
        )

    def test_symlinked_parent_directory_is_rejected_without_reading_through_it(self):
        outside = Path(self.temp_dir.name) / "outside-scripts"
        outside.mkdir()
        (outside / "tool.py").write_bytes(
            (self.install / "scripts" / "tool.py").read_bytes()
        )
        shutil.rmtree(self.install / "scripts")
        (self.install / "scripts").symlink_to(outside, target_is_directory=True)

        result = self._verify()

        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn(
            {"issues": ["symlink_parent"], "path": "scripts/tool.py"},
            payload["differences"],
        )

    def test_explicit_symlink_install_root_is_canonicalized(self):
        alias = Path(self.temp_dir.name) / "install-alias"
        alias.symlink_to(self.install, target_is_directory=True)

        result = self._verify(install=alias)

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("match", payload["status"])


if __name__ == "__main__":
    unittest.main()
