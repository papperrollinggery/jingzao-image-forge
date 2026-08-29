# Reference-Led Styleboard Mode

Use `mode: styleboard` for a triptych, contact sheet, nine-grid storyboard, vertical storyboard, camera study, visual-development board, or reference-led multi-frame presentation.

For interface-led brand-film frames, product walkthroughs, animated infographics, exact in-frame typography, restrained semantic accent color, or a requested L0–L3 information hierarchy, also read [ui-motion-storyboard.md](ui-motion-storyboard.md).

## Core Principle

Analyze first, choose the generation strategy from speed and continuity risk, then verify or assemble the board as that strategy requires.

Choose the execution path from speed and continuity risk. One-call 3×3 generation is a legitimate fast path; independent frames are a precision path, not a universal requirement.

## Generation Strategies

- `sheet_direct`: generate the complete grid in one call. Fastest for rough boards, broad camera exploration, internal review, and early story rhythm. Verify cell count, ratio, character drift, panel continuity, and crop geometry before final use.
- `independent_frames`: generate every native-ratio frame separately and assemble afterward. Use for strict identity, wardrobe, camera, match-cut, prop-state, frame-specific typography/hierarchy, or high-resolution final delivery. This is the default for production UI Motion sequences whose information density changes by beat.
- `hybrid`: generate a direct sheet first, select the useful composition and rhythm, then regenerate only chosen or failed cells independently. This is often the best speed/quality tradeoff.
- `auto`: choose `sheet_direct` when speed and exploration dominate, `independent_frames` when continuity risk dominates, and `hybrid` when a fast board is useful but selected frames need final quality.

## Reference Roles

Inspect every supplied image. Assign one primary role:

- `identity`: face, anatomy, silhouette, proportions, species, recurring marks;
- `wardrobe`: outfit silhouette, layers, color, accessories;
- `scene`: architecture, geography, roads, rooms, vegetation, stage;
- `prop`: shape, scale, state, and handling;
- `camera_action`: shot size, height, focal-length feel, subject scale, action phase, direction;
- `style`: medium, line, texture, render surface, finishing;
- `layout`: grid, margins, gutters, panel hierarchy;
- `palette`: color relationships only.

Write what to use and what to ignore. Keep one primary role. When one image genuinely proves additional layers, record them as explicit `secondary_roles`; do not let a style reference silently replace identity or a camera reference silently replace subject, wardrobe, and location.

A validated `style_capsule` may replace repeated style-reference prose across the board. It controls only transferable visual rules; frame-specific identity, wardrobe, scene, camera, action, text, and continuity locks remain authoritative.

## Presentation Presets

- `line_art`: clean black-and-white line art, variable line weight, readable silhouette, and minimal gray. It may use one explicitly declared semantic accent color; otherwise it remains colorless.
- `hand_drawn`: pencil, marker, charcoal, ink, or brush storyboard with paper texture and controlled gray values.
- `cinematic_frame`: polished film-frame images with realistic or requested-medium camera, light, color, material, and depth.
- `mixed`: rough planning frames plus selected polished key frames; declare which frame uses which finish.

## Nine-Grid Preset

```json
{
  "styleboard": {
    "layout": "3x3",
    "frame_count": 9,
    "frame_aspect_ratio": "16:9",
    "presentation": "hand_drawn",
    "generation_strategy": "auto",
    "reading_order": "left_to_right_top_to_bottom"
  }
}
```

Use `9:16` for a vertical-video storyboard when requested. Frame ratio belongs to each individual frame; the assembled board is a presentation container.

For equal-cell `sheet_direct` or `hybrid` generation, derive the board ratio from the grid: `board ratio = frame ratio × columns ÷ rows`. A 3×3 board therefore shares each cell's ratio, while a horizontal 3×1 triptych of 16:9 cells needs a 16:3 board. Use a custom assembly workflow when cells have mixed ratios or unequal sizes.

## Frame Card

Each frame contains one scene, one primary action, one action phase, and at most one secondary response:

```text
frame id / optional time
shot function
story moment
subjects, wardrobe, scene, prop state
primary action and phase: prepare / initiate / contact / response / hold
viewer position
shot size, camera height, focal-length feel, camera state
foreground / midground / background and frame safety
screen direction, eyeline, axis, attention path
reference assignments
continuity locks and allowed variation
hierarchy profile when needed
L0 primary focus / L1 proof / L2 continuity / L3 ambient scaffold
calm zone / accent owner / silenced competitors
one-sentence generation image
```

Do not use unresolved options such as “turn / jump / hold whichever works.”

## User-Preferred Working Pattern

Default to these practices unless the brief overrides them:

- client-readable story sentence plus camera sentence for every frame;
- references separated by role;
- explicit generation strategy selected from speed and continuity risk;
- production story text, frame IDs, shot numbers, duration labels, edit arrows, and review annotations added outside the generated image and explicitly excluded from model-visible content; exact UI labels, data, SUPER, and brand copy remain inside when the brief requires them;
- character, wardrobe, scene, prop, camera, and style continuity tracked separately;
- approved frames are reused or minimally edited rather than regenerated broadly;
- match-cut pairs share geometry, orientation, focal-length feel, scale, hand/prop state, and action phase;
- line-art, hand-drawn, and realistic cinematic-frame finishes remain explicit choices.
- UI Motion frames use `minimal_state`, `layered_editorial`, `spatial_system`, or a reference-derived `custom` hierarchy; ordinary styleboards leave `hierarchy_profile` at `auto`.

## Assembly

- for `sheet_direct`, preserve the original board plus any extracted cells; for `independent_frames` and `hybrid`, assemble approved frames left-to-right, top-to-bottom;
- use thin consistent gutters and a neutral board background;
- do not stretch frames;
- add production labels outside frames after generation; do not remove or replace exact in-frame UI/SUPER text required by the brief;
- retain individual source frames and a manifest that maps frame id, row, column, aspect ratio, source, and output path;
- if one frame fails, use a targeted board edit or regenerate only that frame rather than discarding the whole useful sheet.

## Continuity Gate

- identity, body proportions, wardrobe, and recurring marks remain stable;
- location geography, weather, time, light direction, and color logic remain coherent;
- props have tracked owner, state, position, and transition;
- subject movement and eyelines preserve screen direction unless a motivated reversal is shown;
- adjacent frames change information, relationship, action phase, or viewer position;
- the nine frames do not repeat the same subject count, shot size, and attention flow without a reason;
- each frame has one readable function and does not become a multi-scene collage;
- layered UI Motion keeps exactly one L0 first read, lets L1 prove it, uses L2 for previous/next continuity, pushes L3 behind the action, and preserves one calm zone instead of distributing equal-weight detail across the frame;
- line-art or hand-drawn style does not drift into full-color rendering; one approved semantic accent may remain when declared. Cinematic frames do not drift into poster art unless requested.
