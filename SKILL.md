---
name: jingzao-image-forge
description: Create, reverse-engineer, edit, restyle, expand, or build reference-led styleboards using a structured visual specification and platform-aware compilation. Use when cinematic narrative frames, artistic treatments, giant-scale spectacle, Chinese fantasy effects, character blocking, camera and lens logic, composition, clean material rendering, artifact control, or cross-model prompt delivery must be controlled; this skill prepares prompts and specifications but does not itself generate images.
---

# 镜造 Image Forge

Turn an image brief or observed reference into a maintainable visual specification, then compile it for the user's target image system.

## Workflow

1. Classify the operation as `create`, `reconstruct`, `edit`, `restyle`, `expand`, or `styleboard`.
2. Read or inspect every supplied image before describing it. Never infer image contents from a filename or prior summary.
3. Preserve the user's exact facts: subject count, names, actions, spatial relationships, visible text, aspect ratio, dimensions, reference roles, and forbidden elements.
4. Detect exact named entities whose existing model knowledge may improve the result. Preserve them verbatim as optional `knowledge_anchors`; do not replace them with generic feature inventories.
5. For a simple single-subject creation, a concise prompt may be enough. For multi-subject scenes, reference-based work, exact layouts, or edits, build a `visual_generation_spec` using [templates/visual-spec.json](templates/visual-spec.json) and read [references/visual-spec.md](references/visual-spec.md).
6. Separate invariants from permitted variation. Use `control.weight`, `control.lock`, and `control.variance` as internal planning semantics; do not assume a platform supports them directly.
7. For edits, state both the smallest requested change and the preserve list. Normalize points and regions to top-left-origin percentages. A point such as `(x: 16.5%, y: 16.4%)` is an anchor, not a guarantee of pixel-accurate masking.
8. Compile the specification with `scripts/compile_prompt.py` or follow [references/prompt-compiler.md](references/prompt-compiler.md). Keep generation parameters separate from prompt prose.
9. Run `scripts/validate_spec.py` before delivering a JSON specification. Review the result against [tests/evals.md](tests/evals.md) when consistency or exact edits matter.

## Knowledge-Aware Generation

Use this route when a request names a recognizable character, person, work, historical event, place, artifact, product, or fictional-world element.

- Default to adaptive `auto`: use the exact named entity as a compact first-pass anchor; select `reference` or `hybrid` only when supplied references or version-specific accuracy justify them.
- For GPT Image 2 or the built-in `$imagegen` path, place the exact entity and requested incarnation, period, or medium before scene detail. Let the model use its existing world knowledge instead of expanding the name into a long generic description.
- Treat cinematic framing, scale, and lighting as composition language. Do not silently convert animation, illustration, game art, or another stated medium into live action.
- Keep the maintainable specification detailed, but compile a clean first-pass prompt. Add detail only when it disambiguates the named entity or corrects an observed failure.
- If `$imagegen` returns a revised prompt, check that the exact anchor, incarnation, and medium survived the rewrite before accepting the output.
- If identity or canonical appearance fails, prefer a corrected fresh generation or a suitable identity reference over a local edit to a small subject. Label reference roles and use only references that match the requested version closely enough.
- Model knowledge is a generation aid, not verification evidence. Mark canonical accuracy `未验证` until checked against a trusted visible reference or confirmed by the user.

## Artifact and Material Quality

For premium, clean, photorealistic, product, portrait, dark-scene, or dense fantasy work, run a compact quality preflight. Read [references/quality-controls.md](references/quality-controls.md) when an output looks noisy, speckled, waxy, oily, over-sharpened, excessively glossy, flare-heavy, or uniformly over-processed.

- Choose one optional `render.artifact_budget`: `strict`, `balanced`, `expressive`, or `source_matched`. Do not stack every cleanup phrase into every prompt.
- Define material-specific roughness, highlight width, reflection, texture scale, and contact behavior before adding generic quality adjectives.
- Keep detail selective: reserve full clarity and microtexture for focal surfaces; let secondary areas fall off through distance, light, focus, and occlusion.
- Bloom, lens flare, grain, floating particles, sparks, and gloss require a visible light source, requested medium, physical event, or source-image precedent. Otherwise keep them restrained.
- Prefer positive visible targets plus one compact current-risk avoid block. Do not preserve a history of old failed objects or styles in negative constraints.
- For dirty-output retries, regenerate from a clean specification when practical. Repeated image-to-image cleanup can preserve or amplify unwanted residue; use editing only when the user needs the original structure preserved.

## Visual Intent Router

After choosing the operation mode, analyze what the image must do. Do not collapse “cinematic,” “artistic,” “spectacular,” and “fantasy” into one poster-like treatment.

