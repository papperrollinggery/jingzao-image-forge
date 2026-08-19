# Reference Style Learning and Style Capsules

Use `mode: learn_style` when the user wants an actual supplied image analyzed and converted into a reusable visual style. This workflow extracts a maintainable rule system; it does not train model weights or prove the source's hidden production process.

## Evidence Layers

Keep three layers separate:

1. **Observed:** directly visible medium behavior, palette ownership, shape/line, texture/material, lighting, composition, typography, optics/rendering, and motifs.
2. **Inferred:** plausible production or design intent that cannot be proven from the final pixels.
3. **Unknown:** tools, model, lens, stock, software, artist intent, and hidden prompt details that are not visible.

Never present inference as observation.

## Learn-Style Workflow

1. Inspect every source image with an actual vision-capable tool.
2. Assign `source_input_ids`; state whether the sources agree or represent different layers.
3. Fill `style_learning.observed` with reusable mechanisms, not subject inventory.
4. Write `transfer_rules` and `forbidden_transfer` before exporting.
5. Validate the learn-style specification.
6. Export a source-image-free capsule that records source count and provenance but embeds no raw image; review advisory warnings for quoted copy, brand/signature terms, or coordinates.
7. Apply the capsule to at least two materially different subjects or scene types.
8. Visually review whether the style transferred while identity, text, layout coordinates, brands, and source-specific objects did not.
9. Mark the capsule `validated` only after those tests; mark it `adopted` only when the user approves durable inclusion in the Skill.

## Required Observations

```json
{
  "style_learning": {
    "profile_id": "graphite-copper-editorial",
    "profile_name": "Graphite Copper Editorial",
    "scope": "skill_candidate",
    "status": "draft",
    "source_input_ids": ["style-reference"],
    "observed": {
      "medium_behavior": "premium editorial infographic with dimensional product-visualization elements",
      "palette_logic": ["graphite owns the field", "copper owns active lines and hierarchy"],
      "shape_line_language": "thin precise rules, rectilinear panels, one circular lens motif",
      "texture_material_logic": ["matte black surfaces", "selective brushed copper", "restrained glass"],
      "lighting_logic": "one motivated warm path with localized highlights and deep clean shadows",
      "composition_logic": ["large title", "single reading path", "stacked readable sections"],
      "typography_logic": ["high-contrast title", "clear sans labels", "monospace technical strings"],
      "optics_rendering_logic": "clean low-noise rendering with restrained glow and phone-readable focus",
      "motifs": ["circular precision geometry", "network lattice", "small sequence grid"]
    },
    "inferred_traits": ["craft precision presented as premium technology"],
    "unknowns": ["original typeface", "source software"],
    "transfer_rules": ["transfer palette ownership and hierarchy, not source content"],
    "forbidden_transfer": ["source title", "brand marks", "exact layout coordinates", "depicted character"],
    "validation_prompts": [],
    "verification_notes": ""
  }
}
```

## Export and Validate

```bash
python3 scripts/validate_spec.py examples/style-learning-graphite-copper.json
python3 scripts/create_style_capsule.py examples/style-learning-graphite-copper.json \
  --output /tmp/style-capsule-graphite-copper.json
python3 scripts/validate_style_capsule.py /tmp/style-capsule-graphite-copper.json
```

Apply a capsule to a normal visual specification:

```bash
python3 scripts/compile_prompt.py examples/tactile-stop-motion-product.json \
  --style-capsule /tmp/style-capsule-graphite-copper.json \
  --platform openai
```

## Privacy and Copyright Boundary

- Do not embed or copy the raw reference image into a capsule.
- Do not persist private images, faces, logos, signatures, source text, exact compositions, or protected character design as style rules.
- Transfer mechanisms: medium behavior, palette ownership, line/shape, texture/material, lighting, hierarchy, optics/rendering, and limited motifs.
- The target specification remains authoritative. Capsule medium, composition, typography, and motifs are scoped influences, not permission to replace target subject, scene, layout, text, or production method.
- A one-off source becomes a draft candidate, not an automatically adopted global rule.
- User approval to analyze or use a reference is not automatically approval to publish that reference or make the capsule public.

## Validation Gate

- At least two cross-subject transfer tests for `validated` or `adopted` status.
- The tests differ in subject and preferably in scenario profile.
- The source subject and exact layout do not reappear unless independently requested.
- Style remains recognizable through mechanisms rather than copied content.
- Visual review notes state both what transferred and what did not.
