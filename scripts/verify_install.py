#!/usr/bin/env python3
"""Compare installed Skill files and symlinks with a Git release tree."""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from pathlib import Path


class InstallVerificationError(RuntimeError):
    """Raised when an install comparison cannot be completed safely."""


def git_output(source: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(source), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise InstallVerificationError(detail or "Git command failed")
    return result.stdout


def tracked_blobs(source: Path, ref: str):
    raw = git_output(source, "ls-tree", "-rz", "-r", "--full-tree", ref)
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, object_type, object_id = metadata.split()
        if object_type != b"blob":
            continue
        yield (
            encoded_path.decode("utf-8", "surrogateescape"),
            mode.decode("ascii"),
            object_id.decode("ascii"),
        )


def is_runtime_artifact(relative_path: str) -> bool:
    parts = Path(relative_path).parts
    return (
        parts[:1] == (".git",)
        or Path(relative_path).name == ".DS_Store"
        or relative_path.endswith(".pyc")
    )


def resolve_install_root(install: Path) -> Path:
    try:
        resolved = install.resolve(strict=True)
        metadata = resolved.lstat()
    except (OSError, RuntimeError) as exc:
        raise InstallVerificationError("install root is unavailable") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise InstallVerificationError("install root must resolve to a directory")
    return resolved


def parent_path_issue(install: Path, relative_path: str) -> str | None:
    try:
        root_metadata = install.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(root_metadata.st_mode):
        raise InstallVerificationError("install root must not be a symlink")
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise InstallVerificationError("install root must be a directory")

    parent = install
    for part in Path(relative_path).parts[:-1]:
        parent /= part
        try:
            metadata = parent.lstat()
        except FileNotFoundError:
            return None
        if stat.S_ISLNK(metadata.st_mode):
            return "symlink_parent"
        if not stat.S_ISDIR(metadata.st_mode):
            return "parent_type"
    return None


def verify_install(source: Path, install: Path, ref: str) -> dict[str, object]:
    source_commit = git_output(source, "rev-parse", f"{ref}^{{commit}}").decode().strip()
    install = resolve_install_root(install)
    differences: list[dict[str, object]] = []
    tracked_paths: set[str] = set()
    tracked_count = 0
    for relative_path, expected_mode, object_id in tracked_blobs(source, source_commit):
        tracked_count += 1
        tracked_paths.add(relative_path)
        target = install / relative_path
        expected = git_output(source, "cat-file", "blob", object_id)
        issues: list[str] = []
        metadata = None
        parent_issue = parent_path_issue(install, relative_path)
        if parent_issue:
            issues.append(parent_issue)
        else:
            try:
                metadata = target.lstat()
            except FileNotFoundError:
                issues.append("missing")
                metadata = None
        if not issues and metadata is not None:
            expected_symlink = expected_mode == "120000"
            actual_symlink = stat.S_ISLNK(metadata.st_mode)
            if expected_symlink != actual_symlink or (
                not expected_symlink and not stat.S_ISREG(metadata.st_mode)
            ):
                issues.append("type")
            else:
                actual = (
                    os.fsencode(os.readlink(target))
                    if actual_symlink
                    else target.read_bytes()
                )
                if actual != expected:
                    issues.append("content")
                actual_mode = (
                    "120000"
                    if actual_symlink
                    else "100755" if metadata.st_mode & 0o111 else "100644"
                )
                if actual_mode != expected_mode:
                    issues.append("mode")
        if issues:
            differences.append({"issues": issues, "path": relative_path})
    untracked_files = sorted(
        path.relative_to(install).as_posix()
        for path in install.rglob("*")
        if (path.is_file() or path.is_symlink())
        and path.relative_to(install).as_posix() not in tracked_paths
    )
    ignored_runtime_files = [path for path in untracked_files if is_runtime_artifact(path)]
    extra_files = [path for path in untracked_files if not is_runtime_artifact(path)]
    return {
        "status": "match" if not differences and not extra_files else "mismatch",
        "ref": ref,
        "source_commit": source_commit,
        "tracked_files": tracked_count,
        "differences": differences,
        "extra_files": extra_files,
        "ignored_runtime_files": ignored_runtime_files,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify installed Skill files and symlinks against a Git release tree."
    )
    parser.add_argument("source", type=Path, help="source Git repository")
    parser.add_argument("install", type=Path, help="installed Skill directory")
    parser.add_argument("--ref", default="HEAD", help="Git tree to compare (default: HEAD)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        result = verify_install(args.source, args.install, args.ref)
    except (InstallVerificationError, OSError, ValueError) as exc:
        print(f"verify_install: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "match" else 1


if __name__ == "__main__":
    raise SystemExit(main())
