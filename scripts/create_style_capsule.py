#!/usr/bin/env python3
"""Export a source-image-free reusable style capsule from a learn_style specification."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

try:
    from validate_spec import load_json, validate_spec
    from validate_style_capsule import (
        lint_style_capsule_content,
        validate_style_capsule,
    )
except ModuleNotFoundError:  # Support `python -m scripts.create_style_capsule` from the repository root.
    from scripts.validate_spec import load_json, validate_spec
    from scripts.validate_style_capsule import (
        lint_style_capsule_content,
        validate_style_capsule,
    )


def create_style_capsule(spec: dict[str, Any]) -> dict[str, Any]:
    errors = validate_spec(spec)
    if errors:
        raise ValueError("Specification validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    if spec.get("mode") != "learn_style":
        raise ValueError("Specification mode must be 'learn_style'")

    learning = spec["style_learning"]
    source_input_ids = learning["source_input_ids"]
    capsule = {
        "style_capsule": "1.0",
        "id": learning["profile_id"],
        "name": learning["profile_name"],
        "scope": learning.get("scope", "session"),
        "status": learning.get("status", "draft"),
        "adoption_approved": learning.get("adoption_approved", False),
        "source_summary": {
            "source_count": len(source_input_ids),
            "raw_images_stored": False,
            "provenance": learning.get(
                "provenance",
                "Observed from supplied reference images; raw images are not embedded in this capsule.",
            ),
        },
        "visual_rules": copy.deepcopy(learning["observed"]),
        "inferred_traits": copy.deepcopy(learning.get("inferred_traits", [])),
        "unknowns": copy.deepcopy(learning.get("unknowns", [])),
        "transfer_rules": copy.deepcopy(learning.get("transfer_rules", [])),
        "forbidden_transfer": copy.deepcopy(learning.get("forbidden_transfer", [])),
        "validation": {
            "prompts": copy.deepcopy(learning.get("validation_prompts", [])),
            "notes": learning.get("verification_notes", ""),
        },
    }
    capsule_errors = validate_style_capsule(capsule)
    if capsule_errors:
        raise ValueError("Style capsule validation failed:\n" + "\n".join(f"- {error}" for error in capsule_errors))
    return capsule


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a validated learn_style specification")
    parser.add_argument("--output", type=Path, help="Optional output path; stdout is used when omitted")
    args = parser.parse_args()

    try:
        raw_spec = load_json(args.spec)
        if not isinstance(raw_spec, dict):
            raise TypeError("Specification root must be an object")
        capsule = create_style_capsule(raw_spec)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = json.dumps(capsule, ensure_ascii=False, indent=2) + "\n"
    for warning in lint_style_capsule_content(capsule):
        print(f"WARNING: {warning}", file=sys.stderr)
    if args.output is None:
        print(payload, end="")
        return 0
    if not args.output.parent.is_dir():
        print(f"Output directory does not exist: {args.output.parent}", file=sys.stderr)
        return 2
    args.output.write_text(payload, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
