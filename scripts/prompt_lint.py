#!/usr/bin/env python3
"""Deterministically lint compiled Jingzao prompts without generating images."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from compile_prompt import (
        SUPPORTED_PLATFORMS,
        compile_spec,
    )
    from validate_spec import load_json, validate_spec
except ModuleNotFoundError:  # Support `python -m scripts.prompt_lint` from the repository root.
    from scripts.compile_prompt import (
        SUPPORTED_PLATFORMS,
        compile_spec,
    )
    from scripts.validate_spec import load_json, validate_spec


def lint_compiled_result(result: dict[str, Any], *, max_words: int | None = None) -> list[str]:
    prompt = result.get("prompt")
    if not isinstance(prompt, str):
        return ["compiled result requires a string prompt"]
    errors: list[str] = []
    for marker in ("Describe the", "replace-with-the-actual", "control.weight", "control.variance"):
        if marker in prompt:
            errors.append(f"placeholder or internal control leaked into prompt: {marker}")
    metrics = result.get("prompt_metrics") if isinstance(result.get("prompt_metrics"), dict) else {}
    words = metrics.get("words")
    if not isinstance(words, int):
        errors.append("compiled result requires integer prompt_metrics.words")
    elif max_words is not None and words > max_words:
        errors.append(f"prompt word count {words} exceeds fixture ceiling {max_words}")
    if result.get("platform") == "midjourney":
        prompt_without_flags = prompt.split(" --", 1)[0]
        if "--" in prompt_without_flags:
            errors.append("Midjourney provider flag leaked into prompt prose")
    review = result.get("prompt_review") if isinstance(result.get("prompt_review"), dict) else {}
    review_status = review.get("status")
    if review_status not in {"ready", "approved", "review_required", "blocked"}:
        errors.append("compiled result requires a valid prompt_review.status")
    elif review_status == "blocked":
        errors.append("prompt_review is blocked")
    elif review_status == "review_required":
        errors.append("prompt_review requires explicit approval before execution")
    return errors


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--platform", choices=sorted(SUPPORTED_PLATFORMS), required=True)
    parser.add_argument("--max-words", type=int)
    parser.add_argument(
        "--approve-review",
        action="store_true",
        help="Approve length/reference-complexity review; context residue remains blocked",
    )
    args = parser.parse_args()
    try:
        spec = load_json(args.spec)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    spec_errors = validate_spec(spec)
    if spec_errors:
        print(json.dumps({"valid": False, "errors": spec_errors}, ensure_ascii=False, indent=2))
        return 2
    result = compile_spec(spec, args.platform, review_approved=args.approve_review)
    errors = lint_compiled_result(result, max_words=args.max_words)
    print(
        json.dumps(
            {
                "valid": not errors,
                "errors": errors,
                "prompt_metrics": result["prompt_metrics"],
                "prompt_review": result["prompt_review"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
