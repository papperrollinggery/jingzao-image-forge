# Visual Generation Specification

Use this reference for multi-subject images, reference-based reconstruction, exact layouts, local edits, restyling, expansion, or any workflow that must survive multiple prompt iterations.

## Core Model

The specification is a platform-neutral source of truth. It separates scene intent from platform syntax and separates hard invariants from creative freedom.

The distributed template is a neutral fill-in skeleton, not an executable prompt. Until it contains semantic generation content, compilation is blocked with `empty_prompt` even though the template itself remains schema-valid.

Required top-level fields:

| Field | Purpose |
| --- | --- |
| `visual_generation_spec` | Schema version. Use `"1.0"`. |
| `mode` | `create`, `reconstruct`, `edit`, `restyle`, `expand`, `learn_style`, or `styleboard`. |
| `intent` | What the finished image is for and what success means. |
| `platform` | `auto`, `openai`, `flux`, `midjourney`, or `generic`. |
| `canvas` | Aspect ratio and optional dimensions. |
| `constraints` | Explicit preservation, change, and exclusion lists. |

Optional sections add precision only when relevant:

- `inputs`: actual base image, subject, wardrobe, product, logo, prop, scene, camera/action, style, layout, palette, or mask references. Use `source_kind`, `source_ref`, and `must_attach` when the actual image must reach generation/editing; see [reference-delivery.md](reference-delivery.md).
- `language`: content-language metadata (`en`, `zh`, or `zh-CN`) preserved in compiler output; it does not translate supplied content automatically.
- `knowledge_anchors`: exact named entities that a capable generation model may recognize from existing world knowledge or supplied references.
- `creative_routing`: primary scenario, genre family, aesthetic family, capture/render method, scene archetypes, audience effect, delivery context, and anti-drift rules.
- `reference_analysis`: reconstruct-only target plus directly observed facts, clearly marked inference, and explicit unknowns.
- `direction`: deliverable, treatment, spectacle scale, camera freedom, genre, world rule, and visual goal.
- `cinematic`: narrative-frame contract, shot function, viewer position, frozen moment, and posterization guard.
- `scene`: environment, time, atmosphere, and overall summary.
- `subjects`: count, appearance, action, pose, gaze, position, scale, and relationships.
- `staging`: primary relationship, subject placement, eyelines, screen direction, axis, occlusion, and attention path.
- `spatial_dynamics`: dominant read, beauty/tension mechanism, exaggeration, distortion, action/counterforce, layer roles, parallax, and motion evidence.
- `composition`: camera motivation, viewer position, shot size, camera height/distance, focal-length rationale, pitch/yaw/roll, projection/distortion, framing, crop pressure, negative space, and depth layers.
- `lighting`: key, fill, rim, direction, contrast, temperature, and practical sources.
- `color_pipeline`: professional exposure, tone scale, color separation, film/digital finishing, display intent, and shot matching.
- `render_pipeline`: engine-reference scope, light transport, GI/ray tracing, PBR/NPR materials, sampling, and visible pass-separation intent.
- `materials`: target-specific surface and physical properties.
- `color`: palette and grade.
- `optics`: focus, depth of field, lens character, motion blur, and optical artifacts.
- `style`: medium, realism level, visual traits, era, and optional text-only style anchors. Actual image references always belong in `inputs`; file paths or URLs in `style.references` are not attachments.
- `style_learning`: observed style mechanisms, inference/unknown separation, transfer boundaries, and validation prompts for `learn_style`.
- `text_elements`: literal visible text and typography constraints.
- `spatial_edits`: local edit targets, anchors, regions, and preservation behavior.
- `effects`: optional causal VFX cards for supernatural, giant-scale, destruction, transformation, energy, or environmental effects.
- `styleboard`: reference assignments, continuity locks, presentation finish, frame cards, and board assembly.
- `render`: detail priorities, artifact budget, and optional visible quality controls. Provider compute quality belongs only in `platform_options`.
- `platform_options`: syntax and generation controls for a named platform.

