---
name: jingzao-image-forge
description: Create, reverse-engineer, edit, restyle, expand, learn reusable styles from reference images, or build styleboards using a structured visual specification and platform-aware compilation. Use when adaptive clean first-pass rendering, dynamic prompt budgeting, visual direction, cinematic/action shots, camera/lens/distortion, spatial tension, professional color and film finishing, Blender/Unreal/CG render behavior, product, fashion, architecture, illustration, animation, documentary, experimental art, giant-scale spectacle, Chinese fantasy, material quality, prompt-contamination cleanup, or cross-model prompt delivery must be controlled; this skill prepares prompts and specifications but does not itself generate images.
---

# 镜造 Image Forge

Turn an image brief or observed reference into a maintainable visual specification, then compile it for the user's target image system.

## Workflow

1. Classify the operation as `create`, `reconstruct`, `edit`, `restyle`, `expand`, `learn_style`, or `styleboard`.
2. Read or inspect every supplied image before describing it. Never infer image contents from a filename or prior summary.
3. Preserve the user's exact facts: subject count, names, actions, spatial relationships, visible text, aspect ratio, dimensions, reference roles, and forbidden elements.
4. Detect exact named entities whose existing model knowledge may improve the result. Preserve them verbatim as optional `knowledge_anchors`; do not replace them with generic feature inventories.
5. Establish a brief-grounded purpose before inventing a scene: intended use, audience, viewer conclusion, and the visible event or product promise. Do not create a narrative, location, interaction, or character merely to make unrelated references appear in one image.
6. Admit only references that make a necessary visual decision for that purpose. User-required assets remain required; when their roles do not form one coherent image, explain the conflict and split the work rather than forcing a synthetic integration scene.
7. For a simple single-subject creation, a concise prompt may be enough. For multi-subject scenes, reference-based work, exact layouts, or edits, build a `visual_generation_spec` using [templates/visual-spec.json](templates/visual-spec.json) and read [references/visual-spec.md](references/visual-spec.md).
8. Separate invariants from permitted variation through mode contracts and `constraints.must_preserve` / `must_change`. Legacy `control.weight`, `lock`, and `variance` remain accepted for compatibility but are deprecated, ignored by compilation, and should not be added to new specifications.
9. For edits, state both the smallest requested change and the preserve list. Normalize points and regions to top-left-origin percentages. A point such as `(x: 16.5%, y: 16.4%)` is an anchor, not a guarantee of pixel-accurate masking.
10. Compile the specification with `scripts/compile_prompt.py` or follow [references/prompt-compiler.md](references/prompt-compiler.md). The compiler normalizes placeholders, removes known duplicated color ownership, preserves every explicit non-empty source field, and reports `prompt_metrics` plus a dynamic `prompt_review`. The review target grows from observable semantic complexity instead of one fixed word count; it is never a model limit and never truncates requested camera, relationship, color, film, material, render, reference, edit, or preservation controls.
11. Do not call ImageGen while `prompt_review.status` is `blocked` or `review_required`. Context residue must be rewritten and recompiled; it cannot be approved through. Nonblocking length, reference-complexity, or surface-risk review may be explicitly accepted with `--approve-review` only after confirming the prompt is clean and the style core is intact. Before delivery, run the bundled fast gate in [references/prompt-hygiene.md](references/prompt-hygiene.md); use its full source trace, semantic ledger, deletion test, and stateless-generator read for complex multi-section prompts, contaminated retries, or repeated action/effect language. This bundled workflow is self-contained for GitHub installs. If `$prompt-contamination-guard` is also installed, it may provide an optional second audit, but its absence must not reduce capability or block delivery. Protect the active style core; remove contamination and repetition, not unique design detail.
12. Run `scripts/validate_spec.py` and `scripts/prompt_lint.py` before delivery. Review the result against [tests/evals.md](tests/evals.md) when consistency or exact edits matter.
13. Keep execution proof and image quality separate: a correct attachment receipt proves only that inputs reached the tool. Before calling an image deliverable-quality, verify creative purpose, visual meaning, anatomy, interaction physics, and scenario-specific success.

