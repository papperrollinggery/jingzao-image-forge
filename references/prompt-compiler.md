# Platform Prompt Compiler

This reference converts one visual specification into a provider-ready prompt. Keep the visual specification as the source of truth; provider prompts are disposable compiled outputs.

Platform behavior changes over time. The provider notes below were checked against official documentation on 2026-08-19. Recheck official documentation before executing an API call or promising parameter support.

## Shared Compilation Order

Use a stable order so prompts remain debuggable:

1. exact named-entity knowledge anchors and requested incarnation;
2. intent, deliverable type, treatment, spectacle scale, genre logic, and camera freedom;
3. cinematic shot contract, viewer position, frozen moment, and staging when relevant;
4. scene and environment;
5. subjects, actions, relationships, and causal effects;
6. composition, camera motivation, focal-length rationale, and spatial placement;
7. motivated lighting, materials, color, and optics;
8. style and realism;
9. compact artifact budget and shot-specific quality controls;
10. exact visible text;
11. requested edits or styleboard frame cards;
12. preservation and continuity constraints;
13. exclusions or provider-native negative controls;
14. generation parameters, kept outside prose when the provider supports them.

Compile locked, high-weight fields first and repeat critical invariants in the edit section. Do not translate `control.weight`, `lock`, or `variance` into provider parameters unless a documented mapping truly exists.

## OpenAI GPT Image

Use short labeled sections for complex prompts. State explicit framing, placement, pose, text, and material details. For edits, say `Change only ...` and `Keep everything else the same`, then restate the preserve list on every iteration.

OpenAI's current official guidance recommends `gpt-image-2` for new image generation and editing workflows. It supports generation and edits through the Image API, and conversational multi-turn image work through the Responses API. Keep `model`, `quality`, and `size` separate from prompt prose. Accepted quality values are `low`, `medium`, `high`, and `auto`.

GPT image generation models can combine reasoning with world knowledge. For a named character, place, historical event, artifact, or fictional-world element, preserve the exact entity and version wording before the rest of the prompt. Start with a clean base prompt and refine through small single-change follow-ups; do not bury a useful entity anchor under speculative generic descriptors.

When the built-in Responses image-generation tool returns `revised_prompt`, inspect it before accepting the result. The exact knowledge anchor, requested incarnation, and rendering medium must remain intact. A rewrite that converts animation into live action, drops a named version, or substitutes a generic subject should be corrected before the next generation.

For reference-backed or hybrid identity work, label every image by index and role. GPT Image 2 processes image inputs at high fidelity automatically; do not invent or emit an `input_fidelity` control for this model. World knowledge and prompt rewriting can improve creation, but neither proves canonical accuracy.

Quality controls should be short and positive: material-specific surface response, controlled highlights, natural microcontrast, selective focal detail, and only source- or scene-motivated grain, bloom, flare, gloss, and particles. Official OpenAI prompting examples favor real texture, natural color balance, and limited retouching, and recommend iterative refinement over overloaded prompts.

For `narrative_film_frame`, preserve the shot contract before aesthetic polish: visible event, relationship pressure, viewer task and position, one frozen moment, staging, camera motivation, distance, focal-length rationale, and motivated lighting. For spectacle or Chinese-fantasy work, compile the chosen treatment and scale separately from causal effects so visual richness does not become a poster-like list of simultaneous assets.

For `styleboard`, compile the global visual master, reference assignments, continuity locks, frame cards, and explicit generation strategy as a prompt package. `sheet_direct` requests one equal-cell board and must carry grid geometry, reading order, panel count, and continuity locks; `independent_frames` compiles native-ratio frame prompts for assembly; `hybrid` compiles the direct board first and targeted replacement frames second. Do not represent any strategy as universally superior.

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
| `no plastic CGI` | `physically plausible materials with natural surface variation` |
| `no extra text` | `only the specified literal text appears` |

If an exclusion cannot be expressed safely as a positive visual target, return it as a warning for human review instead of pretending it is enforced.

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
- style reference URL → `--sref`;
- style reference influence → `--sw`;
- image prompt influence → `--iw` when explicitly supplied;
- raw mode → `--raw`;
- stylization, chaos, quality, seed, and version → their documented parameters.

Do not map internal `control.weight` directly to multi-prompt weights. Only emit Midjourney weights when the specification explicitly supplies a provider-native weight.

Style References transfer overall visual characteristics such as color, medium, texture, and lighting; they are not identity or object-copy controls. Keep text prompts focused on desired content when a Style Reference is present.

Coordinate-only local editing is approximate in a prompt. Compile an anchor such as `(16.5%, 16.4%)` into a semantic placement description and warn that surgical edits require an editor region, mask, or platform UI capability.

Official sources:

- https://docs.midjourney.com/docs/prompts
- https://docs.midjourney.com/hc/en-us/articles/32859204029709-Parameter-List
- https://docs.midjourney.com/hc/en-us/articles/32180011136653-Style-Reference

## Generic Output

When the platform is unknown, produce:

```json
{
  "prompt": "positive visual description",
  "negative_prompt": "portable exclusions",
  "parameters": {},
  "warnings": ["Provider-specific behavior is unverified."]
}
```

Do not invent sampler names, CFG values, steps, seed behavior, reference limits, or size limits for an unspecified provider.

## Compiler Script

Compile a validated spec:

```bash
python3 scripts/compile_prompt.py examples/atomic-cyber-live-action.json --platform openai
python3 scripts/compile_prompt.py examples/atomic-cyber-live-action.json --platform flux --format text
python3 scripts/compile_prompt.py examples/atomic-cyber-live-action.json --platform midjourney
```

The JSON output contains `platform`, `prompt`, `negative_prompt`, `parameters`, `warnings`, and `source_spec_version`.