## Deprecated Control Annotations

Older 1.0 specifications may contain:

```json
{
  "control": {
    "weight": 0.95,
    "lock": true,
    "variance": 0.0
  }
}
```

The validator still accepts and consistency-checks these fields for backward compatibility, but new templates and examples omit them. The compiler ignores them. Express real priority through the mode, actual reference roles, exact text, semantic sections, and `must_preserve` / `must_change`; never map these legacy values to Midjourney weights, CFG, denoise strength, masks, or provider parameters.

## Canvas Profiles

`canvas.profile` is optional:

- `auto`: keep `aspect_ratio: "auto"` and omit dimensions when a creation brief does not specify or materially imply a ratio. Resolve the ratio only when the delivery, composition, source image, or user request requires it.
- `standard_widescreen`: 16:9-class delivery.
- `cinematic_ultrawide`: 21:9, 2.35:1, or 2.39:1-class delivery when width carries narrative or spectacle information.
- `vertical_story`: 9:16-class frame.
- `square`: 1:1-class frame.
- `custom`: any validated positive ratio.

The profile does not override an explicit user ratio or the source image in an edit, restyle, or expansion.

`canvas` is the visual geometry source of truth once its ratio is explicit. Provider `size` or aspect-ratio overrides are optional; when both sides are supplied, they must agree with canvas dimensions/ratio or validation fails. `auto` emits no size or aspect-ratio instruction.

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

## Creative Routing

Use one primary value per controlled family:

```json
{
  "creative_routing": {
    "scenario_profile": "product_tabletop",
    "genre_family": "commercial_editorial",
    "aesthetic_family": "tactile_handcrafted",
    "capture_or_render_method": "stop_motion",
    "scene_archetypes": ["studio tabletop", "miniature set"],
    "audience_effect": "make the object feel crafted, useful, and giftable",
    "delivery_context": "portrait social campaign and product page",
    "design_priority": "material tactility and label readability",
    "cultural_context": "contemporary craft without invented heritage symbols",
    "secondary_influence": "luxury editorial spacing",
    "mix_rule": "handcrafted materials control the object and set; editorial spacing controls hierarchy only",
    "style_authority": "user_brief",
    "adaptation_rule": "new scenarios may change camera and layout but preserve the tactile tone and color hierarchy",
    "tone_locks": ["matte material hierarchy", "restrained copper accent", "clean low-noise shadows"],
    "forbidden_drift": ["plastic CG", "random rustic props", "unreadable label"]
  }
}
```

- `scenario_profile` states what the image must accomplish. Canonical profiles are documented in [scenario-profiles.md](scenario-profiles.md).
- `genre_family` describes audience and story expectations; it does not define rendering medium.
- `aesthetic_family` is the primary visible rule system. Canonical families and production methods are documented in [visual-style-atlas.md](visual-style-atlas.md).
- `capture_or_render_method` describes how the image appears to have been made; it does not claim the generator used that physical process.
- `scene_archetypes` accepts at most three open-text spatial functions.
- A `secondary_influence` requires a `mix_rule` that assigns it one layer. Do not stack multiple equal-weight styles.
- `style_authority` and `tone_locks` prevent a new scenario from silently erasing an explicit user, source-reference, capsule, or source-matched visual identity.

## Spatial Dynamics and Camera Exaggeration

```json
{
  "spatial_dynamics": {
    "dominant_read": "the grounded fighter redirects the descending force",
    "secondary_read": "the background city bends under the same pressure",
    "beauty_mechanism": "clean silhouette against one calm sky gap, with copper light only at the contact line",
    "tension_source": "diagonal descent opposed by a low grounded counterforce",
    "exaggeration_budget": "strong",
    "distortion_strategy": "perspective",
    "realism_anchor": "feet, water displacement, and architecture preserve physical scale",
    "action_vector": "upper right to lower left",
    "counterforce": "ground reaction travels from both feet through the close-body hand seal",
    "foreground_role": "wet stone edge and cloth prove viewer proximity and parallax",
    "midground_role": "fighter and contact point own the action",
    "background_role": "city and cloud response prove scale and consequence",
    "depth_transition": "foreground diagonal leads to contact, then expands into the affected skyline",
    "parallax_logic": "large near stone movement against slower distant architecture",
    "motion_evidence": ["cloth lag", "water pull", "directional debris origin"],
    "readability_guard": "do not let distortion stretch the face, contact point, or body anatomy"
  }
}
```

