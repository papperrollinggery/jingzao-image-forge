# UI Motion Storyboard Workflow

Use this reference when a storyboard frame is driven by interface states, data, typography, infographic motion, or a brand-film UI sequence rather than character blocking or a conventional cinematic scene.

The goal is not a pretty dashboard screenshot. The goal is a sequence of executable frames whose content, typography, accent logic, and state changes are clear enough for motion designers to reproduce.

## 1. Lock the Content Before Styling

Build one row per retained frame from the actual script, approved deck, meeting evidence, or user-edited source:

```text
frame id / optional time
viewer conclusion
visible proof object
local UI state
motion phase: before / action / after / hold
exact visible text and type: main SUPER / auxiliary SUPER / UI / data / logo / source
required asset or reference
forbidden drift
```

- Do not restore removed frames or invent connective screens merely because the visual rhythm feels sparse.
- Keep story description, actual on-screen text, data/UI support, and production annotation separate.
- When several readings are genuinely plausible, create named variants. Do not create variants for every frame.

## 2. Establish the Minimum Visual Bible

Lock only the decisions shared across the sequence:

- frame ratio and native resolution;
- base medium and line behavior;
- neutral palette and one approved accent;
- typography hierarchy and alignment grid;
- UI corner radius, stroke, shadow, and depth policy;
- background policy;
- map, cursor, hand, logo, and source-card rules;
- iteration naming and adopted-frame status.

For a clean line-art UI Motion board, a reliable starting system is:

```text
base: white or warm-white field
primary line: charcoal / near-black
secondary line: cool gray
gray fill: restrained, used for inactive states and depth separation
accent: one approved brand or story color
depth: flat 2D layers, overlap and scale; no fake extruded 3D unless requested
texture: subtle pencil or graphite only when the reference owns it
```

Do not force a map, particle field, orbit line, or global network diagram into every frame. Background elements are content-specific.

## 3. Build an Explicit Information Hierarchy

Correct content is not enough. A production-ready UI Motion frame needs unequal visual roles, density falloff, and a protected calm area. Select `styleboard.hierarchy_profile` before writing frame detail:

| Profile | Use when | Required behavior |
|---|---|---|
| `minimal_state` | A button, cursor, toggle, or compact confirmation is the whole beat. | One dominant component plus one proof; continuity and ambient layers may be absent. |
| `layered_editorial` | A brand-film frame combines UI, data, typography, and motion context. | Use all L0–L3 layers, one calm zone, and explicit suppression. This is the default for information-rich UI Motion. |
| `spatial_system` | Maps, networks, warehouses, product ecosystems, or technology fields need depth. | Use all L0–L3 layers and prove foreground/midground/background separation through scale, crop, overlap, line weight, or density. |
| `custom` | A supplied reference demonstrates a different hierarchy. | Describe the observed system without forcing these profiles. |
| `auto` | Ordinary non-UI styleboards or insufficient evidence. | Do not invent a hierarchy system. |

For every layered or spatial frame, write:

```json
"hierarchy": {
  "l0_primary_focus": "one dominant current event, object, number, or action",
  "l1_proof": ["the evidence that makes the claim true"],
  "l2_continuity": ["previous-state residue", "next-state preview or shared process rail"],
  "l3_ambient_scaffold": ["quiet point field", "construction arc or environment trace"],
  "calm_zone": "a protected region with deliberately reduced information density",
  "accent_owner": "the exact semantic target that may use the accent",
  "silenced_elements": ["elements that must recede instead of competing"]
}
```

### Layer roles

- **L0 — primary focus:** exactly one first read. It may be the current card, selected node, key number, central machine, active route, or decisive result. It must still dominate at thumbnail scale.
- **L1 — proof:** one to three elements that prove L0: exact SUPER, unit, object-state relationship, source/receiver pair, or one supporting card. They support the focus instead of becoming a second poster.
- **L2 — continuity:** quiet evidence of before/after and system membership: a cropped previous card, small next-state preview, shared rail, partial neighbor, or route residue. This is what makes the frame feel like one moment inside a film rather than an isolated slide.
- **L3 — ambient scaffold:** the lowest-contrast spatial grammar: point fields, construction arcs, faint routes, environment outlines, or micro-data. Limit it to one or two motif families and keep it behind L0/L1.
- **Calm zone:** one region where line frequency, dot density, and card count deliberately fall. It protects typography and gives dense information somewhere to breathe.

