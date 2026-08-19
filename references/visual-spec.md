# Visual Generation Specification

Use this reference for multi-subject images, reference-based reconstruction, exact layouts, local edits, restyling, expansion, or any workflow that must survive multiple prompt iterations.

## Core Model

The specification is a platform-neutral source of truth. It separates scene intent from platform syntax and separates hard invariants from creative freedom.

Required top-level fields:

| Field | Purpose |
| --- | --- |
| `visual_generation_spec` | Schema version. Use `"1.0"`. |
| `mode` | `create`, `reconstruct`, `edit`, `restyle`, `expand`, or `styleboard`. |
| `intent` | What the finished image is for and what success means. |
| `platform` | `auto`, `openai`, `flux`, `midjourney`, or `generic`. |
| `canvas` | Aspect ratio and optional dimensions. |
| `constraints` | Explicit preservation, change, and exclusion lists. |

Optional sections add precision only when relevant:

- `inputs`: base image, subject reference, style reference, layout reference, palette reference, or mask.
- `language`: content-language metadata (`en`, `zh`, or `zh-CN`) preserved in compiler output; it does not translate supplied content automatically.
- `knowledge_anchors`: exact named entities that a capable generation model may recognize from existing world knowledge or supplied references.
- `direction`: deliverable, treatment, spectacle scale, camera freedom, genre, world rule, and visual goal.
- `cinematic`: narrative-frame contract, shot function, viewer position, frozen moment, and posterization guard.
- `scene`: environment, time, atmosphere, and overall summary.
- `subjects`: count, appearance, action, pose, gaze, position, scale, and relationships.
- `staging`: primary relationship, subject placement, eyelines, screen direction, axis, occlusion, and attention path.
- `composition`: shot size, angle, perspective, framing, negative space, and depth layers.
- `lighting`: key, fill, rim, direction, contrast, temperature, and practical sources.
- `materials`: target-specific surface and physical properties.
- `color`: palette and grade.
- `optics`: focus, depth of field, lens character, motion blur, and optical artifacts.
- `style`: medium, realism level, visual traits, era, and non-conflicting references.
- `text_elements`: literal visible text and typography constraints.
- `spatial_edits`: local edit targets, anchors, regions, and preservation behavior.
- `effects`: optional causal VFX cards for supernatural, giant-scale, destruction, transformation, energy, or environmental effects.
- `styleboard`: reference assignments, continuity locks, presentation finish, frame cards, and board assembly.
- `render`: quality intent, detail priorities, artifact budget, and optional quality controls.
- `platform_options`: syntax and generation controls for a named platform.

## Control Semantics

Any major object may contain:

```json
{
  "control": {
    "weight": 0.95,
    "lock": true,
    "variance": 0.0
  }
}
```

- `weight`: relative importance from `0.0` to `1.0`.
- `lock`: whether the attribute is an invariant.
- `variance`: allowed creative freedom from `0.0` to `1.0`.

If `lock` is `true`, set `variance` to `0.0`. These values guide compilation and review. They are not automatically equivalent to Midjourney weights, CFG, denoise strength, masks, or any provider-specific parameter.

## Canvas Profiles

`canvas.profile` is optional:

- `auto`: choose from task intent while still recording the final ratio.
- `standard_widescreen`: 16:9-class delivery.
- `cinematic_ultrawide`: 21:9, 2.35:1, or 2.39:1-class delivery when width carries narrative or spectacle information.
- `vertical_story`: 9:16-class frame.
- `square`: 1:1-class frame.
- `custom`: any validated positive ratio.

The profile does not override an explicit user ratio or the source image in an edit, restyle, or expansion.

## Knowledge Anchors

Use `knowledge_anchors` only when an exact named entity contributes meaningful prior knowledge:

```json
{
  "knowledge_anchors": [
    {
      "name": "Bethel, New York on August 16, 1969",
      "context": "period-accurate Woodstock-era outdoor crowd scene",
      "strategy": "auto",
      "reference_ids": [],
      "verification": "unverified",
      "control": {"weight": 1.0, "lock": true, "variance": 0.0}
    }
  ]
}
```

- `name`: preserve the user's exact proper noun and version wording verbatim.
- `context`: only the incarnation, date, medium, or canon distinction needed to disambiguate the entity.
- `strategy`: `auto`, `model_knowledge`, `reference`, or `hybrid`. `auto` is the default; `reference` and `hybrid` require valid `reference_ids` from `inputs`.
- `verification`: `unverified`, `reference_checked`, or `user_confirmed`. Model recognition alone remains `unverified`.
- Keep cinematic composition separate from `style.medium`; “cinematic” does not imply live action.
- Do not replace the anchor with a long facial, costume, architectural, or object-feature inventory on the first pass. Add descriptors only to resolve ambiguity or correct an observed miss.

