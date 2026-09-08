# Jingzao Image Forge — Reference-Image Distillation & AI Image Prompts for Codex

**Carry the details of a reference into your next image.**

Jingzao Image Forge (镜造 Image Forge) turns an image brief and selected reference evidence into an inspectable visual specification, platform-ready prompt, and review criteria. It helps keep the decisions that often drift—hair colour, expression, gaze, action, visible body design, wardrobe, camera, light, material, and required text—explicit and reviewable.

[简体中文](README.zh-CN.md) · [Skill instructions](SKILL.md) · [Practical guide](docs/guide.md) · [AI-readable project map](llms.txt) · [Project-presentation research](docs/research/project-presentation-20260908.md)

[![Validate](https://github.com/papperrollinggery/jingzao-image-forge/actions/workflows/validate.yml/badge.svg)](https://github.com/papperrollinggery/jingzao-image-forge/actions/workflows/validate.yml)

![Jingzao Image Forge v1.10 overview: reference distillation and AI image prompts](assets/jingzao-v1.10-overview-en.png)

<sub>New introduction artwork; actual generated samples and facet-level reviews appear below.</sub>

## New in v1.11: Lilac Material Reveal

Transfer lilac-white studio depth, controlled dark-shell reflections, distinct dry-pigment/fiber materials and product-led element effects to new products. Artist pastels, an electronics array and a contact macro were tested. The refined pastel still has some coarse particles; the record retains initial failures and actual canvas sizes.

| Electronics without powder effects | Dry-pigment contact macro |
|---|---|
| ![Black-shell woven speakers in a lilac-white product array](assets/gallery/lilac-speaker-wide-v1.11.png) | ![Fine black fibers contacting a lilac dry-pigment block](assets/gallery/lilac-fiber-contact-v1.11.png) |

[Style guide and research method](references/lilac-material-reveal.md) · [Refined pastel sample](assets/gallery/lilac-pastel-refined-v1.11.png) · [Five generation/refinement records](tests/forward-evidence/lilac-material-reveal-review.json)

## Start here

Install into the user-level Codex Skills directory:

```bash
git clone https://github.com/papperrollinggery/jingzao-image-forge.git ~/.codex/skills/jingzao-image-forge
cd ~/.codex/skills/jingzao-image-forge
python3 scripts/verify_install.py . . --ref HEAD
```

`match` from `verify_install.py` checks the tracked files and symlinks against the resolved Git commit. Start a new Codex task before checking Skill discovery; an install check does not show that an already-open task adopted the Skill.

For a natural request, call the Skill directly:

```text
$jingzao-image-forge Create a 21:9 film-frame key visual from this brief.
Return a visual_generation_spec, an OpenAI-ready prompt, and the review points.
```

For an existing specification, compile an OpenAI prompt:

```bash
python3 scripts/compile_prompt.py tests/forward-specs/minimal-product-neutral.json --platform openai
```

The v1.10 reference-profile route adds selected visual evidence before compilation:

```bash
python3 scripts/compile_prompt.py SPEC.json \
  --reference-profile PROFILE.json \
  --platform openai
```

`--reference-profile` and `--style-capsule` are mutually exclusive. The former projects selected, observable reference evidence into the target; the latter applies reusable style rules while keeping the target specification authoritative. See [the guide](docs/guide.md#reference-profiles-v110) for the contract and [the prompt compiler reference](references/prompt-compiler.md) for the provider output.

## What it helps you make

- A maintainable `visual_generation_spec` for a new image, edit, restyle, expansion, cinematic frame, styleboard, or production image requirement.
- A reference profile that separates what is observed, unknown, preserved, adapted, omitted, or not applicable across 14 facets: `face_design`, `hair`, `makeup`, `expression`, `gaze`, `pose`, `action`, `body`, `wardrobe`, `camera`, `lighting`, `palette`, `surface`, and `environment`.
- Platform-ready prompt packages for OpenAI, FLUX, Midjourney, or a generic output, without inventing provider controls.
- Reusable, source-image-free style capsules with explicit transfer boundaries.
- Visible-state and camera requirements for film or video pre-production image coverage.

Jingzao is designed for practical still-image work: character and wardrobe studies, product and material images, architecture, key art, narrative frames, action, interface-state boards, and reference-aware edits. It scales the structure to the brief; a simple request does not need a full production package.

| Mode | Use it for |
| --- | --- |
| `create` | A new image from a brief. |
| `reconstruct` | Observable relationships from an actual source image. |
| `edit` | A named local change with explicit preservation. |
| `restyle` | A new treatment while source content stays authoritative. |
| `expand` | New canvas edges with source-bound continuity checks. |
| `learn_style` | Reusable visual rules with transfer boundaries. |
| `styleboard` | Related cinematic frames or interface states. |

## Reference evidence, without pretend certainty

A reference image can carry different responsibilities. A reference profile records the responsibility before it becomes prompt prose. For each of the 14 facets, it captures evidence, a decision, an optional positive projection, and a review check. `unknown` stays unknown; it is not promoted into a preserved fact.

For `attached` profiles, the named source must also be a real `must_attach: true` input in the target specification. The compiled package can describe a handoff plan, but a description is not a delivered image. For `text_transfer`, the profile must not claim an attachment was sent.

This keeps three things separate:

1. **Observed evidence** — what a reviewer can actually see in the source.
2. **Creative selection** — what the target should preserve, adapt, omit, or leave unresolved.
3. **Execution and acceptance** — whether a real input was sent, and whether the returned image meets the intended visual checks.

<a href="assets/gallery/cream-rose-text-profile-v1.10.png"><img src="assets/gallery/cream-rose-text-profile-v1.10.png" width="220" alt="Public cream-rose text-only reference-profile refinement: platinum fringe, ivory headwear, layered clothing, rose background, and fingertip-to-cheek pose"></a>

**Public v1.10 refinement sample.** This text-only profile trial returned an image and improved fingertip-to-cheek contact and plain hanging ribbons relative to its first text-only attempt. It remains a partial result: the fringe is looser and grayer than the source, the headwear reads as lace rather than folded jacquard, and its top is cropped. [Open the full-size image](assets/gallery/cream-rose-text-profile-v1.10.png) · [Read the visual-review evidence](tests/forward-evidence/reference-profile-style-review.json)

Two attached-reference close portraits also retained their main reference traits. An additional window-side body/hand-interaction call was input-blocked without an image. The successful calls do not replay the previously blocked inputs unchanged.

## A small DIR handoff for moving-image preparation

When a still-image package supports a video project, Jingzao can carry only the image-side handoff: a visible state, camera proof, reference roles, prompt, and review points. The surrounding method is:

`video evidence → mechanism and controls → still-image specification → visual review`

The first stage can use `video-evidence-workbench`; the mechanism/control stage can use `film-breakdown-distiller`; Jingzao owns the still-image portion. Those external Skills are optional. The reusable guidance lives in this repository's [production coverage](references/production-coverage.md), [shot design](references/cinematic-shot-design.md), and [quality controls](references/quality-controls.md).

## Capability boundaries

- Jingzao guides the image tools available in the current Codex host to generate and review images. Its Python scripts compile specifications and prompts; they are not an independently hosted rendering service.
- A valid JSON file, a successful command, a declared attachment, or a provider call plan is not visual acceptance.
- The project does not promise that a prompt will pass a provider's policy checks, reproduce an identity, preserve pixels, or produce the same result twice.
- Provider behavior, current controls, and model availability can change. Recheck a provider's current documentation before relying on a provider-specific route.

## Go deeper

The concise entry point deliberately links outward instead of hiding the technical material.

| Need | Read |
| --- | --- |
| Reference-profile contract, current cases, and historical asset index | [Practical guide](docs/guide.md) · [Reference distillation](references/reference-distillation.md) |
| Specification fields | [Visual specification](references/visual-spec.md) |
| Prompt compilation and provider boundaries | [Prompt compiler](references/prompt-compiler.md) |
| Reconstruct, restyle, and expand | [Reference modes](references/reference-modes.md) |
| Style learning and capsules | [Style learning](references/style-learning.md) · [Style capsules](references/style-capsules.md) |
| Film stills and coverage | [Production coverage](references/production-coverage.md) · [Cinematic shot design](references/cinematic-shot-design.md) |
| Clean rendering and visual review | [Quality controls](references/quality-controls.md) · [Image diagnostics](references/image-generation-diagnostics.md) |
| Existing examples and retained evidence | [examples/](examples/) · [tests/](tests/) |

**Release checks:** 255 automated tests, the complete local CI workflow, four-platform reference-trait projection, and independent code/visual review. Automated checks cover structure, compatibility and evidence binding; image quality is reviewed separately.

## Historical material

Earlier introduction graphics and gallery cases remain available from [the historical-material index](docs/guide.md#historical-material). They are isolated from the v1.10 entry image because they document earlier workflows and evidence conditions. They do not stand in for a v1.10 generation result.