Composition may additionally specify `camera_pitch`, `camera_yaw`, `camera_roll`, `lens_projection`, `perspective_distortion`, `edge_behavior`, `crop_pressure`, `camera_state`, and `action_readability`. Parallax has one canonical home in `spatial_dynamics.parallax_logic`. Read [shot-tension-design.md](shot-tension-design.md).

## Professional Color Pipeline

`color_pipeline` separates technical/display intent from visible creative finishing:

```json
{
  "color_pipeline": {
    "intent": "film_emulation",
    "color_science": "scene-referred wide-gamut intent with hue-preserving highlight compression",
    "display_target": "SDR Rec.709",
    "exposure_strategy": "protect window and practical-light texture while keeping hands readable",
    "tonal_curve": "medium-density midtones, deep but open blacks, soft shoulder",
    "black_point": "dense neutral black without crushing fabric folds",
    "white_point": "practical bulb may approach white; skin and wall highlights retain texture",
    "highlight_rolloff": "long natural rolloff around skin, brass, glass, and the practical source",
    "shadow_floor": "cool readable floor with no cyan contamination",
    "midtone_density": "slightly dense faces and wood without muddy microcontrast",
    "white_balance": "cool exterior ambient opposed by one warm practical",
    "color_separation": "skin, wood, brass, and blue ambient remain distinct",
    "skin_tone_policy": "protect natural hue and luminance between warm and cool pools",
    "saturation_policy": "restrained globally; brass owns the only warm accent",
    "gamut_policy": "compress bright emissive and saturated blue without hue skews",
    "film_emulation": {
      "negative_or_reversal_character": "wide-latitude color-negative behavior",
      "print_or_display_character": "restrained print density and soft highlight shoulder",
      "grain": "fine irregular grain concentrated in shadows and midtones",
      "halation": "low, only around sufficiently bright practical edges",
      "bloom": "minimal and source-motivated",
      "gate_weave": "none",
      "vignette": "subtle optical falloff only"
    },
    "shot_matching": "lock black floor, skin treatment, and grain scale across the sequence",
    "continuity_locks": ["skin hue", "shadow floor", "highlight ceiling", "grain scale"],
    "forbidden_casts": ["global teal-orange", "cyan shadows", "yellow skin", "uniform red halation"]
  }
}
```

Read [color-pipeline.md](color-pipeline.md) for film, digital, black-and-white, print, archival, and sequence-matching rules.

## Render Pipeline

```json
{
  "render_pipeline": {
    "domain": "path_traced",
    "engine_reference": "Blender Cycles",
    "engine_reference_scope": "appearance_reference",
    "lighting_transport": "physically based diffuse, glossy, transmission, shadow, and volume paths",
    "global_illumination": "soft multi-bounce indirect light with restrained color bleed",
    "ray_tracing": "roughness-aware reflections and clean contact visibility",
    "reflection_model": "material-specific specular width; metal reflects environment color",
    "shadow_model": "soft area shadows plus precise contact shadows",
    "ambient_occlusion": "local only at real creases and contacts; never a global dirt layer",
    "volumetrics": "clear air unless the scene owns fog, smoke, dust, or cloud",
    "material_workflow": "principled/OpenPBR-style metallic-roughness layers",
    "subsurface_scattering": "skin, wax, leaves, marble, or food only where physically relevant",
    "transmission_refraction": "IOR-aware glass and liquids with visible edges and background distortion",
    "caustics": "only when visible and worth the noise budget",
    "displacement_normal": "scale-correct displacement for silhouette; normals for microstructure",
    "texture_scale": "texel and microtexture scale match object and camera distance",
    "sampling_denoise": "high samples with detail-preserving denoise; no smeared hair, labels, or highlights",
    "render_passes": ["diffuse", "specular", "transmission", "depth", "cryptomatte"],
    "performance_fidelity_tradeoff": "final still prioritizes fidelity; real-time previews may simplify indirect light",
    "npr_strategy": "",
    "forbidden_artifacts": ["fireflies", "over-dark AO", "plastic roughness", "light leaks", "denoise smear"]
  }
}
```