### Hierarchy checks

- Do not solve “more detailed” by adding equally dark cards, icons, and lines everywhere.
- Prefer one enlarged current state, one or two quieter neighbors, and partial edge crops over three equal cards.
- Use size, crop, overlap, line weight, gray value, density, and completeness together; color alone is not hierarchy.
- Keep the detail topology asymmetric: one dense focal cluster, one supporting cluster, and one calm field is usually stronger than evenly distributing detail.
- In a close-up, L2 and L3 may be only edge residue and a faint rail. In a map or system frame, they may become geographic or environmental context, but still remain subordinate.
- For a production sequence with frame-specific text and density, default to `independent_frames`. Use a direct sheet only for calibration, comparison, or a user-requested board; a successful contact sheet does not prove each native 16:9 frame meets the final standard.

## 4. Typography Is Part of the Composition

Exact visible text belongs in `text_elements`. Treat it like a graphic object, not a late annotation.

### Hierarchy

- **Main SUPER:** one dominant statement, normally one or two lines; it owns the first read.
- **Auxiliary SUPER:** one supporting fact or qualifier; it must not compete with the main statement.
- **Data value:** the numeral may dominate, but its unit and scope remain readable.
- **UI label:** short functional copy placed inside the component it controls.
- **Logo/lockup:** use an attached approved asset when its exact form matters.
- **Source note:** small but readable; never substitute a logo for a source unless the brief requires it.

### Layout checks

- preserve exact characters, punctuation, capitalization, units, and approved line breaks;
- use a grid and optical alignment rather than centering every element by default;
- balance large numerals with title text instead of boxing every line;
- keep text clear of frame edges and busy line clusters;
- do not place a short phrase in an oversized empty card merely to fill space;
- avoid arbitrary narrow columns, uneven baselines, orphaned characters, and mixed typographic styles;
- reject generated text that is semantically close but not exact.

Production labels, shot numbers, duration notes, arrows explaining the edit, and review comments stay outside the generated image unless the user explicitly wants them inside. In-frame SUPER, data, UI labels, and brand copy remain inside when the brief requires them. Do not leave empty “text-safe” boxes unless the user asked for a later overlay workflow.

## 5. Accent Color Must Own a Meaning

An accent color is a semantic layer, not decoration. Assign it to one or more explicit meanings:

- selected or active state;
- current progress or route;
- key number or ranking;
- decisive button, cursor, rocket, node, or result;
- one transition bridge carried into the next frame.

Keep inactive elements neutral. As a starting guardrail, accent coverage is usually restrained—often around 5–15% of the image—but the visible hierarchy, brand system, and frame purpose take precedence over a fixed percentage.

Use the approved brand accent. Orange is appropriate only when the brand or project owns orange. Do not introduce generic orange merely because the work is called UI Motion.

Reject these failures:

- every icon and outline is colored;
- accent color appears on unrelated decorative geometry;
- accent competes with the main SUPER;
- two or more accent colors have no separate semantic ownership;
- grayscale frames drift into glossy full-color renders;
- the accent disappears on the state that is supposed to be active.

## 6. Design Local UI States, Not One Global Screen

A functional UI beat is usually clearer as separate frames:

```text
before: component and available choice are visible
action: pointer, selection, drag, progress, or state change is visible
after: result, confirmation, or next node is visible
```

- Enlarge the active component until the intended interaction reads at storyboard scale.
- Show only the surrounding context needed to understand that component.
- Use a mouse pointer for desktop UI by default. Use a finger or hand only for touch devices or an explicitly staged live-action interaction.
- Keep one dominant action per frame. A frame may have one secondary response, not several competing state changes.
- Onboarding, checkout, search, fulfillment, analytics, or another user-provided product flow should be broken into readable UI states rather than collapsed into one all-purpose dashboard. Preserve brand-specific flow names only when the brief provides them.

## 7. Maps, Data, and Brand Assets

### Maps

- Use a map only when geography, coverage, distance, route, or regional data is the actual proof.
- Preserve the approved map language across map frames: dot density, border abstraction, node style, line style, and island coverage.
- Do not continue a map background into unrelated UI steps.

