# Direct Multi-Image Reference Delivery

Use this reference when the user supplies character, costume, product, logo, prop, environment, camera, composition, palette, or style images that must influence generation or editing.

## Non-Negotiable Rule

The image-generation tool must receive the actual images. Do not convert supplied images into text descriptions and then call the model without attachments.

## Minimal Input Record

```json
{
  "id": "product-reference",
  "type": "image",
  "role": "product and packaging reference",
  "description": "Use the actual product, proportions, materials, label, and visible logo while creating a new campaign scene.",
  "source_kind": "local_path",
  "source_ref": "/actual/path/product.png",
  "must_attach": true
}
```

`source_kind` values are `local_path`, `conversation_image`, `remote_url`, `platform_asset`, or `unspecified`. A `must_attach` input cannot remain `unspecified`.

`reconstruct`, `edit`, `restyle`, `expand`, and `learn_style` require at least one image input with `must_attach: true`; validation fails before compilation when the base/reference image is missing. Packaged examples may use an explicit runtime `platform_asset` placeholder, but that placeholder must be replaced with the actual asset before execution.

## Built-In ImageGen Handoff

- Local file: inspect it with `view_image`, then pass its real path in `referenced_image_paths`.
- Conversation-only images: use the smallest `num_last_images_to_include` that includes every required image.
- Never provide both attachment mechanisms in one call.
- Use the tool call arguments or receipt as evidence that images were included.
- If one required image is unavailable, stop; do not continue with a textual reconstruction unless the user explicitly authorizes a text-only fallback.

## Multiple Reference Roles

Keep roles simple and non-overlapping:

- Image 1: character identity and body proportions.
- Image 2: wardrobe and the mark on the left sleeve.
- Image 3: product/packaging and visible logo.
- Image 4: scene geography.
- Image 5: camera/action or style only.

Describe the desired interaction in the prompt. The actual image remains attached throughout generation/editing.

## Generation and Edit Routing

- New scene using supplied assets: multi-reference generation with all required images attached.
- Existing product/photo must remain while surroundings change: use the model's edit path with the base image attached.
- Character continuity across frames: attach approved character/wardrobe assets on every generation where continuity matters.
- Logo or clothing mark: attach the actual logo/mark image and the product/wardrobe image; require visual verification of shape, placement, spelling, and color after generation.

Generative reference transfer is not a pixel-identity guarantee. Failure means retry or route through the model's edit workflow—not post-generation compositing.

## Preflight

```bash
python3 scripts/reference_delivery.py path/to/spec.json
```

The preflight resolves required local paths and reports conversation/remote/platform assets as runtime-required. The compiler also emits an `attachments` manifest and `reference_handoff` block; an executor must honor them.

## Gate

- Every required image appears in the actual generation/edit call.
- Roles are stated without inventing extra policy systems.
- No reference silently controls unrelated content.
- Logo, product, identity, wardrobe, marks, and scene assets are visually checked after output.
- No post-generation compositing is introduced by this Skill.