## Visual Direction

```json
{
  "direction": {
    "deliverable": "narrative_film_frame",
    "treatment": "heightened_cinematic",
    "spectacle_scale": "monumental",
    "camera_freedom": "heightened",
    "genre": "Chinese fantasy",
    "world_rule": "cultivation effects must have a visible owner, operation, resistance, result, and residue",
    "visual_goal": "place the viewer inside a pressured relationship rather than presenting every asset as key art"
  }
}
```

These fields are independent. A narrative frame may be grounded or highly stylized; a poster may be realistic or graphic; giant scale may be dramatic or mythic.

## Cinematic Narrative Contract

Use only for a cinematic task:

```json
{
  "cinematic": {
    "profile": "narrative_film_frame",
    "shot_function": "observe",
    "visible_event": "one character notices that the other has already decided to leave",
    "relationship_pressure": "neither character meets the other's gaze",
    "viewer_task": "read the decision through distance and an unfinished object action",
    "viewer_position": "seated at the far end of the same table",
    "frozen_moment": "the hand releases the shared object before the other character reaches it",
    "withheld_information": "the destination remains offscreen",
    "posterization_guard": true
  },
  "staging": {
    "primary_relationship": "A withdraws from B across the table",
    "subject_positions": ["A screen-left foreground", "B screen-right midground"],
    "eyeline_logic": "A looks toward the exit; B watches A's hand",
    "screen_direction": "attention moves left to right toward the unseen exit",
    "axis": "table and eyeline axis remains readable",
    "occlusion": "foreground chair edge partially blocks B",
    "attention_path": "released object -> A's hand -> B's gaze -> empty doorway"
  }
}
```

For `narrative_film_frame`, the specification must also provide camera motivation, camera height, camera distance, lens rationale, and motivated lighting fields.

## Causal Effects

Use one dominant effect family and only the visible phase needed by the still:

```json
{
  "effects": [
    {
      "function": "show that the formation suppresses movement",
      "owner_source": "the cultivator's grounded hand seal",
      "trigger_formation": "ink-dark lines lock into a restrained circular lattice",
      "material_shape": "compressed calligraphic geometry with mineral dust",
      "path_layer": "midground lattice wraps the target without covering the contact point",
      "operation_contact": "binds the target's forward motion",
      "receiver_environment_response": "cloth, dust, and nearby water pull toward the lattice",
      "intensity": "hero",
      "decay_residue": "lines dim into a few stable seal marks and settled dust"
    }
  ]
}
```

An effect must have a source, operation, visible consequence, and endpoint. Particles, glow, smoke, trails, floating rocks, and emissive light are not default decoration.

## Styleboard Specification

`mode: styleboard` requires image inputs and a `styleboard` object:

```json
{
  "styleboard": {
    "layout": "3x3",
    "frame_count": 9,
    "frame_aspect_ratio": "16:9",
    "presentation": "hand_drawn",
    "generation_strategy": "auto",
    "reading_order": "left_to_right_top_to_bottom",
    "continuity_locks": ["character identity", "wardrobe", "location geography", "light direction"],
    "allowed_variation": ["shot size", "camera angle", "action phase"],
    "reference_assignments": [
      {
        "input_id": "image-1",
        "role": "style",
        "secondary_roles": [],
        "use": "line weight, paper texture, gray-value finish",
        "ignore": "identity, costume, scene, pose"
      }
    ],
    "frames": [
      {
        "id": "frame-01",
        "shot_function": "establish",
        "story_moment": "the characters enter the same space but have not yet acknowledged each other",
        "primary_action": "one character stops at the threshold",
        "action_phase": "hold",
        "shot_size": "wide",
        "camera_height": "eye level",
        "focal_length_mm": 35,
        "composition": "doorway foreground, two characters separated across the middle ground"
      }
    ]
  }
}
```

Canonical presentation values are `line_art`, `hand_drawn`, `cinematic_frame`, or `mixed`. Generation strategies are `auto`, `sheet_direct`, `independent_frames`, or `hybrid`. For equal-cell direct sheets, `board ratio = frame ratio × columns ÷ rows`; this preserves native cell geometry for both square and non-square grids. Each reference has one primary `role` plus optional explicit, non-duplicated `secondary_roles` when the same image genuinely proves more than one layer.

## Spatial Coordinate DSL

Use normalized percentages with the origin at the top-left:

```json
{
  "point": {"x_percent": 16.5, "y_percent": 16.4},
  "region": {
    "x_percent": 7.0,
    "y_percent": 5.0,
    "width_percent": 19.0,
    "height_percent": 23.0
  }
}
```

