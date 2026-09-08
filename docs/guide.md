# Jingzao Image Forge practical guide

The [README](../README.md) is the short entry point. This guide keeps the longer technical map, reference-profile contract, current evidence links, and historical links reachable without asking a new user to read a gallery before they can install or use the Skill. For the complete observation method, read [Reference distillation](../references/reference-distillation.md).

## Reference profiles (v1.10)

A `reference_profile` is a small, reviewable record between an image reference and a target `visual_generation_spec`. It answers two different questions separately:

1. What can actually be observed in the source?
2. What should the target preserve, adapt, omit, or leave unresolved?

The compiler projects only the facets selected for the target into positive prompt language. It does not convert unknown pixels into a claim about identity, a camera setting, a material, or a hidden production fact.

### Facets

Every profile supplies these 14 facet IDs exactly once:

```text
face_design, hair, makeup, expression, gaze, pose, action,
body, wardrobe, camera, lighting, palette, surface, environment
```

Each facet has a source ID list, evidence state, observation, decision, optional positive `prompt`, reason, and `review_check`. The contract uses these states:

| Field | Values | Meaning |
| --- | --- | --- |
| `evidence` | `observed`, `partial`, `unknown`, `not_applicable` | What the source supports. |
| `decision` | `preserve`, `adapt`, `omit`, `unknown`, `not_applicable` | What the target does with the facet. |
| `review_check` | free text | The visible condition a reviewer checks in the result. |

`unknown` cannot be marked `preserve`. `adapt` needs a reason. A facet with `observed` or `partial` evidence names at least one source ID and carries a review check. This keeps the record useful for a real creative choice without treating it as a biometric or forensic inference system.

### Attachment rule

Use `reference_mode: "attached"` only when the source IDs appear once in the target specification's `inputs` and set `must_attach: true`. The profile declares an expected input; it is not a receipt that an executor sent one. Use `reference_mode: "text_transfer"` only when the reference-derived prose can be used without an attachment, and do not describe that route as an image handoff.

### Compile it

For v1.10, compile a target specification together with one profile:

```bash
python3 scripts/compile_prompt.py SPEC.json \
  --reference-profile PROFILE.json \
  --platform openai
```

The repository also includes a runnable attached-reference example:

```bash
python3 scripts/compile_prompt.py \
  tests/forward-specs/reference-profile-cream-rose.json \
  --reference-profile examples/reference-profile-cream-rose.json \
  --platform openai
```

`--reference-profile` and `--style-capsule` are mutually exclusive. Choose the profile when the target needs selected evidence from a particular reference. Choose a style capsule when the task needs a reusable visual method that remains subordinate to the target scene, subject, layout, text, and production method. Read [style capsules](../references/style-capsules.md) before using the latter.

Verify the installed revision's `--help` output before running the v1.10 route in a different checkout.

### Current reference-profile cases

The following records distinguish compilation from an actual returned image. They are small evidence samples, not a success-rate claim.

| Case | What happened | Evidence boundary |
| --- | --- | --- |
| Cream-rose attached profile | A new call with one actual corresponding reference returned an image; hair, expression, gaze, fingertip-near-cheek action, layered wardrobe, palette, and soft light were reviewed as retained. | `passed_with_concerns`; head tilt weakened and exact hand/headwear details differed. Output stays local. |
| Crimson attached profile | A new call with one actual corresponding reference returned an image; hair/eye-coverage relationship, gaze, wardrobe, palette, and controlled light were reviewed as retained. | `passed_with_concerns`; movement/support and precise garment hardware were not verified. Output stays local. |
| Cream-rose text-only refinement | A new call with no reference image returned the [public sample](../assets/gallery/cream-rose-text-profile-v1.10.png). It improved the fingertip contact and plain ribbons relative to the first text-only trial. | `partial`; fringe colour/shape and headwear material differ, and the top of the headwear is cropped. |
| Daylight-window | The spec/profile compiled and an actual attached-reference call was made. | `TOOL_BLOCKED` at input moderation; no image and no visual acceptance. |
| Daylight-seated | Its spec/profile compiles. | No generation trial; compilation only. |

