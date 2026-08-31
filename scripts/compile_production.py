#!/usr/bin/env python3
"""Compile an explicit shot-coverage plan into independent image-frame prompts."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

try:
    from compile_prompt import SUPPORTED_PLATFORMS, compile_spec
    from reference_delivery import (
        CODEX_IMAGEGEN_TARGET,
        PORTABLE_TARGET,
        preflight_reference_delivery,
    )
    from validate_spec import validate_spec
except ModuleNotFoundError:  # Support `python -m scripts.compile_production`.
    from scripts.compile_prompt import SUPPORTED_PLATFORMS, compile_spec
    from scripts.reference_delivery import (
        CODEX_IMAGEGEN_TARGET,
        PORTABLE_TARGET,
        preflight_reference_delivery,
    )
    from scripts.validate_spec import validate_spec


ROOT_KEYS = {"production_manifest", "coverage", "frames"}
COVERAGE_KEYS = {"shot_id", "requirement", "frame_ids", "video_only_reason"}
FRAME_KEYS = {"id", "shot_id", "purpose", "spec"}
STATUS_SEVERITY = {"ready": 0, "review_required": 1, "blocked": 2}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_content(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_has_content(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_content(item) for item in value)
    return value is not None


def _validate_known_keys(value: dict[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in value:
        if key not in allowed:
            errors.append(f"{path}.{key}: unknown field")


def _validate_string(value: Any, path: str, errors: list[str]) -> None:
    if not _nonempty_string(value):
        errors.append(f"{path}: expected a non-empty string")


def validate_manifest(manifest: object) -> list[str]:
    """Return structural and per-frame spec errors without raising on malformed input."""
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["$: expected a JSON object"]

    _validate_known_keys(manifest, ROOT_KEYS, "$", errors)
    if manifest.get("production_manifest") != "1.0":
        errors.append('$.production_manifest: expected "1.0"')

    coverage = manifest.get("coverage")
    if not isinstance(coverage, list):
        errors.append("$.coverage: expected a list")
        coverage = []
    elif not coverage:
        errors.append("$.coverage: expected at least one coverage row")

    frames = manifest.get("frames")
    if not isinstance(frames, list):
        errors.append("$.frames: expected a list")
        frames = []

    coverage_by_shot: dict[str, int] = {}
    coverage_references: dict[str, list[tuple[int, str]]] = {}
    for index, row in enumerate(coverage):
        path = f"$.coverage[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path}: expected an object")
            continue
        _validate_known_keys(row, COVERAGE_KEYS, path, errors)
        shot_id = row.get("shot_id")
        _validate_string(shot_id, f"{path}.shot_id", errors)
        _validate_string(row.get("requirement"), f"{path}.requirement", errors)
        if _nonempty_string(shot_id):
            if shot_id in coverage_by_shot:
                errors.append(f"{path}.shot_id: duplicate shot_id {shot_id!r}")
            else:
                coverage_by_shot[shot_id] = index

        frame_ids = row.get("frame_ids")
        if not isinstance(frame_ids, list):
            errors.append(f"{path}.frame_ids: expected a list")
            frame_ids = []
        valid_frame_ids: list[str] = []
        seen_in_row: set[str] = set()
        for frame_index, frame_id in enumerate(frame_ids):
            id_path = f"{path}.frame_ids[{frame_index}]"
            _validate_string(frame_id, id_path, errors)
            if not _nonempty_string(frame_id):
                continue
            if frame_id in seen_in_row:
                errors.append(f"{id_path}: duplicate frame_id {frame_id!r} in coverage row")
            seen_in_row.add(frame_id)
            valid_frame_ids.append(frame_id)

        reason_present = "video_only_reason" in row
        reason = row.get("video_only_reason")
        if reason_present and not _nonempty_string(reason):
            errors.append(f"{path}.video_only_reason: expected a non-empty string when present")
        if not valid_frame_ids and not _nonempty_string(reason):
            errors.append(f"{path}: empty frame_ids requires a non-empty video_only_reason")
        if valid_frame_ids and _nonempty_string(reason):
            errors.append(f"{path}: frame_ids and non-empty video_only_reason are mutually exclusive")
        if _nonempty_string(shot_id):
            for frame_id in valid_frame_ids:
                coverage_references.setdefault(frame_id, []).append((index, shot_id))

    frames_by_id: dict[str, tuple[int, dict[str, Any]]] = {}
    for index, frame in enumerate(frames):
        path = f"$.frames[{index}]"
        if not isinstance(frame, dict):
            errors.append(f"{path}: expected an object")
            continue
        _validate_known_keys(frame, FRAME_KEYS, path, errors)
        frame_id = frame.get("id")
        shot_id = frame.get("shot_id")
        _validate_string(frame_id, f"{path}.id", errors)
        _validate_string(shot_id, f"{path}.shot_id", errors)
        _validate_string(frame.get("purpose"), f"{path}.purpose", errors)
        spec = frame.get("spec")
        if not isinstance(spec, dict):
            errors.append(f"{path}.spec: expected an object")
        else:
            errors.extend(f"{path}.spec{error[1:]}" if error.startswith("$") else f"{path}.spec: {error}" for error in validate_spec(spec))
            mode = spec.get("mode")
            if isinstance(mode, str) and mode in {"styleboard", "learn_style"}:
                errors.append(f"{path}.spec.mode: production frames must be single-image, not {mode!r}")
            if "styleboard" in spec and _has_content(spec.get("styleboard")):
                errors.append(f"{path}.spec.styleboard: production frames cannot contain styleboard data")
            canvas = spec.get("canvas")
            if not isinstance(canvas, dict) or not _nonempty_string(canvas.get("aspect_ratio")) or canvas.get("aspect_ratio") == "auto":
                errors.append(f"{path}.spec.canvas.aspect_ratio: production frames require an explicit native non-auto canvas.aspect_ratio")
        if _nonempty_string(frame_id):
            if frame_id in frames_by_id:
                errors.append(f"{path}.id: duplicate frame id {frame_id!r}")
            else:
                frames_by_id[frame_id] = (index, frame)

    for frame_id, references in coverage_references.items():
        if frame_id not in frames_by_id:
            for coverage_index, _ in references:
                errors.append(f"$.coverage[{coverage_index}].frame_ids: unknown frame_id {frame_id!r}")
            continue
        frame_index, frame = frames_by_id[frame_id]
        if len(references) != 1:
            errors.append(f"$.frames[{frame_index}].id: frame {frame_id!r} must be referenced exactly once by coverage")
        for coverage_index, coverage_shot_id in references:
            if frame.get("shot_id") != coverage_shot_id:
                errors.append(
                    f"$.coverage[{coverage_index}].frame_ids: frame {frame_id!r} shot_id does not match coverage shot_id {coverage_shot_id!r}"
                )
    for frame_id, (frame_index, _) in frames_by_id.items():
        if frame_id not in coverage_references:
            errors.append(f"$.frames[{frame_index}].id: frame {frame_id!r} is not covered")

    return errors


def _merge_openai_call_plan(compiled: dict[str, Any], preflight: dict[str, Any]) -> None:
    call_plan = preflight.get("imagegen_call_plan")
    if not isinstance(call_plan, dict):
        return
    call_plan = copy.deepcopy(call_plan)
    review = compiled.get("prompt_review")
    review_status = review.get("status") if isinstance(review, dict) else "blocked"
    call_plan["prompt_review_status"] = review_status
    if not preflight.get("valid", False) and call_plan.get("status") == "ready":
        call_plan["status"] = "blocked"
        errors = call_plan.setdefault("errors", [])
        if isinstance(errors, list):
            errors.extend(error for error in preflight.get("errors", []) if isinstance(error, str))
    if call_plan.get("status") == "ready" and review_status in {"blocked", "review_required"}:
        call_plan["status"] = review_status
        errors = call_plan.setdefault("errors", [])
        if isinstance(errors, list):
            errors.append("compiled prompt must pass prompt_review before ImageGen execution")
    compiled["imagegen_call_plan"] = call_plan


def _frame_status(compiled: dict[str, Any], preflight: dict[str, Any], platform: str) -> str:
    review = compiled.get("prompt_review")
    review_status = review.get("status") if isinstance(review, dict) else "blocked"
    if review_status == "blocked":
        return "blocked"
    if platform == "openai":
        if not preflight.get("valid", False):
            return "blocked"
        plan = compiled.get("imagegen_call_plan")
        plan_status = plan.get("status") if isinstance(plan, dict) else "blocked"
        if plan_status == "blocked":
            return "blocked"
        if plan_status == "review_required":
            return "review_required"
    elif not preflight.get("valid", False):
        return "blocked"
    return "review_required" if review_status == "review_required" else "ready"


def _overall_status(statuses: list[str]) -> str:
    return max(statuses, key=lambda status: STATUS_SEVERITY[status], default="ready")


def compile_manifest(
    manifest: dict,
    base_dir: Path,
    platform: str | None = None,
    *,
    review_approved: bool = False,
) -> dict:
    """Compile every validated frame separately, keeping all source metadata outside prompts."""
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("Invalid production manifest:\n" + "\n".join(f"- {error}" for error in errors))
    if platform is not None and platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"unsupported platform: {platform}")

    output_frames: list[dict[str, Any]] = []
    warnings: list[str] = [
        "Structural coverage does not approve visual or video execution, quality, continuity, or delivery."
    ]
    statuses: list[str] = []
    target_base_dir = Path(base_dir)
    for frame in manifest["frames"]:
        spec = copy.deepcopy(frame["spec"])
        compiled = compile_spec(spec, platform, review_approved=review_approved)
        compiled_platform = compiled["platform"]
        preflight_target = CODEX_IMAGEGEN_TARGET if compiled_platform == "openai" else PORTABLE_TARGET
        preflight = preflight_reference_delivery(spec, target_base_dir, target=preflight_target)
        if compiled_platform == "openai":
            _merge_openai_call_plan(compiled, preflight)
        status = _frame_status(compiled, preflight, compiled_platform)
        statuses.append(status)
        output_frames.append(
            {
                "id": frame["id"],
                "shot_id": frame["shot_id"],
                "purpose": frame["purpose"],
                "canvas": copy.deepcopy(frame["spec"]["canvas"]),
                "compiled": compiled,
                "preflight": preflight,
            }
        )
        warnings.extend(f"{frame['id']}: {warning}" for warning in compiled.get("warnings", []) if isinstance(warning, str))
        warnings.extend(f"{frame['id']}: {warning}" for warning in preflight.get("errors", []) if isinstance(warning, str))

    return {
        "production_manifest": manifest["production_manifest"],
        "coverage": copy.deepcopy(manifest["coverage"]),
        "frames": output_frames,
        "status": _overall_status(statuses),
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to a production manifest JSON file")
    parser.add_argument("--platform", choices=sorted(SUPPORTED_PLATFORMS), help="Override every frame's platform")
    parser.add_argument("--approve-review", action="store_true")
    parser.add_argument("--frame-id", help="Emit only one frame after validating and compiling the complete plan")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_manifest(manifest)
    if errors:
        print("INVALID PRODUCTION MANIFEST", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    try:
        result = compile_manifest(manifest, args.manifest.parent, args.platform, review_approved=args.approve_review)
    except (TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.frame_id:
        selected = [frame for frame in result["frames"] if frame["id"] == args.frame_id]
        if not selected:
            print(f"ERROR: unknown frame id: {args.frame_id}", file=sys.stderr)
            return 2
        frame = selected[0]
        frame_status = _frame_status(frame["compiled"], frame["preflight"], frame["compiled"]["platform"])
        result = {
            **frame,
            "status": frame_status,
            "warnings": [
                "Structural coverage does not approve visual or video execution, quality, continuity, or delivery.",
                *[warning for warning in frame["compiled"].get("warnings", []) if isinstance(warning, str)],
                *[warning for warning in frame["preflight"].get("errors", []) if isinstance(warning, str)],
            ],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
