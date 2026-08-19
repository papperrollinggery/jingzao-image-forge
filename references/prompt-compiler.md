# Platform Prompt Compiler

This reference converts one visual specification into a provider-ready prompt. Keep the visual specification as the source of truth; provider prompts are disposable compiled outputs.

Platform behavior changes over time. The provider notes below were checked against official documentation on 2026-08-19. Recheck official documentation before executing an API call or promising parameter support.

## Shared Compilation Order

Use a stable order so prompts remain debuggable:

1. exact named-entity knowledge anchors and requested incarnation;
2. intent plus creative route: scenario, genre, primary aesthetic, capture/render method, scene archetypes, audience effect, and delivery context;
3. optional learned style capsule, explicitly subordinate to the target subject, scene, layout, text, and production method;
4. deliverable type, treatment, spectacle scale, genre logic, and camera freedom;
5. cinematic shot contract, viewer position, frozen moment, and staging when relevant;
6. scene and environment;
7. subjects, actions, relationships, and causal effects;
8. composition, camera motivation, focal-length rationale, and spatial placement;
9. spatial dynamics, camera/lens/distortion, and motivated lighting;
10. materials, color, professional color pipeline, render pipeline, and optics;
11. detailed style and realism;
12. compact artifact budget and shot-specific quality controls;
13. exact visible text;
14. requested edits or styleboard frame cards;
15. preservation and continuity constraints;
16. exclusions or provider-native negative controls;
17. generation parameters, kept outside prose when the provider supports them.

Derive priority from the operation mode, visible event, reference roles, exact text, and `must_preserve` / `must_change`. Legacy `control.weight`, `lock`, and `variance` remain accepted for compatibility but are ignored; never translate them into provider parameters.

## Prompt Normalization and Budget

The maintained specification may stay detailed, but the disposable compiled prompt is normalized per provider. When section content exceeds the review target, compact only lower-priority route, finishing, material-transport, optics, and secondary-style clauses. Never prune actual reference requirements, exact text, visible events, relationships, subject identity/action, camera/viewer geometry, edits, preserve/change invariants, or a causal effect's owner/contact/cost/response/residue chain.

Canonical ownership prevents repetition: when a full `color_pipeline` exists, `color` contributes palette ownership rather than a second grade/contrast/saturation system. `lighting` continues to own physical sources and direction; the color pipeline owns exposure, tone, white balance, display, and film finishing. The compiler removes known template placeholders, emits `prompt_metrics`, and reports every normalized section. `scripts/prompt_lint.py` provides deterministic fixture ceilings and leakage checks for CI; generated-image quality remains a separate manual forward test.

The compiler also emits `prompt_review`. `blocked` marks conversation-dependent residue outside exact visible copy and cannot be approved through. `review_required` marks length or reference complexity and must be reviewed before model execution; after confirming current-source cleanliness and style-core integrity, recompile with `--approve-review`. This flag never overrides `blocked` contamination. Four or more required references trigger review to verify necessity and prevent attachment count from becoming a simultaneous-visibility requirement. Use [Prompt Hygiene Without Style Flattening](prompt-hygiene.md): preserve medium, aesthetic, palette, material, camera, and intentional distortion while removing invented context, negative residue, repeated mechanisms, and conflicting anchors.

## OpenAI GPT Image

Use short labeled sections for complex prompts. State explicit framing, placement, pose, text, and material details. For edits, say `Change only ...` and `Keep everything else the same`, then restate the preserve list on every iteration.

OpenAI's current official guidance recommends `gpt-image-2` for new image generation and editing workflows. It supports generation and edits through the Image API, and conversational multi-turn image work through the Responses API. Keep `model`, `quality`, and `size` separate from prompt prose. Accepted quality values are `low`, `medium`, `high`, and `auto`.

`gpt-image-2` accepts flexible sizes, not a three-size allow-list. A concrete `WIDTHxHEIGHT` size must keep both edges at multiples of 16, each edge at or below 3840, long-to-short ratio at or below 3:1, and total pixels from 655,360 through 8,294,400; `auto` is also valid. The validator enforces these current constraints. A `learn_style` analysis compile emits no generation size because it is not an image-generation deliverable.

GPT image generation models can combine reasoning with world knowledge. For a named character, place, historical event, artifact, or fictional-world element, preserve the exact entity and version wording before the rest of the prompt. Start with a clean base prompt and refine through small single-change follow-ups; do not bury a useful entity anchor under speculative generic descriptors.