Read the exact checks, hashes, output availability, and limits in [reference-profile visual-review evidence](../tests/forward-evidence/reference-profile-style-review.json). The four returned images do not replay previous blocked inputs unchanged, identify a provider-policy cause, validate full-body proportions, or establish that the older style-capsule route now works. That capsule remains a separate draft path.

## Common questions

### Does this preserve a person's hair, expression, gesture, or body?

It makes those choices explicit and gives each one a review check. A profile can preserve observable hair, expression, gaze, pose, action, visible body design, and wardrobe without claiming that the source person's identity has been copied or verified. If the source is a close portrait, full-body anatomy remains untestable.

### Can it create or edit an image?

The Skill can guide the current Codex host's available image tool through generation and review. The repository's Python scripts create specifications, prompts, attachment plans, and audits; they are not a standalone hosted renderer. A returned image still needs visual review against the chosen checks.

### Should I use a reference profile or a style capsule?

Use one reference profile for selected, source-specific visual evidence in the current image. Use one style capsule for reusable surface, palette, shape, material, lighting, hierarchy, or rendering rules that remain subordinate to a new target. The two CLI options are mutually exclusive. The legacy style-capsule route remains available, but its soft editorial capsule is still draft and was not validated by the new reference-profile trials.

### Did this change the upstream DIR workflow?

No. Jingzao incorporates a limited image-side method and optional handoff guidance. It does not add a `--reference-profile` field to an upstream DIR executor or claim an upstream execution test.

## What the prompt compiler does

The source of truth is a `visual_generation_spec`, not a disposable one-line prompt. It can carry scene, subjects, camera, lighting, materials, visible text, preserve/change constraints, required inputs, and review criteria. `scripts/compile_prompt.py` serializes that source for OpenAI, FLUX, Midjourney, or a generic provider output.

```bash
python3 scripts/compile_prompt.py examples/atomic-cyber-live-action.json --platform openai
python3 scripts/compile_prompt.py examples/atomic-cyber-live-action.json --platform flux --format text
python3 scripts/compile_prompt.py examples/atomic-cyber-live-action.json --platform midjourney
```

Provider-specific fields are output guidance, not proof that a provider accepted them. The compiler does not generate images or turn a call plan into an execution receipt. Detailed field behavior and current provider boundaries are in [Prompt compiler](../references/prompt-compiler.md).

## Reference-aware image work

Use the mode that matches the requested change:

| Mode | Goal | Primary reference rule |
| --- | --- | --- |
| `create` | Make a new image from a brief. | Add references only when they have a clear role. |
| `reconstruct` | Rebuild observable relationships. | Separate `observed`, `inferred`, and `unknown`. |
| `edit` | Change a named local area. | State what changes and what stays fixed. |
| `restyle` | Change treatment while source content stays authoritative. | Preserve identity, pose, camera, crop, geometry, layout, and text as required. |
| `expand` | Extend the canvas. | Check subject position, frame-height ratio, vanishing points, and edge continuity. |
| `learn_style` | Distill reusable visual rules. | Use a source-image-free capsule with transfer exclusions. |
| `styleboard` | Plan several related frames or interface states. | State reference roles and continuity locks per deliverable. |

Read [Reference modes](../references/reference-modes.md), [Reference delivery](../references/reference-delivery.md), and [Visual specification](../references/visual-spec.md) before treating a source image as an execution input.

## Film and video pre-production handoff

Jingzao's scope stops at the image package: requirement, visible state, camera proof, reference roles, prompt, and image review. It does not take ownership of a screenplay, timing, dialogue, video-model selection, or the project ledger.

For a lightweight DIR-aligned handoff, use the following chain:

```text
video evidence → mechanism / controls → image-frame requirement → image review
```

