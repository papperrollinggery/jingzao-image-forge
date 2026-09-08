#!/usr/bin/env python3
"""Validate and project a reference-observation profile into existing spec prose."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

try:
    from validate_spec import validate_spec
except ModuleNotFoundError:  # Support `python -m scripts.reference_profile` from the repository root.
    from scripts.validate_spec import validate_spec


PROFILE_VERSION = "1.0"
FACET_IDS = {
    "face_design",
    "hair",
    "makeup",
    "expression",
    "gaze",
    "pose",
    "action",
    "body",
    "wardrobe",
    "camera",
    "lighting",
    "palette",
    "surface",
    "environment",
}
EVIDENCE_VALUES = {"observed", "partial", "unknown", "not_applicable"}
DECISION_VALUES = {"preserve", "adapt", "omit", "unknown", "not_applicable"}
PROFILE_KEYS = {"reference_profile", "id", "reference_mode", "source_ids", "facets"}
FACET_KEYS = {"id", "source_ids", "evidence", "observation", "decision", "prompt", "reason", "review_check"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _known_keys(value: Any, allowed: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected an object")
        return
    extras = sorted(set(value).difference(allowed))
    if extras:
        errors.append(f"{path}: unknown fields {extras}")
    missing = sorted(allowed.difference(value))
    if missing:
        errors.append(f"{path}: missing fields {missing}")


def _is_allowed_string(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _contains_exact_clause(summary: str, prompt: str) -> bool:
    """Match a whole prior projection line, never an arbitrary substring."""
    normalized = prompt.strip()
    return bool(normalized) and any(line.strip() == normalized for line in summary.splitlines())


def validate_reference_profile(profile: Any) -> list[str]:
    """Return contract errors for a reference profile without mutating it."""
    errors: list[str] = []
    if not isinstance(profile, dict):
        return ["$: expected a JSON object"]
    _known_keys(profile, PROFILE_KEYS, "$", errors)

    if profile.get("reference_profile") != PROFILE_VERSION:
        errors.append(f'$.reference_profile: expected "{PROFILE_VERSION}"')
    profile_id = profile.get("id")
    if not _nonempty_string(profile_id) or SLUG_RE.fullmatch(profile_id) is None:
        errors.append("$.id: expected a non-empty lowercase slug")
    if not _is_allowed_string(profile.get("reference_mode"), {"attached", "text_transfer"}):
        errors.append('$.reference_mode: expected "attached" or "text_transfer"')

    source_ids = profile.get("source_ids")
    valid_source_ids: list[str] = []
    if not isinstance(source_ids, list) or not source_ids:
        errors.append("$.source_ids: expected a non-empty list")
    elif any(not _nonempty_string(item) for item in source_ids):
        errors.append("$.source_ids: expected non-empty strings")
    elif len(set(source_ids)) != len(source_ids):
        errors.append("$.source_ids: duplicate source ids are not allowed")
    else:
        valid_source_ids = source_ids

    facets = profile.get("facets")
    if not isinstance(facets, list):
        return [*errors, "$.facets: expected a list"]
    facet_ids: list[str] = []
    for index, facet in enumerate(facets):
        path = f"$.facets[{index}]"
        _known_keys(facet, FACET_KEYS, path, errors)
        if not isinstance(facet, dict):
            continue
        facet_id = facet.get("id")
        if not _is_allowed_string(facet_id, FACET_IDS):
            errors.append(f"{path}.id: unsupported facet")
        else:
            facet_ids.append(facet_id)
        evidence = facet.get("evidence")
        decision = facet.get("decision")
        if not _is_allowed_string(evidence, EVIDENCE_VALUES):
            errors.append(f"{path}.evidence: unsupported value")
        if not _is_allowed_string(decision, DECISION_VALUES):
            errors.append(f"{path}.decision: unsupported value")
        for field in ("observation", "prompt", "reason", "review_check"):
            if not isinstance(facet.get(field), str):
                errors.append(f"{path}.{field}: expected a string")

        facet_sources = facet.get("source_ids")
        if not isinstance(facet_sources, list) or any(not _nonempty_string(item) for item in facet_sources):
            errors.append(f"{path}.source_ids: expected a list of non-empty strings")
        elif len(set(facet_sources)) != len(facet_sources):
            errors.append(f"{path}.source_ids: duplicate source ids are not allowed")
        elif any(item not in valid_source_ids for item in facet_sources):
            errors.append(f"{path}.source_ids: must be a subset of $.source_ids")

        observation = facet.get("observation")
        prompt = facet.get("prompt")
        reason = facet.get("reason")
        review_check = facet.get("review_check")
        if _is_allowed_string(evidence, {"observed", "partial"}) and not _nonempty_string(observation):
            errors.append(f"{path}.observation: required for observed or partial evidence")
        if _is_allowed_string(evidence, {"observed", "partial"}) and not facet_sources:
            errors.append(f"{path}.source_ids: required for observed or partial evidence")
        if evidence == "unknown" and decision == "preserve":
            errors.append(f"{path}: unknown evidence cannot be preserved")
        if evidence == "unknown" and decision == "adapt":
            errors.append(f"{path}: unknown evidence cannot be adapted; put target-only design in the base spec")
        if evidence == "not_applicable" and decision != "not_applicable":
            errors.append(f"{path}: not_applicable evidence requires not_applicable decision")
        if _is_allowed_string(decision, {"preserve", "adapt"}) and not _nonempty_string(prompt):
            errors.append(f"{path}.prompt: required for preserve or adapt")
        if _is_allowed_string(decision, {"preserve", "adapt"}) and not _nonempty_string(review_check):
            errors.append(f"{path}.review_check: required for preserve or adapt")
        if _is_allowed_string(decision, {"omit", "unknown", "not_applicable"}) and _nonempty_string(prompt):
            errors.append(f"{path}.prompt: must be empty when not adopted")
        if decision == "adapt" and not _nonempty_string(reason):
            errors.append(f"{path}.reason: required for adapt")
        if decision == "unknown" and not _nonempty_string(reason):
            errors.append(f"{path}.reason: required for unknown")
        if decision == "omit" and not _nonempty_string(reason):
            errors.append(f"{path}.reason: required for omit")

    if len(facet_ids) != len(set(facet_ids)):
        errors.append("$.facets: facet ids must be unique")
    missing_facets = sorted(FACET_IDS.difference(facet_ids))
    if missing_facets:
        errors.append(f"$.facets: missing required facets {missing_facets}")
    extra_count = len(facets) - len(facet_ids)
    if extra_count or len(facets) != len(FACET_IDS):
        errors.append(f"$.facets: expected exactly {len(FACET_IDS)} unique facets")
    return errors


def _validate_spec_for_profile(spec: Any, profile: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise TypeError("spec: expected an object")
    if not _nonempty_string(spec.get("intent")):
        raise ValueError("spec.intent: expected a non-empty string")
    if profile["reference_mode"] != "attached":
        return
    inputs = spec.get("inputs")
    if not isinstance(inputs, list):
        raise TypeError("spec.inputs: attached reference profiles require a list")
    by_id: dict[str, list[dict[str, Any]]] = {}
    for item in inputs:
        if isinstance(item, dict) and _nonempty_string(item.get("id")):
            by_id.setdefault(item["id"], []).append(item)
    for source_id in profile["source_ids"]:
        matches = by_id.get(source_id, [])
        if not matches:
            raise ValueError(f"spec.inputs: missing attached source id {source_id!r}")
        if len(matches) != 1:
            raise ValueError(f"spec.inputs: source id {source_id!r} must occur once")
        if matches[0].get("must_attach") is not True:
            raise ValueError(f"spec.inputs: source id {source_id!r} must set must_attach=true")


def apply_reference_profile(spec: Any, profile: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Deep-copy ``spec``, append adopted prompt prose once, and return a separate audit."""
    errors = validate_reference_profile(profile)
    if errors:
        raise ValueError("invalid reference profile: " + "; ".join(errors))
    assert isinstance(profile, dict)
    _validate_spec_for_profile(spec, profile)
    assert isinstance(spec, dict)
    result = copy.deepcopy(spec)

    scene = result.get("scene")
    if scene is None:
        scene = {}
        result["scene"] = scene
    if not isinstance(scene, dict):
        raise TypeError("spec.scene: expected an object when present")
    summary = scene.get("summary", "")
    if not isinstance(summary, str):
        raise TypeError("spec.scene.summary: expected a string when present")

    projected_prompts: list[str] = []
    facet_audit: list[dict[str, Any]] = []
    current_summary = summary
    for facet in profile["facets"]:
        adopted = facet["decision"] in {"preserve", "adapt"}
        prompt = facet["prompt"]
        status = "not_adopted"
        if adopted:
            if _contains_exact_clause(current_summary, prompt) or prompt in projected_prompts:
                status = "already_present"
            else:
                projected_prompts.append(prompt)
                current_summary = f"{current_summary.rstrip()}\n{prompt.strip()}".strip()
                status = "appended"
        facet_audit.append(
            {
                "source_ids": list(facet["source_ids"]),
                "facet": facet["id"],
                "evidence": facet["evidence"],
                "observation": facet["observation"],
                "decision": facet["decision"],
                "prompt": prompt if adopted else "",
                "reason": facet["reason"],
                "review_check": facet["review_check"] if adopted else "",
                "projection_status": status,
            }
        )
    if projected_prompts:
        scene["summary"] = current_summary

    attachment_status = "declared_must_attach" if profile["reference_mode"] == "attached" else "text_transfer_no_attachment_claimed"
    audit = {
        "metadata": {
            "reference_profile": PROFILE_VERSION,
            "profile_id": profile["id"],
            "reference_mode": profile["reference_mode"],
            "source_ids": list(profile["source_ids"]),
            "attachment_status": attachment_status,
        },
        "facets": facet_audit,
    }
    return result, audit


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="Reference profile JSON")
    parser.add_argument("--spec", required=True, type=Path, help="Target visual specification JSON")
    args = parser.parse_args()
    try:
        profile = _load_json(args.profile)
        spec = _load_json(args.spec)
        result, audit = apply_reference_profile(spec, profile)
        spec_errors = validate_spec(result)
        if spec_errors:
            raise ValueError("invalid projected spec: " + "; ".join(spec_errors))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({"spec": result, "audit": audit}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
