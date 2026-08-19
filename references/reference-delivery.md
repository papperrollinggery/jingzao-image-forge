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

- Run `python3 scripts/reference_delivery.py path/to/spec.json --target codex_imagegen` before execution. The target-specific plan is compiler output, not a new visual-spec field.
- Prompt review and attachment delivery are two independent gates. The compiler owns `prompt_review`. For local references its call plan can also become execution-ready. Conversation-image selection is intentionally unresolved at compile time; immediately before execution, run this standalone preflight with `--confirm-conversation-window` and use its returned call plan as the authoritative attachment gate. Neither gate approves the other.
- The bundled Codex ImageGen contract verified on 2026-08-19 accepts at most five reference/edit images and exactly one attachment mechanism per call. This is a named, dated target capability—not a portable provider rule.
- Local file: inspect it with `view_image`, then pass its real path in `referenced_image_paths`.
- Conversation-only images: confirm immediately before execution that the required images are the newest contiguous conversation-image window, then pass `--confirm-conversation-window` to preflight and use the smallest `num_last_images_to_include` that includes every required image. This is best-effort because conversation images do not yet have stable path-like references.
- Never provide both attachment mechanisms in one call.
- `remote_url` and `platform_asset` are not executable by built-in ImageGen until materialized as local files; unresolved values block target preflight.
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

Reference admission follows the brief, not the maximum attachment count. A user-required identity, product, logo, or continuity asset stays required, but an unrelated reference must not be added just to demonstrate capacity. If required roles do not support one coherent delivery, split the work or report the conflict instead of inventing a synthetic integration scene. Pipeline stress tests verify call-plan/receipt mechanics separately from creative forward tests.

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

For the Codex target it additionally emits:

```json
{
  "imagegen_call_plan": {
    "status": "ready",
    "mechanism": "referenced_image_paths",
    "required_input_ids": ["identity", "wardrobe", "product"],
    "expected_attachment_count": 3
  }
}
```

After the tool call, verify a runtime receipt against the same plan:

```json
{
  "mechanism": "referenced_image_paths",
  "sent_input_ids": ["identity", "wardrobe", "product"],
  "sent_count": 3,
  "tool_call_id": "actual-tool-call-id",
  "output_ref": "actual-output-reference"
}
```

Use `--receipt path/to/receipt.json` with the Codex target. A mismatch means generation may have completed, but reference-backed execution is not verified.

For public forward evidence, replace the raw `tool_call_id` with `tool_call_id_sha256`, use only logical input IDs and a repository-relative `output_ref`, and allowlist the remaining fields. Resolve every manifest/receipt path inside the repository root; reject absolute paths, parent traversal, URL schemes, Windows drives, symlink escape, nested receipt objects, and sensitive runtime strings. Do not publish local paths, source filenames, signed URLs, tokens, session/thread IDs, cursors, or raw conversation-image handles. Any manifest case whose compiled spec has `must_attach: true` requires a receipt; hash-only prompt/output evidence is insufficient to prove actual reference delivery.

## Gate

- Every required image appears in the actual generation/edit call.
- Roles are stated without inventing extra policy systems.
- No reference silently controls unrelated content.
- Logo, product, identity, wardrobe, marks, and scene assets are visually checked after output.
- No post-generation compositing is introduced by this Skill.