- A point is a semantic anchor.
- A region is an approximate bounding box.
- `x_percent + width_percent` and `y_percent + height_percent` must not exceed `100`.
- Use an actual mask when pixel boundaries matter. Text coordinates alone do not create a deterministic mask.

For a local edit, include:

```json
{
  "target": "moon",
  "instruction": "Transform only the intact lunar disk into a physically fractured moon.",
  "preserve_surroundings": true,
  "control": {"weight": 1.0, "lock": false, "variance": 0.12}
}
```

## Mode-Specific Minimums

### Create

Define `intent`, `canvas`, scene or subject content, and meaningful constraints. Avoid filling every section when it adds no control.

### Reconstruct

Provide at least one image input. Split findings into directly observable attributes, plausible but unverified production inferences, and unknown details that should not be invented. The deliverable is a functional reconstruction prompt, not a claim to recover the original hidden prompt.

### Edit

Provide a base image input and at least one `spatial_edits` item or `must_change` constraint. Always provide `must_preserve`. Lock identity, geometry, camera, layout, text, or surroundings when they must not drift.

### Restyle

Provide a base image and a style target. Put geometry, subject identity, pose, layout, and literal text in `must_preserve`; put visual treatment in `must_change`.

### Expand

Provide the base image, new canvas, extension direction, and continuity rules. Preserve the original image content and subject placement unless the user explicitly requests reframing. Describe how background, lighting, texture, perspective, and depth continue into new space.

### Styleboard

Provide at least one image input, explicit reference roles, a presentation finish, frame count, frame ratio, continuity locks, allowed variation, and one frame card per frame. Each frame has one shot function, one story moment, one primary action, and one action phase.

## Exact Text

Each visible string belongs in `text_elements`:

```json
{
  "content": "OPEN",
  "case_sensitive": true,
  "placement": "above the doorway",
  "typography": "large condensed sans serif",
  "color": "#FF3B30",
  "control": {"weight": 1.0, "lock": true, "variance": 0.0}
}
```

Keep spelling and casing verbatim. Do not translate user-visible copy unless requested.

## Render Quality Controls

Use a compact `artifact_budget` instead of repeating a long cleanup list:

```json
{
  "render": {
    "quality": "high",
    "detail_priority": ["primary subject", "hero material"],
    "artifact_budget": "balanced",
    "quality_controls": [
      "skin remains matte with soft, localized specular highlights",
      "background gradients remain clean and low-noise"
    ]
  }
}
```

- `strict`: clean product, typography, diagrams, minimal editorials, and other artifact-intolerant work.
- `balanced`: default premium imagery; allows only restrained, scene-motivated grain, bloom, flare, gloss, and particles.
- `expressive`: intentional painterly, analog, fantasy, or effects-heavy work while preserving material separation and focal hierarchy.
- `source_matched`: edits, restyles, and expansions that must inherit the source image's grain, sharpness, bloom, flare, and surface response without adding new artifact classes.
- `quality_controls`: optional shot-specific positive targets. Keep them concise and physically observable.

Do not treat intentional film grain, brush texture, wet gloss, atmospheric particles, or lens artifacts as defects when the user or source explicitly requires them.

Each `materials` item uses the canonical fields `target`, `description`, and `physical_properties`. The validator rejects the ambiguous legacy key `properties` so material intent cannot be silently dropped during compilation.

## Scene Relationships

Describe relations explicitly rather than relying on a keyword list:

- who is in front of or behind whom;
- which hand holds an object;
- gaze target;
- contact and occlusion;
- relative scale;
- foreground, midground, and background placement.

If the relation is essential, repeat it in `constraints.must_preserve`.

## Review Checklist

- All user-provided facts are preserved.
- Subject count and identities are explicit.
- Actions are physically coherent.
- Spatial anchors are inside the canvas.
- Exact text is quoted and locked.
- Every edit says what changes and what remains invariant.
- Reference-image roles are distinct.
- Exact knowledge anchors appear early, remain verbatim, and retain their requested incarnation and medium.
- Canonical accuracy is not marked verified from model knowledge alone.
- Visual direction distinguishes deliverable, treatment, spectacle scale, genre logic, and camera freedom.
- Narrative frames bind relationship, staging, lens, camera distance, and motivated light instead of defaulting to poster composition.
- Causal effects have an owner, path, operation, response, and residue.
- Styleboard references have one primary role; frame cards and continuity locks are explicit.
- Artifact controls preserve intentional medium traits while suppressing unmotivated noise, light spots, uniform gloss, and equal-detail rendering.
- Internal controls are not misrepresented as provider-native controls.
- Unobserved reconstruction details are labeled as inference or unknown.