## Progressive Detail and Minimal Intervention

Treat the template as a neutral scaffold, not a request to fill every field.

- Start with only the brief-grounded core: intended result, subject or visible event, environment when needed, requested medium, explicit canvas, and hard constraints.
- Leave canvas, subject coordinates, camera, film finishing, render transport, and optical artifacts at `auto` or empty when the brief and observed references do not require them. A non-empty generation prompt with `render.artifact_budget: auto` emits only the adaptive preventive clean base; it must not silently choose 16:9, a camera, grain, bloom, flare, gloss, particles, or a new medium. An empty template and `learn_style` analysis emit no clean base.
- Add a professional section only when it solves a current visual decision: narrative staging, extreme action geometry, hand/object mechanics, strict color continuity, named CG behavior, reference reconstruction, or another explicit requirement.
- Explicit non-empty user or specification values remain authoritative and compile normally. Minimal intervention controls automatic enrichment; it must not erase requested focal length, distortion, film behavior, material transport, stylization, or other intentional design.
- Use a deletion test before delivery: if removing a clause would not change a requested fact, visible decision, preservation rule, or diagnosed failure, omit it from the first-pass prompt.
- Correct observed failures with the smallest relevant addition. Do not promote one retry phrase, model accident, or stylistic preference into a universal default.

## Adaptive Clean Base and Dynamic Prompt Budget

Every non-empty generation prompt using `render.artifact_budget: auto` receives one compact positive clean base. It assigns every texture to the requested medium or a named material; only **localized** texture or surface variation must have an explicit spatial owner and stay inside its named region rather than spreading as filler microtexture. Highlights/reflections/contact shadows remain tied to surface geometry and motivated light, non-focal surfaces stay low-frequency, and every intentional medium trait already stated by the brief or source remains protected. It does not name grain, brushwork, patina, wear, wetness, or optical artifacts unless the current specification already does. This is preventive prompt shaping, not an oil-spot detector and not a universal matte finish.

The compiler classifies the prompt as `concise`, `standard`, `complex`, `sequence`, or `analysis` and derives a review target from active semantic sections plus subjects, required references, materials, causal effects, exact text, styleboard frames, constraints, and an applied style capsule.

- The platform profile supplies a minimum and maximum **review target**, not an API limit.
- Length review uses `prompt_metrics.review_units`: ordinary whitespace word counts remain compatible, while CJK text is estimated at roughly two CJK characters per review unit so unspaced Chinese/Japanese/Korean text cannot bypass review.
- A complex prompt may legitimately receive a larger target; a long single-clause prompt does not gain budget merely by repeating words.
- Exact duplicate structured subjects, materials, effects, text elements, frames, or constraints do not increase complexity units.
- No compiled prompt is shortened automatically. If it exceeds the dynamic target, remove duplication or low-priority source clauses and recompile while preserving every unique current fact.
- `scripts/prompt_lint.py --max-words` remains a fixture-specific CI ceiling for detecting accidental regression; it is not the model-facing budget.
- Generic surface-risk phrases such as `ultra detailed`, `micro detail everywhere`, `wet glossy`, or `beautiful lighting` require review outside literal `text_elements.content`. Rewrite them as focal detail, material ownership, wet/dry boundaries, and named light before generation.

## Actual Reference Handoff

When the user supplies character, wardrobe, product, logo, prop, location, composition, or style images, the actual images must reach the generation/edit tool. A prose description of a supplied image is not a substitute.

Read [references/reference-delivery.md](references/reference-delivery.md) for multi-image tool handoff and preflight.