- **Deliverable:** `narrative_film_frame`, `cinematic_key_art`, `poster`, or `concept_art`. Story moments, relationships, reactions, decisions, and implied before/after favor a narrative frame; marketing, cover, hero, title-led, or showcase language favors key art or poster.
- **Treatment:** `grounded_cinematic`, `heightened_cinematic`, or `graphic_stylized`. Grounded choices remain physically filmable; heightened choices may exaggerate perspective, color, optical behavior, or composition when the viewer effect is explainable; graphic treatment may use designed shape, line, 2D/3D layering, and impossible camera logic while preserving spatial readability.
- **Spectacle scale:** `intimate`, `dramatic`, `monumental`, or `mythic`. Scale changes camera placement, human/environment ratio, atmosphere, occlusion, environment response, and information density—not merely the adjective “epic.”
- **Genre logic:** record the world rule that governs the shot. Chinese fantasy, xianxia, mythology, giant creatures, science fiction, product work, and documentary realism require different effect, material, and camera assumptions.
- **Camera freedom:** `physical`, `heightened`, or `impossible`. Use the least impossible level that achieves the user's requested result.

For substantial cinematic, artistic, spectacle, giant-scale, or Chinese-fantasy work, read [references/direction-profiles.md](references/direction-profiles.md). Preserve the user's medium and desired exaggeration; realism is a choice, not a universal quality gate.

## Narrative Film Frame

When the deliverable is `narrative_film_frame`, read [references/cinematic-shot-design.md](references/cinematic-shot-design.md).

- Define the visible event, relationship change, viewer task, chosen frozen moment, and withheld information before camera vocabulary.
- Choose viewer position and primary relationship before blocking, eyelines, axis, screen direction, occlusion, and attention flow.
- Derive shot size, camera height, camera distance, focal length, focus, and foreground from one primary viewer function.
- Tie lighting to physical or world-valid sources and a narrative function. Decorative rim light, smoke, bloom, particles, and graphic effects cannot replace staging or performance.
- Guard against posterization: do not make every character, prop, effect, and background equally visible, centered, sharp, heroic, or simultaneously active.

Use `canvas.profile: cinematic_ultrawide` when lateral distance, offscreen space, layered geography, giant scale, or a 21:9/2.35:1 delivery materially helps. Do not force all film frames into ultrawide.

## Reference-Led Styleboard

Use `styleboard` when the user wants reference analysis translated into several consistent shots, a triptych, contact sheet, nine-grid board, vertical storyboard, camera/style study, or “reference image → target style → multi-frame presentation.” Read [references/styleboard-mode.md](references/styleboard-mode.md).

- Inspect every reference and assign one primary role: identity, wardrobe, scene, prop, `camera_action`, style, layout, or palette. A reference must not silently control unrelated layers.
- Build frame cards before generation. Each frame needs one shot function, one story moment, one primary action and phase, camera logic, subject map, and reference assignments.
- Choose the generation strategy from speed and continuity risk: `sheet_direct` for the fastest one-call board, `independent_frames` for strict native-ratio continuity, or `hybrid` for a fast direct sheet followed by targeted cell replacement. A direct sheet is a valid deliverable when panel count, cell geometry, continuity, and crop safety pass review.
- Lock continuity and state allowed variation separately. Match-cut pairs share geometry, orientation, focal-length feel, scale, action phase, and prop state; only declared variables may change.

## Mode Rules

- `create`: Describe the desired result directly; add exclusions only when they prevent a likely failure.
- `reconstruct`: Report observable features separately from inference. Reproduce visual attributes, not an unknowable original prompt.
- `edit`: Use “change only” plus explicit invariants. Prefer one meaningful change per iteration.
- `restyle`: Lock geometry, identity, pose, layout, and text unless the user says otherwise; vary only visual treatment.
- `expand`: Preserve the original field of view and subject position, then describe only the new canvas area and continuity requirements.
- `styleboard`: Analyze reference roles, define a visual master and frame cards, choose `sheet_direct`, `independent_frames`, or `hybrid` from speed and continuity risk, then verify the approved sequence or board.

## Session Improvement Loop

After completing the user's image-spec or prompt task, briefly review concrete friction from that use: user corrections, validation or compilation failures, ambiguous schema guidance, missing platform rules, or repeated manual workarounds.

- Propose an optimization only when the issue is evidenced, reusable, and within this Skill's scope. Do not generalize a one-off preference, an unverified model failure, or a provider limitation into a universal rule.
- If there is a credible improvement, finish the requested deliverable first. Then report the observed problem and evidence, its impact, the smallest proposed Skill change, affected files, and how the change would be tested. Ask whether the user wants `$jingzao-image-forge` optimized now.
- Do not edit the development source, installed copy, tests, or references without the user's explicit approval for that optimization. Approval to create or edit an image prompt is not approval to modify the Skill.
- When approved, use `$skill-creator`, update the development source, run structural validation, specification validation, regression tests, and relevant platform compilation checks, then sync the installed copy only after those checks pass.
- Do not persist user images, private prompt content, temporary session state, or unsupported guesses as Skill guidance. If no meaningful issue was observed, do not ask an optimization question.

## Delivery Contract

Return the smallest useful set of artifacts:

- assumptions or missing inputs marked `未验证`;
- structured JSON when precision or reuse justifies it;
- one platform-ready prompt;
- separate negative prompt or exclusion controls only when supported;
- separate parameters and warnings;
- exact preservation and change constraints for edits.
- global style locks, per-frame cards, reference assignments, and assembly instructions for `styleboard`.

Do not claim an image was generated, a style was matched, or an edit is pixel-accurate without tool output or visual verification. Do not silently add brands, logos, people, text, products, or story elements.