Engine references describe visual behavior unless `engine_reference_scope` is explicitly `actual_pipeline`. See [render-pipeline.md](render-pipeline.md).

## Style Learning

`mode: learn_style` requires actual image inputs and a `style_learning` object:

```json
{
  "style_learning": {
    "profile_id": "graphite-copper-editorial",
    "profile_name": "Graphite Copper Editorial",
    "scope": "skill_candidate",
    "status": "draft",
    "source_input_ids": ["style-reference"],
    "provenance": "Observed from a user-approved reference; raw image not embedded.",
    "observed": {
      "medium_behavior": "premium editorial infographic with dimensional product-visualization elements",
      "palette_logic": ["graphite owns the field", "copper owns active lines and hierarchy"],
      "shape_line_language": "thin rules, rectilinear panels, one circular lens motif",
      "texture_material_logic": ["matte black", "selective brushed copper", "restrained glass"],
      "lighting_logic": "one motivated warm path with localized highlights",
      "composition_logic": ["large title", "single transformation path", "stacked readable sections"],
      "typography_logic": ["high-contrast title", "clear sans labels", "monospace technical strings"],
      "optics_rendering_logic": "clean low-noise rendering with restrained glow",
      "motifs": ["scene graph", "lens ring", "storyboard grid"]
    },
    "inferred_traits": ["craft precision presented as premium technology"],
    "unknowns": ["original typeface", "source software"],
    "transfer_rules": ["transfer hierarchy and palette ownership, not source content"],
    "forbidden_transfer": ["identity", "exact text", "logo", "exact layout coordinates"],
    "validation_prompts": [],
    "verification_notes": ""
  }
}
```

Scopes are `session`, `project`, or `skill_candidate`; statuses are `draft`, `validated`, or `adopted`. `validated` and `adopted` require at least two transfer-test prompts plus visual review notes. See [style-learning.md](style-learning.md) for export, application, privacy, and adoption rules.

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
      "resistance_cost": "the caster's grounded arm trembles and the seal loses one outer ring",
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