- Record each image's real source in `inputs` with `source_kind`, `source_ref`, and `must_attach: true`; keep the role in ordinary language.
- Before built-in ImageGen execution, run `scripts/reference_delivery.py <spec> --target codex_imagegen`. Missing or unresolved images, more than five required references, mixed local/conversation mechanisms, and unconfirmed conversation windows block execution. The five-image limit and mutually exclusive mechanisms were verified against the bundled Codex ImageGen contract on 2026-08-19 and must be rechecked when that tool changes.
- For built-in `$imagegen`, inspect local files with `view_image`, then pass every required local file through `referenced_image_paths`. When required images exist only in the conversation, confirm immediately before the call that they are the latest contiguous image window, then use the smallest `num_last_images_to_include` that contains all of them. Conversation-image selection is best-effort until stable image references exist.
- For multiple images, tell the model what each image contributes: character identity, wardrobe, product, logo, prop, scene, composition, camera, palette, or style. State what should remain unchanged in the normal prompt; do not invent a separate policy layer.
- Do not turn attachment count into a composition requirement. A pipeline stress test may verify five delivered files without demanding that five unrelated roles become simultaneously visible in one finished image. Creative forward tests start from a coherent brief and use only its necessary references.
- If the user explicitly requires several assets in one image, first verify that their roles support one real delivery context. When they do not, report the conflict or propose separate deliverables; do not invent an arbitrary handoff, event, location, or story to make the set fit.
- Compare the execution-ready `imagegen_call_plan` with a receipt containing the actual mechanism, sent input IDs/count, tool call ID, and output reference. For local images this may be the compiler plan; for conversation images it is the execution-time preflight plan after confirming the recent window. If expected and sent inputs do not match, report `reference delivery unverified`; do not call the result reference-backed. Public evidence uses a sanitized call-ID hash and repository-relative output path; raw paths, URLs, tokens, session/thread IDs, and cursors remain local.
- If the tool call cannot include a required image, stop and report the missing attachment instead of silently generating from text.
- GPT Image 2 processes image inputs at high fidelity automatically; do not invent an `input_fidelity` control.
- Logo, clothing marks, product appearance, and character continuity are visually verified after generation. If they fail, revise reference roles or use the model's image-edit path and retry. Do not hide the failure with post-generation compositing; this is a generation Skill, not a compositing Skill.

## Creative Validity and Interaction Physics

Reference compliance is not creative validity. A technically successful multi-image call may still produce a meaningless scene, an implausible action, or unusable commercial work. Apply this section before writing the scene and again during visual review.

- Derive the delivery context and intended viewer conclusion from the user brief or project facts before combining references. A narrative image needs a grounded visible event and relationship change; a campaign or product image needs a product promise, use context, or communication task; a technical study needs an observable question. Do not manufacture these answers merely to satisfy a test.
- Every included subject, product, prop, location, and style reference must support that purpose. Do not invent a scene merely to force unrelated reference roles into one frame.
- For hand-object or body-object interaction, verify affordance and mechanics: which hand bears weight, where fingers wrap or support, wrist alignment, center of mass, counterforce, contact/occlusion, body balance, and the frozen action phase. Reject ambiguous floating, pinching, duplicated, contested, or anatomically impossible contact.
- Separate reference-delivery stress tests from creative forward tests. The former proves attachment mechanics only and should not request or publish a synthetic showcase image; the latter begins with a coherent real use case and must pass purpose, interaction, anatomy, and visual communication.
- If the creative premise is wrong, redesign the scenario from the brief. Do not spend retries polishing an image whose use or meaning cannot be explained.

## Knowledge-Aware Generation

Use this route when a request names a recognizable character, person, work, historical event, place, artifact, product, or fictional-world element.

- Default to adaptive `auto`: use the exact named entity as a compact first-pass anchor; select `reference` or `hybrid` only when supplied references or version-specific accuracy justify them.
- For GPT Image 2 or the built-in `$imagegen` path, place the exact entity and requested incarnation, period, or medium before scene detail. Let the model use its existing world knowledge instead of expanding the name into a long generic description.
- Treat cinematic framing, scale, and lighting as composition language. Do not silently convert animation, illustration, game art, or another stated medium into live action.
- Keep the maintainable specification detailed, but compile a clean first-pass prompt. Add detail only when it disambiguates the named entity or corrects an observed failure.
- If `$imagegen` returns a revised prompt, check that the exact anchor, incarnation, and medium survived the rewrite before accepting the output.
- If identity or canonical appearance fails, prefer a corrected fresh generation or a suitable identity reference over a local edit to a small subject. Label reference roles and use only references that match the requested version closely enough.
- Model knowledge is a generation aid, not verification evidence. Label canonical accuracy `未验证` in prose and set `verification: "unverified"` in the specification until checked against a trusted visible reference or confirmed by the user.