### Data

- Make the number, unit, comparison, and scope agree.
- Use progress bars, routes, bars, counters, or nodes only when they prove the claim.
- The highlighted portion represents the active or compared value; decoration does not count as proof.

### Logos

- Attach and use the actual asset when exact identity matters.
- A standalone app icon may use a model-known mark only when the user accepts that route and the result is visually verified.
- Do not add logos to data-source screens, neutral evidence cards, or frames where the brief does not place them.

## 8. Prompt Construction

Write positive visible targets first:

```text
16:9 UI Motion storyboard frame, flat 2D graphite line art on warm white.
One dominant local interface state: [component and state].
Exact visible text: [literal strings with hierarchy and line breaks].
Primary read: [viewer conclusion].
Proof: [number, route, button, selected card, map coverage, or result].
Hierarchy: [L0 focus]; [L1 proof]; [L2 continuity]; [L3 ambient scaffold]; calm zone [location].
Approved accent [color] appears only on [semantic targets]; all inactive elements stay gray.
Typography: [alignment, scale relation, weight, max lines, spacing].
Motion evidence: [before/action/after state and direction].
Preserve: [layout, brand asset, map language, line style, exact text].
```

Use a compact current-risk exclusion block, for example:

```text
No full dashboard, equal-weight cards, uniformly dark detail, unexplained dead space,
fake 3D extrusion, decorative map, hand cursor, extra logo, invented copy,
warped text, arbitrary colored icons, visible frame IDs, shot numbers,
duration labels, review arrows, production annotations, or unrelated motion trails.
```

Do not accumulate every previous failure in the exclusion list. Keep only risks relevant to the current frame.

## 9. Generation and Iteration Loop

1. Freeze the retained frame list and exact text ledger.
2. Approve one or two calibration frames that test L0–L3 hierarchy, calm-zone placement, typography, line finish, UI scale, and accent ownership.
3. Generate the complete first pass without repeatedly stopping to replace earlier frames.
4. Review the full sequence for content and visual language.
5. Mark each frame `adopted`, `candidate`, or `replace`; record the exact reason.
6. Regenerate only failed frames or true alternatives, preserving approved neighbors.
7. Run one full-sequence review after replacements.

Do not respond to one bad frame by reinterpreting the entire visual language. Correct the smallest responsible layer: L0 focus, L1 proof, L2 continuity, L3 scaffold, calm zone, content, text, UI state, accent, style, or asset use.

## 10. Full-Sequence Review

Review after the first pass is complete:

- **Content:** each frame proves the intended statement; no deleted or invented beat returns.
- **Typography:** exact copy, readable hierarchy, deliberate line breaks, consistent alignment.
- **Hierarchy:** one L0 dominates at thumbnail scale; L1 proves it; L2 connects the beat to its neighbors; L3 creates depth without equal-weight clutter; one calm zone survives.
- **Density:** detail is intentionally asymmetric and falls off by layer; no frame becomes a uniform field of cards, dots, or outlines.
- **Style:** 2D line language stays stable; no random fake 3D, stone, gloss, or full-color drift.
- **Accent:** every orange/brand-color area has declared semantic ownership.
- **UI Motion:** each interaction is a readable local state; the sequence shows progression.
- **Background:** maps and network motifs appear only where content requires them.
- **Input device:** cursor, touch, remote, or physical action matches the scene.
- **Brand:** exact logos appear where required and nowhere else.
- **Composition:** empty space is intentional; no unexplained dead half, tiny map, or cramped text card.
- **Continuity:** adopted frames keep scale, line weight, gray values, accent, and component language.

## 11. Source and Iteration Archive

Keep one flat archive unless the user requests folders. Use filenames and a manifest to separate provenance:

```text
S012_迭代01_本地历史.png
S012_迭代02_网页上传参考_本地同源.png
S012_迭代03_ChatGPT生成_候选.png
S012_迭代04_ChatGPT生成_当前采用.png
```

The manifest records frame/group, iteration, source type, source name/time, current adoption, exact pixel match, visual similarity when needed, and hash. Downloading, extracting, or matching an asset does not authorize client use or external distribution.
