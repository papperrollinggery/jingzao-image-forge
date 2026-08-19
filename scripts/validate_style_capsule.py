#!/usr/bin/env python3
"""Validate a reusable 镜造 Image Forge style capsule."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CAPSULE_SCOPES = {"session", "project", "skill_candidate"}
CAPSULE_STATUSES = {"draft", "validated", "adopted"}
PROFILE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CONTENT_RISK_PATTERNS = (
    ("quoted literal", re.compile(r"[\"“”][^\"“”]{2,}[\"“”]")),
    ("brand or signature term", re.compile(r"\b(?:logo|trademark|signature|watermark|copyright)\b|[©™®]", re.IGNORECASE)),
    (
        "coordinate-like content",
        re.compile(r"\b(?:x_percent|y_percent|width_percent|height_percent)\b|\(\s*[xy]\s*[:=]", re.IGNORECASE),
    ),
)


def _is_allowed(value: Any, allowed: set[Any]) -> bool:
    try:
        return value in allowed
    except TypeError:
        return False


def _require_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected a non-empty string")


def _validate_string_list(value: Any, path: str, errors: list[str], *, required: bool = False) -> None:
    if not isinstance(value, list):
        errors.append(f"{path}: expected a list")
        return
    if required and not value:
        errors.append(f"{path}: expected at least one item")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{path}[{index}]: expected a non-empty string")


def _validate_known_keys(value: dict[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in value:
        if key not in allowed:
            errors.append(f"{path}.{key}: unknown field")


def validate_style_capsule(capsule: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(capsule, dict):
        return ["$: expected a JSON object"]

    _validate_known_keys(
        capsule,
        {
            "style_capsule",
            "id",
            "name",
            "scope",
            "status",
            "adoption_approved",
            "source_summary",
            "visual_rules",
            "inferred_traits",
            "unknowns",
            "transfer_rules",
            "forbidden_transfer",
            "validation",
        },
        "$",
        errors,
    )

    if capsule.get("style_capsule") != "1.0":
        errors.append("$.style_capsule: expected \"1.0\"")
    profile_id = capsule.get("id")
    _require_string(profile_id, "$.id", errors)
    if isinstance(profile_id, str) and profile_id.strip() and PROFILE_ID_RE.match(profile_id) is None:
        errors.append("$.id: use lowercase letters, digits, and single hyphens")
    _require_string(capsule.get("name"), "$.name", errors)
    if not _is_allowed(capsule.get("scope"), CAPSULE_SCOPES):
        errors.append(f"$.scope: expected one of {sorted(CAPSULE_SCOPES)}")
    status = capsule.get("status")
    if not _is_allowed(status, CAPSULE_STATUSES):
        errors.append(f"$.status: expected one of {sorted(CAPSULE_STATUSES)}")
    adoption_approved = capsule.get("adoption_approved", False)
    if not isinstance(adoption_approved, bool):
        errors.append("$.adoption_approved: expected a boolean")
    if status == "adopted" and adoption_approved is not True:
        errors.append("$.adoption_approved: adopted capsules require explicit approval")

    source_summary = capsule.get("source_summary")
    if not isinstance(source_summary, dict):
        errors.append("$.source_summary: expected an object")
    else:
        _validate_known_keys(
            source_summary,
            {"source_count", "raw_images_stored", "provenance"},
            "$.source_summary",
            errors,
        )
        source_count = source_summary.get("source_count")
        if not isinstance(source_count, int) or isinstance(source_count, bool) or source_count <= 0:
            errors.append("$.source_summary.source_count: expected a positive integer")
        if source_summary.get("raw_images_stored") is not False:
            errors.append("$.source_summary.raw_images_stored: expected false; do not embed source images")
        _require_string(source_summary.get("provenance"), "$.source_summary.provenance", errors)

    visual_rules = capsule.get("visual_rules")
    if not isinstance(visual_rules, dict):
        errors.append("$.visual_rules: expected an object")
    else:
        _validate_known_keys(
            visual_rules,
            {
                "medium_behavior",
                "palette_logic",
                "shape_line_language",
                "texture_material_logic",
                "lighting_logic",
                "composition_logic",
                "typography_logic",
                "optics_rendering_logic",
                "motifs",
            },
            "$.visual_rules",
            errors,
        )
        for key in ("medium_behavior", "shape_line_language", "lighting_logic", "optics_rendering_logic"):
            _require_string(visual_rules.get(key), f"$.visual_rules.{key}", errors)
        for key in (
            "palette_logic",
            "texture_material_logic",
            "composition_logic",
            "typography_logic",
            "motifs",
        ):
            _validate_string_list(visual_rules.get(key, []), f"$.visual_rules.{key}", errors)

    _validate_string_list(capsule.get("inferred_traits", []), "$.inferred_traits", errors)
    _validate_string_list(capsule.get("unknowns", []), "$.unknowns", errors)
    _validate_string_list(capsule.get("transfer_rules"), "$.transfer_rules", errors, required=True)
    _validate_string_list(capsule.get("forbidden_transfer"), "$.forbidden_transfer", errors, required=True)

    validation = capsule.get("validation")
    if not isinstance(validation, dict):
        errors.append("$.validation: expected an object")
    else:
        _validate_known_keys(validation, {"prompts", "notes"}, "$.validation", errors)
        prompts = validation.get("prompts", [])
        _validate_string_list(prompts, "$.validation.prompts", errors)
        notes = validation.get("notes", "")
        if not isinstance(notes, str):
            errors.append("$.validation.notes: expected a string")
        if _is_allowed(status, {"validated", "adopted"}):
            if not isinstance(prompts, list) or len(prompts) < 2:
                errors.append("$.validation.prompts: validated or adopted capsules require two transfer tests")
            if not isinstance(notes, str) or not notes.strip():
                errors.append("$.validation.notes: validated or adopted capsules require visual review notes")

    return errors


def lint_style_capsule_content(capsule: Any) -> list[str]:
    if not isinstance(capsule, dict):
        return []
    visual_rules = capsule.get("visual_rules")
    if not isinstance(visual_rules, dict):
        return []
    warnings: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
        elif isinstance(value, str):
            for label, pattern in CONTENT_RISK_PATTERNS:
                if pattern.search(value):
                    warnings.append(f"{path}: possible source-specific {label}; review before adoption")

    walk(visual_rules, "$.visual_rules")
    return warnings


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to a style capsule JSON file")
    args = parser.parse_args()

    try:
        capsule = load_json(args.path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID\n{exc}", file=sys.stderr)
        return 2

    errors = validate_style_capsule(capsule)
    if errors:
        print("INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