## Artifact and Material Quality

For premium, clean, photorealistic, product, portrait, dark-scene, or dense fantasy work, run a compact quality preflight. Read [references/quality-controls.md](references/quality-controls.md) when an output looks noisy, speckled, waxy, oily, over-sharpened, excessively glossy, flare-heavy, or uniformly over-processed.

- Keep `render.artifact_budget: auto` for the adaptive preventive clean base on ordinary first passes. Select `strict`, `balanced`, `clean_reset`, `expressive`, or `source_matched` only when the medium, source, delivery risk, or an observed artifact justifies that preset. An explicit preset replaces rather than stacks with the clean base.
- A repeated dirty-output report is demonstrated risk, not a neutral first pass. Set `render.artifact_budget: clean_reset`, rebuild from a clean specification, and preserve only the subject, composition, medium, palette, and essential relationships. Do not use repeated image-to-image cleanup unless exact source geometry matters more than residue carryover.
- Define material-specific roughness, highlight width, reflection, texture scale, and contact behavior before adding generic quality adjectives.
- Assign texture ownership before adding microdetail: establish 3–7 dominant low-frequency shape groups, one or two focal-detail clusters, and at least one continuous calm surface. Reserve full clarity for camera-readable focal surfaces; make support and depth zones lose edge frequency, texture frequency, and contour completeness through distance, light, focus, atmosphere, or occlusion.
- Keep ambient occlusion and contact shadows local to real seams, overlaps, creases, and support points. Separate glossy, matte, wet, and dry regions by material response; never use global sheen or contour grime as a depth shortcut.
- Bloom, lens flare, grain, floating particles, sparks, and gloss require a visible light source, requested medium, physical event, or source-image precedent. Otherwise keep them restrained.
- Prefer positive visible targets plus one compact current-risk avoid block. Do not preserve a history of old failed objects or styles in negative constraints.
- For dirty-output retries, regenerate from a clean specification when practical. Repeated image-to-image cleanup can preserve or amplify unwanted residue; use editing only when the user needs the original structure preserved.
- Before calling an output deliverable-quality, inspect it both at thumbnail scale and at 100%. Fail the clean-surface gate if large calm masses disappear, non-focal areas carry equal microtexture, highlights become oily/plastic, AO becomes a dirty halo, darks fill with noise, or random dots/text-like marks survive. Freeze passing controls and change one main variable per retry.

## Visual Intent Router

After choosing the operation mode, analyze what the image must do. Do not collapse “cinematic,” “artistic,” “spectacular,” and “fantasy” into one poster-like treatment.

- **Creative route:** choose one primary scenario, genre family, aesthetic family, capture/render method, and up to three scene archetypes. For product, fashion, food, architecture, environment, vehicle, creature, history, science, interface, game, event, social, or experimental work, read [references/scenario-profiles.md](references/scenario-profiles.md).
- **Aesthetic system:** choose one primary aesthetic family and at most one scoped secondary influence. Read [references/visual-style-atlas.md](references/visual-style-atlas.md) for cinematic naturalism, noir, expressionism, surreal/dream, romantic sublime, modernist graphic, retro analog, luxury editorial, handcrafted, painterly, animation, documentary, speculative, minimal, archival, and mixed-media routes.
- **Style authority:** state whether the user brief, source reference, learned capsule, or source-matched image owns the tone. Scenario adaptation may change camera and content strategy, but explicit medium, palette, color pipeline, material hierarchy, and `tone_locks` must survive unless the user requests a change.
- **Deliverable:** `narrative_film_frame`, `cinematic_key_art`, `poster`, or `concept_art`. Story moments, relationships, reactions, decisions, and implied before/after favor a narrative frame; marketing, cover, hero, title-led, or showcase language favors key art or poster.
- **Treatment:** `grounded_cinematic`, `heightened_cinematic`, or `graphic_stylized`. Grounded choices remain physically filmable; heightened choices may exaggerate perspective, color, optical behavior, or composition when the viewer effect is explainable; graphic treatment may use designed shape, line, 2D/3D layering, and impossible camera logic while preserving spatial readability.
- **Spectacle scale:** `intimate`, `dramatic`, `monumental`, or `mythic`. Scale changes camera placement, human/environment ratio, atmosphere, occlusion, environment response, and information density—not merely the adjective “epic.”
- **Genre logic:** record the world rule that governs the shot. Chinese fantasy, xianxia, mythology, giant creatures, science fiction, product work, and documentary realism require different effect, material, and camera assumptions.
- **Camera freedom:** `physical`, `heightened`, or `impossible`. Use the least impossible level that achieves the user's requested result.

