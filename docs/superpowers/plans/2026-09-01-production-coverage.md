# Production Coverage Implementation Plan

> **For agentic workers:** Use scoped subagent-driven development with test-first implementation, then independent specification and code review. Existing image compilation remains authoritative.

**Goal:** Deliver a backward-compatible image-production handoff that accounts for required shot coverage and produces one isolated prompt package per planned image.

**Architecture:** Keep DIR responsible for story, shot planning, video prompts, and the project ledger. Add a small opt-in production manifest around existing complete single-image specs; reuse the existing validator, compiler, and attachment preflight. Do not infer individual images by slicing prose from a multi-frame styleboard.

**Tech Stack:** Python 3.10+ standard library, unittest, existing image-spec compiler, GitHub Actions.

## Scope and design decisions

- Baseline: v1.5.0 (`ae62524`). Preserve clean-base prevention, dynamic budgets, seven existing modes, UI Motion hierarchy, named anchors, exact text, real reference delivery, and platform adapters.
- Ordinary single-image calls and sheet exploration remain unchanged.
- Production coverage is opt-in. No fixed frame quota, compulsory reverse shot, or mandatory start/end pair. A planned shot either identifies its necessary image frames or records a specific reason why video-only motion is sufficient.
- Each image carries a complete existing `visual_generation_spec`, with an explicit native aspect ratio. This deliberately avoids automatic inheritance/merging, phase inference, or cross-frame text/reference leakage.
- Manifest metadata never enters model-facing prompts. Each frame spec owns its visible state, exact text, references, and preservation constraints.
- World-space identity/geography and camera-relative composition are separate. Reverse angles are not blanket horizontal mirrors. New/unseen geometry remains an explicit design decision or unknown.
- Local edits specify the change, resulting fill, invariant regions, and necessary secondary changes in shadows/reflections/contact. Do not promise pixel identity or require impossible unchanged lighting.
- LIRA contributes portable state/coverage/edit ideas only. Do not copy fixed provider order, fixed prompt-length ceilings, universal composition/palette presets, or claims that a model is globally dirty.

## Task 1: Production manifest compiler

Files: create `scripts/compile_production.py` and `tests/test_production.py` only.

Public API:

```python
validate_manifest(manifest: object) -> list[str]
compile_manifest(manifest: dict, base_dir: Path, platform: str | None = None,
                 *, review_approved: bool = False) -> dict
```

Input contract:

```json
{
  "production_manifest": "1.0",
  "coverage": [
    {"shot_id": "shot-01", "requirement": "Show the held object", "frame_ids": ["frame-01"]},
    {"shot_id": "shot-02", "requirement": "Continuous approach", "frame_ids": [], "video_only_reason": "No new identity, geometry, contact, or prop state needs an image anchor"}
  ],
  "frames": [
    {"id": "frame-01", "shot_id": "shot-01", "purpose": "Prove the readable object state", "spec": {"visual_generation_spec": "1.0", "mode": "create", "intent": "A brass key lying flat on a plain desk.", "canvas": {"aspect_ratio": "16:9"}}}
  ]
}
```

- [ ] Write failing tests before implementation: unique IDs, missing/orphan/misassigned frame links, explicit video-only reason, malformed structures/unknown keys, invalid image specs, no nested styleboard/analysis, explicit native ratio, no mutation, isolated text/subjects/references, preserved source constraints, and all four adapters.
- [ ] Implement validation and compilation without changing existing modules. Require at least one coverage row; an all-video-only plan is a valid plan with zero exported image frames.
- [ ] Return a JSON bundle with `production_manifest`, `coverage`, `frames`, `status`, and a clear warning that structural coverage is not creative/image/video approval. Each frame retains id/shot_id/purpose/canvas plus `compiled` and attachment `preflight`. Preserve existing prompt-review and execution statuses, including blocked/review-required; never silently approve them. The executor must consume canvas; do not invent dimensions.
- [ ] Run portable attachment preflight relative to the manifest directory. Add Codex execution preflight for OpenAI without treating unsupported Codex mechanics as failure for other providers. Missing required local references must prevent a ready handoff; conversation references remain execution-time requirements.
- [ ] CLI: positional manifest; optional `--platform`, `--approve-review`, `--frame-id`. Default emits the complete JSON bundle; selection emits exactly one frame envelope after validating the entire plan. No image/API execution or filesystem writes. Invalid input/unknown frame exits 2; valid but blocked/review-required handoff exits 1 while retaining JSON evidence; ready handoff exits 0.
- [ ] Run `python3 -B -m unittest discover -s tests -v`; all baseline and new tests must pass. Check directory/malformed JSON input produces a clean error, not a traceback.

## Task 2: User workflow, example, and CI

Files: `SKILL.md`, `references/production-coverage.md`, `references/styleboard-mode.md`, `references/prompt-compiler.md`, `examples/production-coverage.json`, `tests/evals.md`, both READMEs, `llms.txt`, and `.github/workflows/validate.yml`.

- [ ] Add one conditional entrypoint link; do not expand unrelated image modes.
- [ ] Document coverage planning, reverse-view geometry, separate prop states, physically consistent minimal edits, and the boundary between still-image state and video transition.
- [ ] Add an original, non-private example with front/reverse/insert coverage and a justified video-only beat. It must contain no copied film, brand, personal image, or presumed approval.
- [ ] Correct the existing statement that `independent_frames` automatically compiles separate prompts. Legacy styleboard produces a planning package; this new explicit manifest produces single-image packages.
- [ ] Extend CI to compile the manifest for all adapters and select a frame; validate the new code with the existing Ruff and unittest gates.

## Task 3: Review and release

### Added user-approved quality scope

- Complete read-only DIR cleanup trace: source intake, material response, optional surface macro, pre-generation rules, generated-output QA, one-layer retry, clean-master lineage, convergence and adoption. Preserve DIR itself.
- Improve six advisory cleanup phrases plus explicit clean-reset preservation wording; keep clean_base, budgets, user text and existing adapters unchanged.
- Verify against real private scene assets, not only unit tests. Retain failures and separate surface improvement from action/count/composition acceptance. Do not publish private images, prompts or paths.
- Permit a texture-free layout proxy only after demonstrated dirty-reference carryover; validate its geometry/contacts before reuse. Do not promote a one-case benefit into a universal rule.
- Add valid-spec quality tests and portable-diagnostic regression coverage, then run the final DeepSeek review for over-engineering and negative optimization.

- [ ] Audit dirty legacy files against v1.5 and preserve every unique change. Do not overwrite the original directory while work is active.
- [ ] Independently review specification compliance, then code correctness/security and negative regressions. Fix concrete findings; do not broaden the architecture.
- [ ] Run all CI-equivalent commands, structural Skill validation, isolated installation tests, and realistic independent use tests. Label image/video quality unverified unless actual media was generated and inspected.
- [ ] Snapshot original dirty state recoverably before reconciling the original checkout. Record which changes were already released versus newly integrated.
- [ ] Publish only reviewed tracked files: no raw private references, local paths, session identifiers, tool outputs, or unreviewed old residue.
- [ ] Commit, push, verify branch CI, integrate main, verify main CI, install the exact candidate with recoverable backup, compare packaged core files, tag/release v1.6.0, verify tag CI and remote release assets.
- [ ] Final receipt binds commit/tag, source/install/archive parity, checks, prior-work disposition, and remaining limitations. Do not claim future session auto-loading or media quality from file parity.
