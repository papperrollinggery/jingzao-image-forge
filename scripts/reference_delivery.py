#!/usr/bin/env python3
"""Build and preflight actual-image attachment handoff for 镜造 specifications."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PORTABLE_TARGET = "portable"
CODEX_IMAGEGEN_TARGET = "codex_imagegen"
REFERENCE_TARGETS = {PORTABLE_TARGET, CODEX_IMAGEGEN_TARGET}

# Verified against the bundled Codex imagegen Skill on 2026-08-19. The target
# accepts at most five reference/edit images and requires exactly one attachment
# mechanism: local referenced_image_paths or the recent conversation-image window.
CODEX_IMAGEGEN_MAX_REFERENCES = 5


def build_attachment_manifest(spec: dict[str, Any]) -> list[dict[str, Any]]:
    inputs = spec.get("inputs") if isinstance(spec.get("inputs"), list) else []
    manifest: list[dict[str, Any]] = []
    image_index = 0
    for item in inputs:
        if not isinstance(item, dict) or item.get("type") != "image":
            continue
        image_index += 1
        manifest.append(
            {
                "input_id": item.get("id"),
                "image_index": image_index,
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


def build_imagegen_call_plan(
    spec: dict[str, Any],
    *,
    conversation_window_confirmed: bool = False,
) -> dict[str, Any]:
    attachments = build_attachment_manifest(spec)
    required = [item for item in attachments if item["must_attach"]]
    input_ids = [str(item["input_id"]) for item in required]
    source_kinds = {str(item["source_kind"]) for item in required}
    errors: list[str] = []
    mechanism = "none"
    argument: list[str] | int | None = None

    if len(required) > CODEX_IMAGEGEN_MAX_REFERENCES:
        errors.append(
            f"Codex ImageGen accepts at most {CODEX_IMAGEGEN_MAX_REFERENCES} reference/edit images; "
            f"{len(required)} are required"
        )

    unsupported = source_kinds.intersection({"remote_url", "platform_asset", "unspecified"})
    if unsupported:
        errors.append(
            "Codex ImageGen requires remote_url/platform_asset sources to be materialized as local_path, "
            "and unspecified sources to be resolved, before execution"
        )

    has_local = "local_path" in source_kinds
    has_conversation = "conversation_image" in source_kinds
    if has_local and has_conversation:
        errors.append(
            "Codex ImageGen cannot combine referenced_image_paths with num_last_images_to_include in one call"
        )
    elif has_local:
        mechanism = "referenced_image_paths"
        argument = [str(item["source_ref"]) for item in required]
    elif has_conversation:
        mechanism = "num_last_images_to_include"
        argument = len(required)
        if not conversation_window_confirmed:
            errors.append(
                "conversation-image selection is a best-effort recent window; confirm immediately before execution "
                "that the latest required images are contiguous and no newer unrelated image is included"
            )

    return {
        "target": CODEX_IMAGEGEN_TARGET,
        "status": "ready" if not errors else "blocked",
        "mechanism": mechanism,
        "required_input_ids": input_ids,
        "expected_attachment_count": len(required),
        "argument": argument,
        "conversation_window_confirmed": bool(conversation_window_confirmed),
        "capability": {
            "max_reference_images": CODEX_IMAGEGEN_MAX_REFERENCES,
            "verified_on": "2026-08-19",
        },
        "errors": errors,
    }


def validate_execution_receipt(call_plan: dict[str, Any], receipt: Any) -> list[str]:
    errors: list[str] = []
    if call_plan.get("status") != "ready":
        errors.append("imagegen call plan is not ready")
    if not isinstance(receipt, dict):
        return [*errors, "execution receipt must be an object"]

    expected_ids = call_plan.get("required_input_ids", [])
    sent_ids = receipt.get("sent_input_ids")
    if sent_ids != expected_ids:
        errors.append(f"sent_input_ids do not match expected input order: {expected_ids}")
    if receipt.get("sent_count") != call_plan.get("expected_attachment_count"):
        errors.append("sent_count does not match expected_attachment_count")
    if receipt.get("mechanism") != call_plan.get("mechanism"):
        errors.append("receipt mechanism does not match the call plan")
    tool_call_id = receipt.get("tool_call_id")
    tool_call_id_sha256 = receipt.get("tool_call_id_sha256")
    has_tool_call_id = isinstance(tool_call_id, str) and bool(tool_call_id.strip())
    has_tool_call_hash = (
        isinstance(tool_call_id_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", tool_call_id_sha256) is not None
    )
    if not has_tool_call_id and not has_tool_call_hash:
        errors.append("execution receipt requires non-empty tool_call_id or lowercase tool_call_id_sha256")
    if not isinstance(receipt.get("output_ref"), str) or not receipt["output_ref"].strip():
        errors.append("execution receipt requires non-empty output_ref")
    return errors


def reference_delivery_warnings(spec: dict[str, Any]) -> list[str]:
    handoff = build_reference_handoff(spec)
    warnings: list[str] = []
    if handoff["required_attachment_count"]:
        warnings.append(
            "Actual image attachments are mandatory for this request; prompt text and image descriptions are not substitutes."
        )
    return warnings


def preflight_reference_delivery(
    spec: dict[str, Any],
    base_dir: Path,
    *,
    target: str = PORTABLE_TARGET,
    conversation_window_confirmed: bool = False,
) -> dict[str, Any]:
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
    call_plan = (
        build_imagegen_call_plan(spec, conversation_window_confirmed=conversation_window_confirmed)
        if target == CODEX_IMAGEGEN_TARGET
        else None
    )
    if call_plan is not None:
        if call_plan["mechanism"] == "referenced_image_paths":
            call_plan["argument"] = [
                item["resolved_source"]
                for item in resolved
                if item.get("must_attach") and item.get("preflight") == "ready" and "resolved_source" in item
            ]
        errors.extend(call_plan["errors"])
    return {
        "target": target,
        "valid": not errors,
        "errors": errors,
        "runtime_required": runtime_required,
        "attachments": resolved,
        "handoff": build_reference_handoff(spec),
        "imagegen_call_plan": call_plan,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a visual specification JSON file")
    parser.add_argument("--target", choices=sorted(REFERENCE_TARGETS), default=PORTABLE_TARGET)
    parser.add_argument(
        "--confirm-conversation-window",
        action="store_true",
        help="Confirm at execution time that the latest conversation images exactly cover the required set",
    )
    parser.add_argument("--receipt", type=Path, help="Optional execution receipt JSON to verify against the call plan")
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
    result = preflight_reference_delivery(
        spec,
        args.spec.parent,
        target=args.target,
        conversation_window_confirmed=args.confirm_conversation_window,
    )
    if args.receipt:
        try:
            with args.receipt.open("r", encoding="utf-8") as handle:
                receipt = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            result["receipt_valid"] = False
            result["receipt_errors"] = [str(exc)]
        else:
            plan = result.get("imagegen_call_plan")
            receipt_errors = (
                validate_execution_receipt(plan, receipt)
                if isinstance(plan, dict)
                else ["--receipt requires --target codex_imagegen"]
            )
            result["receipt_valid"] = not receipt_errors
            result["receipt_errors"] = receipt_errors
        if not result.get("receipt_valid", False):
            result["valid"] = False
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