For substantial cinematic, artistic, spectacle, giant-scale, or Chinese-fantasy work, read [references/direction-profiles.md](references/direction-profiles.md). Preserve the user's medium and desired exaggeration; realism is a choice, not a universal quality gate.

## Shot Tension and Spatial Dynamics

For battles, action, performance, fashion movement, giant scale, extreme angles, beautiful hero shots, or deliberate distortion, read [references/shot-tension-design.md](references/shot-tension-design.md).

- Define dominant and secondary reads before adding detail.
- Map the action vector, counterforce, frozen phase, motion evidence, and readability guard.
- Give foreground, midground, and background different functions; use occlusion and parallax to prove viewer position, speed, scale, or pressure.
- Select one exaggeration budget and one distortion strategy. State the realism or spatial anchor that prevents random deformation.
- Couple focal length with camera distance, pitch/yaw/roll, lens projection, edge behavior, crop pressure, and camera state.
- Treat beauty as hierarchy, silhouette, negative space, color/value separation, material contrast, depth rhythm, and controlled visual rest—not as the word “beautiful.”
- For object handling, bind action, grip/support, weight, counterforce, wrist/body balance, and contact visibility to the chosen frozen phase; hands are not decorative endpoints.

## Professional Color and Film Finishing

When grading, film stock character, color continuity, skin tone, archival reproduction, or a cinematic look matters, read [references/color-pipeline.md](references/color-pipeline.md).

- Separate color science/display intent from the creative grade.
- Define exposure, tonal curve, black/white points, highlight rolloff, shadow floor, midtone density, white balance, color separation, skin-tone protection, saturation, and gamut behavior.
- For film emulation, separate negative/reversal character, print/display character, grain, halation, bloom, gate weave, flicker, and vignette. Use only the artifacts the requested medium needs.
- Do not use generic teal/orange, crushed blacks, clipped highlights, uniform grain, or global halation as universal cinema quality.
- Lock the color pipeline across shots while allowing story-motivated day/night, location, memory, threat, or subjective changes.

## Render Pipeline and Material Transport

For Blender, Unreal Engine, RenderMan, Arnold, V-Ray, Octane, Redshift, ray/path tracing, global illumination, real-time CG, NPR, or material-heavy work, read [references/render-pipeline.md](references/render-pipeline.md).

- Label an engine name as `appearance_reference` unless an actual engine pipeline is in scope; a prompt cannot prove engine execution.
- Define light transport, global illumination, ray tracing, reflection/shadow/AO, volumes, subsurface, transmission/refraction, caustics, displacement/normal behavior, texture scale, sampling/denoise, and passes only when visible and useful. These remain single-generation appearance controls, not a post-generation assembly workflow.
- For each hero material, specify microstructure, roughness, specular response, transmission, subsurface behavior, anisotropy, wear/patina, and contact/deformation as relevant.
- Prevent plastic uniform roughness, floating contact, over-dark AO, light leaks, fireflies, texture-scale mismatch, and denoise-smudged detail.

## Reference Style Learning

Use `learn_style` when the user wants an actual supplied image converted into a reusable style system. Read [references/style-learning.md](references/style-learning.md). For reviewed built-in capsules and their evidence, read [references/style-capsules.md](references/style-capsules.md).