When the built-in Responses image-generation tool returns `revised_prompt`, inspect it before accepting the result. The exact knowledge anchor, requested incarnation, and rendering medium must remain intact. A rewrite that converts animation into live action, drops a named version, or substitutes a generic subject should be corrected before the next generation.

For reference-backed or hybrid identity work, label every image by index and role. GPT Image 2 processes image inputs at high fidelity automatically; do not invent or emit an `input_fidelity` control for this model. World knowledge and prompt rewriting can improve creation, but neither proves canonical accuracy.

When an input declares `must_attach: true`, the compiler emits it in the top-level `attachments` manifest and marks the prompt input line as requiring the actual image. Executors must forward the real files/images to the generation or edit call; descriptions are not replacements. The top-level `imagegen_call_plan` records the expected Codex mechanism, input IDs, count, and dated capability limit; execution is reference-verified only after a matching receipt. This Skill does not route to post-generation compositing.

Quality controls should be short and positive: material-specific surface response, controlled highlights, natural microcontrast, selective focal detail, and only source- or scene-motivated grain, bloom, flare, gloss, and particles. Official OpenAI prompting examples favor real texture, natural color balance, and limited retouching, and recommend iterative refinement over overloaded prompts.

For `narrative_film_frame`, preserve the shot contract before aesthetic polish: visible event, relationship pressure, viewer task and position, one frozen moment, staging, camera motivation, distance, focal-length rationale, and motivated lighting. For spectacle or Chinese-fantasy work, compile the chosen treatment and scale separately from causal effects so visual richness does not become a poster-like list of simultaneous assets.

For `styleboard`, compile the global visual master, reference assignments, continuity locks, frame cards, and explicit generation strategy as a prompt package. `sheet_direct` requests one equal-cell board and must carry grid geometry, reading order, panel count, and continuity locks; `independent_frames` compiles native-ratio frame prompts for assembly; `hybrid` compiles the direct board first and targeted replacement frames second. Do not represent any strategy as universally superior.

For `creative_routing`, compile the primary scenario and aesthetic before detailed scene/style fields so the downstream controls share one purpose. A secondary influence must carry a division-of-labor `mix_rule`; do not flatten it into an equal-weight style list.

For `learn_style`, the analysis record may be compiled for inspection, but the reusable output is a validated `style_capsule`. When `--style-capsule` is supplied, compile its transferable surface, palette, shape/line, material, lighting, hierarchy, optics/rendering, and optional motifs before the target scene. Explicitly state that the target specification remains authoritative. Always include capsule `forbidden_transfer` boundaries; do not allow a capsule to reintroduce source identity, exact text, logo, protected design, or layout coordinates.

Compile `spatial_dynamics` before camera detail so dominant read, tension, action/counterforce, layer roles, exaggeration, and distortion explain why the camera is designed that way. Compile the target `color_pipeline` and `render_pipeline` after scene lighting/material/color so they refine the visible result without replacing the subject or world. Engine references labeled `appearance_reference` must remain visual vocabulary; do not present them as tools that actually ran.

When FLUX `prompt_format` is `json`, the compiler result remains a JSON envelope whose `prompt` field contains a second serialized JSON document. Consumers must parse the outer result and then parse `prompt` when they need the structured FLUX object.

Example shape:

```text
Goal:
Create a premium landscape key visual.

Scene:
...

Subjects:
...

Edit:
Change only the moon inside the specified upper-left region.

Preserve:
Camera angle, skyline geometry, exposure, atmosphere, and all surrounding pixels.

Constraints:
No added text, logos, or watermarks.
```

Literal visible text should be quoted and include typography, size, color, and placement. For multi-image inputs, label each image by index and role.

Official sources:

- https://developers.openai.com/api/docs/guides/image-generation
- https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide
- https://developers.openai.com/api/docs/models/gpt-image-2

## FLUX

FLUX works well with clear natural-language descriptions. For FLUX.2, official guidance also supports structured JSON prompts for production workflows, automation, complex scenes, and multi-subject relationships.

Do not produce a negative prompt for FLUX.2. Official guidance says it does not support negative prompts. Rewrite avoidant phrasing into the desired visible state where possible:

| Avoidant phrase | Positive target |
| --- | --- |
| `no blur` | `sharp focus throughout` |
| `no people` | `an empty environment` |
| `no plastic CGI` / `plastic CGI sheen` | `physically plausible materials with natural surface variation` |
| `no extra text` / `new text` | `only the specified literal text appears` |
| `logo` / `logos` | `unbranded scene containing only the requested visual content` |
| `watermark` / `watermarks` | `clean image containing only the requested visual content` |
| `global gloss` | `material-specific matte and reflective response with no uniform sheen` |

The compiler strips `no`/`without`, folds supported plurals, and maps only known concepts. If an exclusion cannot be expressed safely as a positive visual target, it is omitted from the FLUX prompt and returned as a warning for human review instead of pretending it is enforced.

For multiple references, state the role of each image: subject from image 1, style from image 2, environment from image 3. Use exact quoted text and explicit placement. Keep optional `prompt_upsampling` in parameters rather than prompt prose.

Official sources:

- https://docs.bfl.ai/guides/prompting_summary
- https://docs.bfl.ai/guides/prompting_guide_flux2
- https://docs.bfl.ai/guides/prompting_unified_basics

## Midjourney

Write the visible content first. Place all parameters at the end, separated from the text by spaces and without punctuation inside the parameter sequence.

Common mappings:

- canvas aspect ratio → `--ar`;
- exclusions → `--no`;
- style reference URL or style-code string → `--sref`; an optional positive per-reference `weight` compiles as `URL::weight`, while global `style_weight` compiles separately as `--sw`;
- style reference influence → `--sw`;
- raw mode → `--raw`;
- stylization, chaos, quality, seed, and version → their documented parameters.

Do not map internal `control.weight` directly to multi-prompt weights. Only emit Midjourney weights when the specification explicitly supplies a provider-native weight.

Ordinary prose is neutralized before Midjourney flags are appended: user text containing `--` or `::` must not become an injected parameter or multi-prompt weight. Provider-native style-reference weights remain separate flag values.

Style References transfer overall visual characteristics such as color, medium, texture, and lighting; they are not identity or object-copy controls. Keep text prompts focused on desired content when a Style Reference is present.

The compiler also emits an execution route rather than pretending every task is plain `/imagine`: ordinary image prompts influence content/composition, Style Reference handles appearance, Omni Reference handles one V7 person/object/vehicle reference, and edit/restyle/expand require the Midjourney Editor. These routes are execution guidance, not web automation, and must be rechecked against current Midjourney documentation.

Coordinate-only local editing is approximate in a prompt. Compile an anchor such as `(16.5%, 16.4%)` into a semantic placement description and warn that surgical edits require an editor region, mask, or platform UI capability.

Official sources:

- https://docs.midjourney.com/docs/prompts
- https://docs.midjourney.com/hc/en-us/articles/32859204029709-Parameter-List
- https://docs.midjourney.com/hc/en-us/articles/32180011136653-Style-Reference
- https://docs.midjourney.com/hc/en-us/articles/36285124473997-Omni-Reference
- https://docs.midjourney.com/hc/en-us/articles/32764383466893-Editor

## Generic Output

When the platform is unknown, produce:

```json
{
  "prompt": "positive visual description",
  "negative_prompt": "portable exclusions",
  "parameters": {},
  "warnings": ["Provider-specific syntax and parameter support are unverified."]
}
```

Do not invent sampler names, CFG values, steps, seed behavior, reference limits, or size limits for an unspecified provider.

## Compiler Script

Compile a validated spec:

```bash
python3 scripts/compile_prompt.py examples/atomic-cyber-live-action.json --platform openai
python3 scripts/compile_prompt.py examples/atomic-cyber-live-action.json --platform flux --format text
python3 scripts/compile_prompt.py examples/atomic-cyber-live-action.json --platform midjourney
python3 scripts/compile_prompt.py examples/causal-fantasy-effect.json --platform openai --approve-review
python3 scripts/compile_prompt.py examples/tactile-stop-motion-product.json \
  --style-capsule examples/style-capsule-graphite-copper.json \
  --platform openai
```

The JSON output contains `platform`, `prompt`, `prompt_metrics`, `prompt_review`, `negative_prompt`, `parameters`, `warnings`, `attachments`, `reference_handoff`, `imagegen_call_plan`, and `source_spec_version`. Context-residue review scans structured source fields before provider serialization and excludes only `text_elements.content`; this avoids provider escaping errors and does not create a second copy source. Midjourney output additionally carries `execution_route`.
