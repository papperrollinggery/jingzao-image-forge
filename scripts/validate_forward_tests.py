#!/usr/bin/env python3
"""Validate auditable, non-pixel forward-test evidence records."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from compile_prompt import compile_spec
    from reference_delivery import (
        CODEX_IMAGEGEN_TARGET,
        preflight_reference_delivery,
        validate_execution_receipt,
    )
    from validate_spec import load_json
except ModuleNotFoundError:  # Support `python -m scripts.validate_forward_tests`.
    from scripts.compile_prompt import compile_spec
    from scripts.reference_delivery import (
        CODEX_IMAGEGEN_TARGET,
        preflight_reference_delivery,
        validate_execution_receipt,
    )
    from scripts.validate_spec import load_json


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_RECEIPT_ALLOWED_KEYS = {
    "receipt_version",
    "mechanism",
    "sent_input_ids",
    "sent_count",
    "tool_call_id_sha256",
    "output_ref",
    "raw_output_sha256",
    "execution_prompt_sha256",
    "execution_prompt_note",
    "actual_output_dimensions",
    "review",
}
MANIFEST_ALLOWED_KEYS = {
    "forward_test_manifest",
    "review_policy",
    "prompt_hash_policy",
    "receipt_policy",
    "cases",
}
CASE_ALLOWED_KEYS = {
    "case_id",
    "status",
    "mode",
    "scenario",
    "tool",
    "model",
    "prompt_source",
    "prompt_sha256",
    "output",
    "output_sha256",
    "execution_receipt",
    "review_date",
    "review",
}
PROMPT_SOURCE_ALLOWED_KEYS = {
    "compiled_spec": {"type", "spec", "platform", "style_capsule"},
    "capsule_validation_prompt": {"type", "style_capsule", "prompt_index"},
}
PUBLIC_RECEIPT_SENSITIVE_VALUE_RE = re.compile(
    r"(?:/Users/|/home/|/tmp/|/private/|/var/|/Volumes/|\b(?:api|access|auth|xsec)?[_ -]?token\b|session[-_:]|thread[-_:]|cursor[-_:])",
    re.IGNORECASE,
)
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
WINDOWS_DRIVE_ANY_RE = re.compile(r"(?:^|[\s\"'=])[A-Za-z]:[\\/]")
URI_SCHEME_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://")
POSIX_ABSOLUTE_RE = re.compile(r"(?<![A-Za-z0-9._-])/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+")
PUBLIC_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def _require_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected a non-empty string")


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or WINDOWS_DRIVE_RE.match(value) or URI_SCHEME_RE.search(value) or "\\" in value:
        raise ValueError(f"public path must be repository-relative: {value!r}")
    if ".." in path.parts:
        raise ValueError(f"public path must not contain parent traversal: {value!r}")
    root_resolved = root.resolve()
    resolved = (root_resolved / path).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"public path escapes repository root: {value!r}") from exc
    return resolved


def _scan_public_strings(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if (
            WINDOWS_DRIVE_ANY_RE.search(value)
            or value.startswith("\\\\")
            or "\\" in value
            or URI_SCHEME_RE.search(value)
            or POSIX_ABSOLUTE_RE.search(value)
            or PUBLIC_RECEIPT_SENSITIVE_VALUE_RE.search(value)
        ):
            errors.append(f"{path}: contains a local/runtime identifier or URI")
        return errors
    if isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_scan_public_strings(item, f"{path}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(_scan_public_strings(item, f"{path}.{key}"))
    return errors


def _validate_prompt_source(prompt_source: Any, path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(prompt_source, dict):
        return [f"{path}: expected an object"]
    source_type = prompt_source.get("type")
    if not isinstance(source_type, str):
        return [f"{path}.type: expected a string"]
    allowed = PROMPT_SOURCE_ALLOWED_KEYS.get(source_type)
    if allowed is None:
        return [f"{path}.type: unsupported value"]
    unexpected = sorted(set(prompt_source).difference(allowed))
    if unexpected:
        errors.append(f"{path}: unknown fields {unexpected}")
    if source_type == "compiled_spec":
        _require_string(prompt_source.get("spec"), f"{path}.spec", errors)
        platform = prompt_source.get("platform", "openai")
        if not isinstance(platform, str) or platform not in {"openai", "flux", "midjourney", "generic"}:
            errors.append(f"{path}.platform: unsupported value")
        capsule = prompt_source.get("style_capsule")
        if capsule is not None:
            _require_string(capsule, f"{path}.style_capsule", errors)
    else:
        _require_string(prompt_source.get("style_capsule"), f"{path}.style_capsule", errors)
        prompt_index = prompt_source.get("prompt_index")
        if isinstance(prompt_index, bool) or not isinstance(prompt_index, int) or prompt_index < 0:
            errors.append(f"{path}.prompt_index: expected a non-negative integer")
    errors.extend(_scan_public_strings(prompt_source, path))
    return errors


def _expected_prompt(case: dict[str, Any], root: Path) -> str:
    prompt_source = case.get("prompt_source")
    if not isinstance(prompt_source, dict):
        raise TypeError("prompt_source must be an object")
    source_type = prompt_source.get("type")
    if source_type == "compiled_spec":
        spec = load_json(_resolve(root, str(prompt_source.get("spec"))))
        capsule_path = prompt_source.get("style_capsule")
        capsule = load_json(_resolve(root, str(capsule_path))) if capsule_path else None
        return compile_spec(spec, str(prompt_source.get("platform", "openai")), capsule)["prompt"]
    if source_type == "capsule_validation_prompt":
        capsule = load_json(_resolve(root, str(prompt_source.get("style_capsule"))))
        index = prompt_source.get("prompt_index")
        return capsule["validation"]["prompts"][index]
    raise ValueError(f"unsupported prompt_source type: {source_type!r}")


def _required_attachment_context(case: dict[str, Any], root: Path) -> tuple[Path | None, dict[str, Any] | None, int]:
    prompt_source = case.get("prompt_source")
    if not isinstance(prompt_source, dict) or prompt_source.get("type") != "compiled_spec":
        return None, None, 0
    spec_path = _resolve(root, str(prompt_source.get("spec")))
    spec = load_json(spec_path)
    inputs = spec.get("inputs") if isinstance(spec.get("inputs"), list) else []
    required_count = sum(
        1
        for item in inputs
        if isinstance(item, dict) and item.get("type") == "image" and item.get("must_attach") is True
    )
    return spec_path, spec, required_count


def _validate_public_receipt(receipt: Any, path: str, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return [f"{path}: expected an object"]
    unexpected = sorted(set(receipt).difference(PUBLIC_RECEIPT_ALLOWED_KEYS))
    if unexpected:
        errors.append(f"{path}: unsupported or sensitive public keys {unexpected}")
    if receipt.get("receipt_version") != "1.0":
        errors.append(f"{path}.receipt_version: expected \"1.0\"")
    if receipt.get("mechanism") not in {"none", "referenced_image_paths", "num_last_images_to_include"}:
        errors.append(f"{path}.mechanism: unsupported value")
    sent_input_ids = receipt.get("sent_input_ids")
    if not isinstance(sent_input_ids, list) or any(not isinstance(item, str) or not item for item in sent_input_ids):
        errors.append(f"{path}.sent_input_ids: expected non-empty strings")
    sent_count = receipt.get("sent_count")
    if isinstance(sent_count, bool) or not isinstance(sent_count, int) or sent_count < 0:
        errors.append(f"{path}.sent_count: expected a non-negative integer")
    tool_hash = receipt.get("tool_call_id_sha256")
    if not isinstance(tool_hash, str) or SHA256_RE.fullmatch(tool_hash) is None:
        errors.append(f"{path}.tool_call_id_sha256: expected lowercase SHA-256")
    output_ref = receipt.get("output_ref")
    if not isinstance(output_ref, str) or not output_ref:
        errors.append(f"{path}.output_ref: expected a public repository-relative path")
    else:
        try:
            resolved_output = _resolve(root, output_ref)
        except ValueError as exc:
            errors.append(f"{path}.output_ref: {exc}")
        else:
            if resolved_output.suffix.lower() not in PUBLIC_IMAGE_SUFFIXES:
                errors.append(f"{path}.output_ref: expected an image path")
    for key in ("raw_output_sha256", "execution_prompt_sha256"):
        value = receipt.get(key)
        if value is not None and (not isinstance(value, str) or SHA256_RE.fullmatch(value) is None):
            errors.append(f"{path}.{key}: expected lowercase SHA-256")
    dimensions = receipt.get("actual_output_dimensions")
    if dimensions is not None and (
        not isinstance(dimensions, str) or re.fullmatch(r"[1-9]\d*x[1-9]\d*", dimensions) is None
    ):
        errors.append(f"{path}.actual_output_dimensions: expected WIDTHxHEIGHT")
    for key in ("review", "execution_prompt_note"):
        value = receipt.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{path}.{key}: expected a non-empty string")
    for key, value in receipt.items():
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, (dict, list)):
                errors.append(f"{path}.{key}: nested public receipt values are not allowed")
    errors.extend(_scan_public_strings(receipt, path))
    return errors


def validate_forward_test_manifest(manifest: Any, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["$: expected an object"]
    unexpected_manifest_keys = sorted(set(manifest).difference(MANIFEST_ALLOWED_KEYS))
    if unexpected_manifest_keys:
        errors.append(f"$: unknown fields {unexpected_manifest_keys}")
    errors.extend(_scan_public_strings(manifest, "$"))
    if manifest.get("forward_test_manifest") != "1.0":
        errors.append("$.forward_test_manifest: expected \"1.0\"")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) < 5:
        return [*errors, "$.cases: expected at least five evidence cases"]
    case_ids: set[str] = set()
    for index, case in enumerate(cases):
        path = f"$.cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{path}: expected an object")
            continue
        unexpected_case_keys = sorted(set(case).difference(CASE_ALLOWED_KEYS))
        if unexpected_case_keys:
            errors.append(f"{path}: unknown fields {unexpected_case_keys}")
        for key in ("case_id", "status", "mode", "scenario", "tool", "model", "output", "review_date", "review"):
            _require_string(case.get(key), f"{path}.{key}", errors)
        errors.extend(_validate_prompt_source(case.get("prompt_source"), f"{path}.prompt_source"))
        case_id = case.get("case_id")
        if isinstance(case_id, str):
            if case_id in case_ids:
                errors.append(f"{path}.case_id: duplicate {case_id!r}")
            case_ids.add(case_id)
        if case.get("status") not in {"passed", "failed", "not_proven"}:
            errors.append(f"{path}.status: expected passed, failed, or not_proven")
        output = case.get("output")
        try:
            output_path = _resolve(root, output) if isinstance(output, str) and output else None
        except ValueError as exc:
            output_path = None
            errors.append(f"{path}.output: {exc}")
        if output_path is not None and not output_path.is_file():
            errors.append(f"{path}.output: file does not exist")
        if output_path is not None and output_path.suffix.lower() not in PUBLIC_IMAGE_SUFFIXES:
            errors.append(f"{path}.output: expected an image file")
        output_hash = case.get("output_sha256")
        if not isinstance(output_hash, str) or SHA256_RE.fullmatch(output_hash) is None:
            errors.append(f"{path}.output_sha256: expected lowercase SHA-256")
        elif output_path is not None and output_path.is_file():
            actual_output_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
            if actual_output_hash != output_hash:
                errors.append(f"{path}.output_sha256: expected current hash {actual_output_hash}")
        recorded_hash = case.get("prompt_sha256")
        if not isinstance(recorded_hash, str) or SHA256_RE.fullmatch(recorded_hash) is None:
            errors.append(f"{path}.prompt_sha256: expected lowercase SHA-256")
            continue
        try:
            prompt = _expected_prompt(case, root)
        except (KeyError, IndexError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path}.prompt_source: {exc}")
            continue
        actual_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if actual_hash != recorded_hash:
            errors.append(f"{path}.prompt_sha256: expected current hash {actual_hash}")

        try:
            spec_path, spec, required_attachment_count = _required_attachment_context(case, root)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path}.prompt_source: {exc}")
            continue
        receipt_ref = case.get("execution_receipt")
        if receipt_ref is None:
            if required_attachment_count:
                errors.append(
                    f"{path}.execution_receipt: required for {required_attachment_count} must_attach image input(s)"
                )
            continue
        if not isinstance(receipt_ref, str) or not receipt_ref.strip():
            errors.append(f"{path}.execution_receipt: expected a non-empty path")
            continue
        if spec_path is None or spec is None:
            errors.append(f"{path}.execution_receipt: requires a compiled_spec prompt source")
            continue
        try:
            receipt_path = _resolve(root, receipt_ref)
            if receipt_path.suffix.lower() != ".json":
                errors.append(f"{path}.execution_receipt: expected a JSON file")
            receipt = load_json(receipt_path)
            errors.extend(_validate_public_receipt(receipt, f"{path}.execution_receipt", root))
            preflight = preflight_reference_delivery(spec, spec_path.parent, target=CODEX_IMAGEGEN_TARGET)
            if not preflight.get("valid"):
                errors.extend(f"{path}.execution_receipt preflight: {item}" for item in preflight.get("errors", []))
                continue
            receipt_errors = validate_execution_receipt(preflight["imagegen_call_plan"], receipt)
            errors.extend(f"{path}.execution_receipt: {item}" for item in receipt_errors)
            if receipt.get("output_ref") != output:
                errors.append(f"{path}.execution_receipt: output_ref does not match case output")
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path}.execution_receipt: {exc}")
    return errors


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        manifest = load_json(args.manifest)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID\n{exc}", file=sys.stderr)
        return 2
    root = args.manifest.resolve().parents[1]
    errors = validate_forward_test_manifest(manifest, root)
    if errors:
        print("INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
