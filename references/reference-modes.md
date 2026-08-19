# Reconstruct, Restyle, and Expand

Use this reference for the three source-image modes whose success depends on stronger invariants than ordinary creation. Every mode requires an actual attached image and a verified execution receipt.

## Reconstruct

Purpose: rebuild observable visual relationships without pretending to recover a hidden prompt, lens, software, node graph, or production intent.

Required contract:

- `reference_analysis.target`: what must be reconstructed;
- `observed`: facts directly visible in pixels;
- `inferred`: plausible but explicitly unverified interpretation;
- `unknowns`: details that cannot be recovered;
- one or more actual reference images with roles and `must_attach: true`.

See `examples/reconstruct-architecture-reference.json`.

## Restyle

Purpose: change only the image-making treatment while source geometry and protected content remain authoritative.

Required contract:

- `must_preserve`: identity, pose, camera, crop, geometry, layout, existing text, and any other source invariant;
- `must_change`: one named treatment change;
- `render.artifact_budget: source_matched` when source grain, sharpness, bloom, or wear must survive;
- actual base image; additional style images, when supplied, have style-only roles.

If the prompt changes content, layout, identity, or camera beyond `must_change`, it has drifted into generation rather than restyling. See `examples/restyle-risograph-editorial.json`.

## Expand

Purpose: extend source boundaries for a new canvas without redesigning the original composition.

Required contract:

- target `canvas` and named expansion edges;
- `must_preserve`: original content, subject relative x/y, frame-height ratio, perspective/vanishing points, exposure, light direction, material response, and source-boundary continuity;
- `must_change`: only new edge regions and crop-safe context;
- actual base image.

Do not promise pixel identity. Visually compare subject position/scale, main vanishing points, original edge continuity, and whether the result was silently re-centered. See `examples/expand-roadside-outpaint.json`.

Current evidence boundary (2026-08-19): one built-in ImageGen forward test produced visually continuous extensions, but after two single-variable corrections no attempt simultaneously preserved the requested 2.39:1 canvas, the strongly left-weighted subject anchor, and source frame-height ratio. Therefore the specification, preflight, and execution route are supported, but strict anchored outpaint is not yet a production-quality claim. Mark drift as FAILED instead of accepting continuity alone.

## Provider Routing

- Built-in Codex ImageGen: use its image edit path with the actual base image and a verified call plan/receipt.
- Midjourney: reconstruct may use Image Prompt or Omni Reference depending on content; restyle/expand require the Editor/Retexture/Pan/Zoom-Out route rather than pretending an ordinary imagine prompt is an edit.
- Other providers: return explicit warnings when the required edit/reference mechanism is unverified.

Never add a post-generation compositing fallback.