- Inspect the image; do not infer style from the filename, prompt history, or user summary alone.
- Separate directly observed mechanisms from production inferences and unknowns.
- Extract medium behavior, palette ownership, shape/line language, texture/material logic, lighting, composition, typography, optics/rendering, and limited recurring motifs.
- Write transfer rules and forbidden transfer rules. Do not learn subject identity, faces, exact text, logos, signatures, protected character design, or exact layout coordinates as style.
- Export a source-image-free `style_capsule` with `scripts/create_style_capsule.py`; review its advisory content-risk warnings and validate it with `scripts/validate_style_capsule.py`.
- Test a capsule on at least two materially different subjects or scenarios before marking it `validated` or `adopted`. Bind each test to a non-image evidence record (`case_id`, prompt index, scenario, evidence reference, review); raw private references remain uncommitted. Applying a capsule is not evidence that the style transferred successfully; inspect the generated images.
- A draft capsule may be created automatically as the current deliverable. Durable inclusion in the installed or public Skill requires user approval, and raw private references are never embedded.

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

For `reconstruct`, `restyle`, or `expand`, read [references/reference-modes.md](references/reference-modes.md).

- `create`: Describe the desired result directly; add exclusions only when they prevent a likely failure.
- `reconstruct`: Supply `reference_analysis` with a target, directly observed facts, clearly marked inference, and explicit unknowns. Reproduce observable visual attributes, not an unknowable original prompt or software pipeline.
- `edit`: Use “change only” plus explicit invariants. Prefer one meaningful change per iteration.
- `restyle`: Require both `must_preserve` and `must_change`; lock geometry, identity, pose, layout, and text unless the user says otherwise, and vary only the named visual treatment.
- `expand`: Require both `must_preserve` and `must_change`; preserve original content, subject relative position/scale, perspective, exposure, and source boundaries, then describe only the new edges and crop-safe continuity. Continuity alone is not a PASS when anchor, scale, or target ratio drifts.
- `learn_style`: Analyze actual reference pixels, create a draft style-learning record, export a source-image-free capsule with reviewed transfer boundaries, and validate transfer across different content before adoption.
- `styleboard`: Analyze reference roles, define a visual master and frame cards, choose `sheet_direct`, `independent_frames`, or `hybrid` from speed and continuity risk, then verify the approved sequence or board.

## Session Improvement Loop

After completing the user's image-spec or prompt task, briefly review concrete friction from that use: user corrections, validation or compilation failures, ambiguous schema guidance, missing platform rules, or repeated manual workarounds.

- Propose an optimization only when the issue is evidenced, reusable, and within this Skill's scope. Do not generalize a one-off preference, an unverified model failure, or a provider limitation into a universal rule.
- If there is a credible improvement, finish the requested deliverable first. Then report the observed problem and evidence, its impact, the smallest proposed Skill change, affected files, and how the change would be tested. Ask whether the user wants `$jingzao-image-forge` optimized now.
- Do not edit the development source, installed copy, tests, or references without the user's explicit approval for that optimization. Approval to create or edit an image prompt is not approval to modify the Skill.
- When approved, use `$skill-creator`, update the development source, run structural validation, specification validation, regression tests, and relevant platform compilation checks, then sync the installed copy only after those checks pass.
- Keep every long-running review, generation test, or delegated audit as an active plan item until it returns a terminal status and its result/evidence files are read. Record the task/session identifier and latest cursor; poll or wait every 30–60 seconds, continue safe independent work between checks, and never rely on the user to ask whether it finished.
- An unchanged running status is not completion or failure. Do not broadcast empty polls, but do not drop the follow-up obligation. If a tool returns an error, preserve the actual error and use only documented recovery paths.
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
- observed/inferred/unknown separation, transfer boundaries, and a validated `style_capsule` for `learn_style`.

Do not claim an image was generated, a style was matched, or an edit is pixel-accurate without tool output or visual verification. Do not silently add brands, logos, people, text, products, or story elements.
