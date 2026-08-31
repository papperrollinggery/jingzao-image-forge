# Production Coverage and Independent Image Handoff

Use this only when a sequence must provide usable images to a film/video workflow. Ordinary single images and exploratory contact sheets do not need a production manifest.

## Responsibility boundary

DIR or the user's planning workflow owns the script, shot IDs, timing, video-model choices, dialogue, and project ledger. Jingzao owns the image requirement, visible state, camera proof, reference roles, prompt, and image review. Do not rebuild the upstream workflow inside this Skill or turn a request for images into permission to generate videos.

Before generation, account for the approved shot list. Each shot has a visible requirement and either its necessary image-frame IDs or a specific reason for using video-only motion. This is a structural cross-check against the supplied plan, not an automatic judgment that the story or edit is complete.

## Choose anchors from risk, not a frame quota

- Establish geography when later views depend on it; an attractive environment image alone does not cover reactions, reverse angles, contact, or changed prop states.
- Add an image when it fixes a necessary identity, camera relation, reveal, interaction/contact, precise text, endpoint, or object-state fact that the video prompt should not invent.
- A continuous low-risk movement can remain a video instruction. State what is allowed to vary and why no additional image anchor is necessary; confirm the actual model/input mode upstream.
- Start/end pairs, inserts, over-the-shoulder views, and reverse shots are conditional tools, not mandatory bundles. Do not generate every intermediate motion state merely to increase coverage.
- A still describes one visible phase. A video prompt may describe a transition between phases; do not apply “states only” as a universal restriction on video models.
- Distinguish environment master, character/wardrobe reference, prop-state asset, exploratory storyboard, and production image. One file can serve several explicitly reviewed roles, but a contact sheet is not automatically a set of approved production frames.

For each planned frame, determine the shot function, visible state, reference/asset versions, camera proof, required invariants, permitted variation, and review criterion. Keep these records with the project. Never mark a frame adopted from prompt compilation alone.

## Reverse views: lock the world, change the projection

Write two separate lists:

1. World invariants: room layout, object identity/dimensions, wall positions, doors, windows, light sources, prop owner/state, and actor positions.
2. View-dependent facts: camera position/direction, lens/distance, screen-left/right, foreground occlusion, visible wall, and eyeline.

Derive the new view from the actual camera position. A reverse angle is not a blanket horizontal flip. A new camera may reveal previously unseen surfaces; label them unknown or establish a project-approved design instead of presenting them as reference-observed truth. “Preserve everything” must not lock the old projection when a new viewpoint is requested.

Example: a north-facing camera sees a west-wall wheel at screen-left. A south-facing camera sees it at screen-right; the north window is now behind the camera. Keep the west-wall wheel and north window in the same world locations. Do not mirror their world geometry or invent a second window.

## Prop states and physically consistent edits

Track meaningful states separately: closed/open, held/released, intact/broken, unlit/lit, locked/unlocked. Reuse approved identity, materials, and geometry while declaring only the state that changes. Do not assume one pristine prop image proves every later state.

For a local edit, state:

- the smallest requested change and the visible result;
- what fills a removed object's region;
- the identity, composition, medium, text, and regions that remain fixed;
- necessary secondary effects, such as a moved object's contact shadow, reflection, occlusion, or exposed background.

Preserve unaffected lighting, not physically impossible old shadows. Do not repeat an exhaustive preservation list in several sections or promise “100% identical” pixels. If the change requires new geometry or a new camera, treat it as a new-view image with world locks, not cosmetic local cleanup. Keep existing `edit`, `reconstruct`, `clean_reset`, and reference-delivery contracts.

## Production manifest

See [the complete example](../examples/production-coverage.json).

- `production_manifest`: `"1.0"`.
- `coverage`: one row per approved shot, with `shot_id`, `requirement`, and `frame_ids`. Empty `frame_ids` require a nonempty `video_only_reason`; do not use that reason as a generic waiver for missing work.
- `frames`: unique `id`, matching `shot_id`, a brief backstage `purpose`, and a complete single-image `spec` using the existing schema. Each frame must be referenced exactly once by its own shot.
- Each spec declares an explicit native `canvas.aspect_ratio`; production frames cannot be nested styleboards or style-learning analyses.
- Every frame owns its own subjects, visible state, text, references, preservation rules, and requested style. There is no implicit shared-spec merge and no inferred slicing of whole-board prose.
- Paths for local image inputs are relative to the manifest file, as with standalone image specs. Supply actual identity/geography references when continuity depends on them. Text-only examples demonstrate compilation, not verified continuity.

The compiler preserves IDs, purpose, the full requested `canvas`, coverage, and preflight results outside model-facing prompts. The executor must consume the frame's `canvas` when setting native aspect ratio/dimensions; ratio-only metadata is not proof that an API size was set or that an image meets it. Never guess pixel dimensions. A frame never receives another frame's exact text or references by automatic inheritance. Supply an intentional shared asset explicitly to every frame that needs it.

```bash
python3 scripts/compile_production.py examples/production-coverage.json --platform openai
python3 scripts/compile_production.py examples/production-coverage.json --platform openai --frame-id frame-02
```

Default output is a JSON bundle of independent frame envelopes. `--frame-id` selects one envelope after validating the entire plan. This command does not generate images, write files, upload references, or call a video model. Redirect output only to a project path you intend to create.

Exit codes: `0` ready prompt/reference handoff; `1` blocked or review-required handoff with diagnostic JSON; `2` invalid manifest, unknown selection, or unreadable input. Review approval is explicit and never bypasses contamination. Required local files must exist; conversation references still require execution-time confirmation. Non-OpenAI adapters are not judged by Codex-only attachment mechanics.

## Acceptance and release boundary

1. Compare every shot in the original approved plan with `coverage`; the validator cannot find a shot omitted from both lists.
2. Confirm no duplicate/missing/orphan/misassigned frame IDs, invalid single-image specs, unresolved required references, or unconsumed prompt review.
3. Read each prompt independently: correct native ratio, one current visible state, exact local text, proper reference roles, intentional style, and no backstage notes.
4. Inspect actual images at thumbnail and full size for identity, world geometry, reverse-view relationships, contact, prop states, exact text, texture hierarchy, and preserved medium.
5. Review adjacent images as a sequence and trace candidates versus adopted assets. A ready prompt bundle is neither visual approval nor evidence that a downstream video was generated or reached reference-film quality.

Portable ideas adapted from local LIRA material are selective: explicit state assets, camera-relative object arrangement, and narrow edits with preservation. Its fixed provider order, universal thirds/60–30–10 palette, fixed prompt caps, named-entity bans, and unverified global model-quality claims are not Jingzao defaults. Existing platform adapters, user intent, dynamic budgets, and style authority remain authoritative.