`video-evidence-workbench` can produce traceable source observations. `film-breakdown-distiller` can turn those observations into an editable mechanism and control plan. Those external Skills are optional; the image-side guidance needed by Jingzao is available locally in [Production coverage](../references/production-coverage.md), [Cinematic shot design](../references/cinematic-shot-design.md), [Shot tension design](../references/shot-tension-design.md), and [Quality controls](../references/quality-controls.md). This repository does not modify or assert adoption by an upstream DIR executor.

For each still, check the camera and visible state, not merely whether the prompt includes film vocabulary. For a sequence, check identity, wardrobe, props, geography, light direction, screen direction, and object state as they advance.

## Technical reference map

| Topic | Reference |
| --- | --- |
| Core schema and field semantics | [Visual specification](../references/visual-spec.md) |
| Reference observation and projection | [Reference distillation](../references/reference-distillation.md) · [Reference-profile template](../templates/reference-profile.json) |
| Scenarios and route selection | [Scenario profiles](../references/scenario-profiles.md) · [Direction profiles](../references/direction-profiles.md) |
| Style selection and learning | [Visual style atlas](../references/visual-style-atlas.md) · [Style learning](../references/style-learning.md) · [Style capsules](../references/style-capsules.md) |
| Camera, action, and coverage | [Cinematic shot design](../references/cinematic-shot-design.md) · [Shot tension design](../references/shot-tension-design.md) · [Production coverage](../references/production-coverage.md) |
| Color, materials, and clean rendering | [Color pipeline](../references/color-pipeline.md) · [Render pipeline](../references/render-pipeline.md) · [Quality controls](../references/quality-controls.md) |
| Prompt hygiene and diagnosis | [Prompt hygiene](../references/prompt-hygiene.md) · [Image diagnostics](../references/image-generation-diagnostics.md) |
| UI and multi-frame boards | [UI motion storyboard](../references/ui-motion-storyboard.md) · [Styleboard mode](../references/styleboard-mode.md) |
| Existing structured examples | [examples/](../examples/) |
| Tests and retained verification material | [tests/](../tests/) |

## Historical material

These files are retained for people who need to inspect earlier project presentation or earlier example/evidence conditions. They are not the v1.10 release artwork and should not be presented as a current generation result.

### Earlier introduction graphics

- [Chinese workflow page, v5](../assets/jingzao-image-forge-intro-zh-v5.png)
- [Chinese workflow page, v4](../assets/jingzao-image-forge-intro-zh-v4.png)
- [Earlier English hero](../assets/jingzao-image-forge-hero-en.png)
- [Earlier Chinese hero](../assets/jingzao-image-forge-hero-zh.png)
- [Feature recommendation poster](../assets/jingzao-image-forge-recommendation-zh-v3.png)
- [WeChat group card](../assets/jingzao-image-forge-wechat-card-zh-v3.png)

### Earlier case material

- [Continuous nine-shot ferry specification](../examples/continuous-nine-shot-ferry.json)
- [UI motion storyboard specification](../examples/ui-motion-storyboard.json)
- [Causal fantasy effect specification](../examples/causal-fantasy-effect.json)
- [Crimson Nocturne style capsule](../references/style-capsules/crimson-nocturne-wuxia-montage.json)
- [Forward-test manifest](../tests/forward-test-manifest.json)

Read each example's own label and retained receipt before making an execution or visual-quality claim. A gallery image, static asset, or structural test result is not by itself evidence that an input was sent or that a current model output was accepted.

## Product material styles (v1.11)

[Lilac Material Reveal](../references/lilac-material-reveal.md) separates studio treatment from target-owned geometry and materials. Choose a hero/array, contact macro or material-release state before compiling; do not add powder effects to unrelated products. Three initial trials plus two refinements are documented with actual prompt suffixes, dimensions and visual limits.

```bash
python3 scripts/compile_prompt.py tests/forward-specs/lilac-speaker-array.json \
  --style-capsule references/style-capsules/lilac-material-reveal.json --platform openai
```

For a native tool accepting only a prompt and images, separately emitted compiler parameters must be explicitly handed off. Preserve the actual sent suffix and inspect the returned size; see [reference delivery](../references/reference-delivery.md).
