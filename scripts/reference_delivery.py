#!/usr/bin/env python3
"""Build and preflight actual-image attachment handoff for 镜造 specifications."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_attachment_manifest(spec: dict[str, Any]) -> list[dict[str, Any]]:
    inputs = spec.get("inputs") if isinstance(spec.get("inputs"), list) else []
    manifest: list[dict[str, Any]] = []
    for index, item in enumerate(inputs, start=1):
        if not isinstance(item, dict) or item.get("type") != "image":
            continue
        manifest.append(
            {
                "input_id": item.get("id"),
                "image_index": index,
                "role": item.get("role"),
                "source_kind": item.get("source_kind", "unspecified"),
                "source_ref": item.get("source_ref", ""),
                "must_attach": bool(item.get("must_attach", False)),
            }
        )
    return manifest


def build_reference_handoff(spec: dict[str, Any]) -> dict[str, Any]:
    attachments = build_attachment_manifest(spec)
    required = [item for item in attachments if item["must_attach"]]
    return {
        "required_attachment_count": len(required),
        "imagegen_contract": (
            "Pass local_path sources through referenced_image_paths. Pass conversation_image sources through the "
            "smallest num_last_images_to_include that contains every required image. Never replace an attachment "
            "with a prose description. This Skill does not route to post-generation compositing."
            if required
            else "No required image attachment is declared."
        ),
    }


def reference_delivery_warnings(spec: dict[str, Any]) -> list[str]:
    handoff = build_reference_handoff(spec)
    warnings: list[str] = []
    if handoff["required_attachment_count"]:
        warnings.append(
            "Actual image attachments are mandatory for this request; prompt text and image descriptions are not substitutes."
        )
    return warnings


def preflight_reference_delivery(spec: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    attachments = build_attachment_manifest(spec)
    errors: list[str] = []
    runtime_required: list[str] = []
    resolved: list[dict[str, Any]] = []
    for item in attachments:
        entry = dict(item)
        if not item["must_attach"]:
            entry["preflight"] = "optional"
            resolved.append(entry)
            continue
        source_kind = item["source_kind"]
        source_ref = item["source_ref"]
        if source_kind == "local_path":
            source_path = Path(source_ref)
            if not source_path.is_absolute():
                source_path = (base_dir / source_path).resolve()
            entry["resolved_source"] = str(source_path)
            if not source_path.is_file():
                entry["preflight"] = "missing"
                errors.append(f"{item['input_id']}: required local image not found: {source_path}")
            else:
                entry["preflight"] = "ready"
        elif source_kind in {"conversation_image", "remote_url", "platform_asset"}:
            entry["preflight"] = "runtime_required"
            runtime_required.append(str(item["input_id"]))
        else:
            entry["preflight"] = "missing"
            errors.append(f"{item['input_id']}: required attachment has no resolvable source")
        resolved.append(entry)
    return {
        "valid": not errors,
        "errors": errors,
        "runtime_required": runtime_required,
        "attachments": resolved,
        "handoff": build_reference_handoff(spec),
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a visual specification JSON file")
    args = parser.parse_args()
    try:
        with args.spec.open("r", encoding="utf-8") as handle:
            spec = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    if not isinstance(spec, dict):
        print(json.dumps({"valid": False, "errors": ["spec root must be an object"]}, indent=2))
        return 2
    result = preflight_reference_delivery(spec, args.spec.parent)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