For a UI Motion board, keep the same schema and read [ui-motion-storyboard.md](ui-motion-storyboard.md). Put exact on-screen copy in `text_elements`; put the viewer conclusion, proof object, local interface state, motion phase, accent target, and background rule in the corresponding frame's `story_moment`, `primary_action`, `action_phase`, and `composition`. Use `line_art` with one declared semantic accent rather than inventing a separate full-color presentation mode.

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
  "preserve_surroundings": true
}
```

## Mode-Specific Minimums

### Create

Define `intent`, `canvas`, scene or subject content, and meaningful constraints. Avoid filling every section when it adds no control.

### Reconstruct

Provide at least one image input plus `reference_analysis.target`, non-empty `observed`, optional `inferred`, and non-empty `unknowns`. The deliverable is a functional reconstruction prompt, not a claim to recover the original hidden prompt or software pipeline. See `examples/reconstruct-architecture-reference.json`.

### Edit

Provide a base image input and at least one `spatial_edits` item or `must_change` constraint. Always provide `must_preserve`. Lock identity, geometry, camera, layout, text, or surroundings when they must not drift.

### Restyle

Provide a base image and a style target. Put geometry, subject identity, pose, layout, and literal text in non-empty `must_preserve`; put only the named visual treatment in non-empty `must_change`. See `examples/restyle-risograph-editorial.json`.

### Expand

Provide the base image, new canvas, extension direction, and continuity rules. `must_preserve` and `must_change` are both required. Preserve original content, subject relative position/scale, perspective, exposure, and source-boundary continuity unless the user explicitly requests reframing. See `examples/expand-roadside-outpaint.json`.

### Learn Style

Provide at least one actual image input and a complete `style_learning` record. Separate observed mechanisms, inferred traits, and unknowns. Export only reusable visual rules; do not embed source images or transfer source identity, exact text, logos, signatures, protected designs, or exact layout coordinates. Validated/adopted records require two different scenarios plus non-image evidence bindings to the forward-test manifest.

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

In a UI Motion storyboard, `text_elements` may be genuine in-frame content: SUPER, UI labels, data values, units, brand copy, and source notes. Shot numbers, duration labels, review arrows, and production comments remain outside unless the user explicitly asks to see them in the generated image. Do not replace required exact text with an empty text-safe box by default.

## Render Quality Controls

Use a compact `artifact_budget` instead of repeating a long cleanup list:

```json
{
  "render": {
    "detail_priority": ["primary subject", "hero material"],
    "artifact_budget": "auto",
    "quality_controls": [
      "skin remains matte with soft, localized specular highlights",
      "background gradients remain clean and low-noise"
    ]
  }
}
```

- `auto`: default adaptive prevention for a non-empty generation prompt; emits one medium-preserving clean base but no ratio, camera, grain, bloom, flare, gloss, particles, or new medium. Empty templates and `learn_style` analysis remain neutral.
- `strict`: clean product, typography, diagrams, minimal editorials, and other artifact-intolerant work.
- `balanced`: explicitly requested premium restraint; allows only restrained, scene-motivated grain, bloom, flare, gloss, and particles.
- `clean_reset`: repeated oiliness, speckle, dirty AO, equal-frequency texture, or latent residue; rebuilds low-frequency masses, texture ownership, material boundaries, contact, and exposure from a clean specification rather than preserving failed pixels.
- `expressive`: intentional painterly, analog, fantasy, or effects-heavy work while preserving material separation and focal hierarchy.
- `source_matched`: edits, restyles, and expansions that must inherit the source image's grain, sharpness, bloom, flare, and surface response without adding new artifact classes.
- `quality_controls`: optional shot-specific positive targets. Keep them concise and physically observable.

Do not treat intentional film grain, brush texture, wet gloss, atmospheric particles, or lens artifacts as defects when the user or source explicitly requires them.

Each `materials` item requires `target`, `description`, and `physical_properties`. Optional professional controls are `microstructure`, `roughness`, `specular_response`, `transmission`, `subsurface_behavior`, `anisotropy`, `wear_patina`, and `contact_deformation`. The validator rejects the ambiguous legacy key `properties` even when canonical fields are also present, so material intent cannot be silently dropped during compilation.

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
- Creative routing distinguishes scenario, genre, aesthetic family, production method, scene archetype, and delivery context without duplicating or conflicting with detailed style fields.
- Learned styles preserve observed mechanisms, inference/unknown separation, source-image-free export, reviewed transfer boundaries, advisory copy-risk warnings, and cross-subject validation evidence.
- Professional color describes exposure, tone scale, separation, display intent, film finishing, and continuity instead of generic grading names.
- Render pipeline and hero materials state visible light transport, BRDF/BSDF behavior, texture scale, contact, and artifact risks without claiming unexecuted software.
- Narrative frames bind relationship, staging, lens, camera distance, and motivated light instead of defaulting to poster composition.
- Causal effects have an owner, path, operation, response, and residue.
- Styleboard references have one primary role; frame cards and continuity locks are explicit.
- Artifact controls preserve intentional medium traits while suppressing unmotivated noise, light spots, uniform gloss, and equal-detail rendering.
- Deprecated internal controls are absent from new specs and are never misrepresented as provider-native controls.
- Unobserved reconstruction details are labeled as inference or unknown.
