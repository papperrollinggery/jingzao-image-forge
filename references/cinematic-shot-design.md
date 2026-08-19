# Cinematic Narrative Shot Design

Use this reference for a single image that should feel like a frame taken from an unfolding film scene rather than a poster, key visual, game splash screen, or asset showcase.

This layer is medium-neutral. Preserve live action, animation, illustration, or another requested medium while applying filmable spatial and narrative logic.

## Film Frame vs Poster

| Narrative film frame | Poster / key art |
| --- | --- |
| one causally informative frozen moment | simultaneous presentation of major assets |
| viewer occupies a motivated position | viewer receives an idealized overview |
| blocking and occlusion express relationship | hierarchy comes from heroic scale and graphic layout |
| some information remains offscreen or withheld | characters, props, and effects are clearly displayed |
| shot size and lens serve one viewer task | camera choices maximize spectacle and recognition |
| light comes from the scene and changes interpretation | rim light and effects often separate every element |
| selective focus and ordinary areas are allowed | high finish and equal legibility dominate |

Do not remove poster qualities when the user actually requests a poster, cover, campaign image, or key art.

## Scene Contract

Write these before choosing a lens or angle:

```text
visible event: what changes or is about to change?
relationship pressure: who watches, approaches, avoids, controls, waits, or loses initiative?
viewer task: what must the audience notice, infer, or remember?
emotional result: what state should the frame leave behind?
withheld information: what remains outside the frame, obscured, delayed, or unresolved?
```

## Frozen Moment

A still can show one causally informative state. Select a moment with a visible trace of what just happened or will happen next:

- attention lands before a decision;
- a hand stops before contact;
- one character notices what another missed;
- an action creates a readable consequence;
- distance, gaze, posture, barrier, or object behavior changes a relationship.

Do not ask one frame to show setup, attack, reaction, victory, aftermath, and every important prop simultaneously.

## Viewer Position and Relationship Geometry

Choose the viewer position before the camera vocabulary:

- inside the relationship: shared eye level, over-shoulder, close observational distance;
- outside it: doorway, window, corridor, crowd, vehicle, reflection, or long-lens observation;
- pressured by it: low constrained position, blocked foreground, narrow available camera zone;
- aligned with one character: inherited eyeline, partial body foreground, subjective focus;
- deliberately misaligned: only when discomfort or incomplete understanding is the intended result.

Record:

```text
primary relationship and axis
screen-left / screen-right or near / far placement
body direction vs gaze direction
distance, contact, shared object, or barrier
foreground occlusion and why the camera is there
attention entry -> interruption -> decisive landing -> unresolved exit
```

## Shot Function Before Shot Size

Choose one primary function:

- `establish`: space, scale, direction, relationship;
- `introduce`: reveal a character, object, threat, or goal;
- `observe`: read behavior, restraint, or mood;
- `follow`: preserve directional energy through a frozen state;
- `emphasize`: isolate a decision, clue, hand, face, or contact point;
- `react`: show a visible consequence;
- `transition`: connect states through one visual bridge;
- `resolve`: hold the new state so the beat lands.

Then select the minimum shot size that contains the required information. Wide shots serve geography and full-body relation; medium shots serve hands, torso, face, and interaction; close-ups serve one decisive leak or detail.

## Camera and Lens Coupling

Focal length, distance, height, and framing are one system:

| Lens intent | Use | Misuse boundary |
| --- | --- | --- |
| 24–28mm | environment pressure, close spatial tension, scale with a justified near camera | not for a clean recognizable face inside an extreme-wide showcase |
| 32–40mm | environmental observation, blocking, active two-shots, grounded movement | avoid using it as a generic “cinematic” token |
| 50mm | natural relational distance, medium performance, restrained observation | does not automatically create intimacy |
| 65–85mm | compression, surveillance, isolation, reaction, selective background relation | avoid blur that removes required geography |
| long lens through foreground | being watched, distance, crowd, separation | requires a plausible observation position and visible compression logic |

For every shot, state:

```text
camera motivation: why is the viewer here?
camera height: whose physical or psychological level?
camera distance: what relationship must remain visible?
focal length and rationale: what spatial effect serves the beat?
subject frame ratio: how much of the frame belongs to people vs environment?
focus plane: what is sharp, and what is allowed to fall away?
```

Low angle is not automatically powerful; high angle is not automatically weak. Height must organize gaze, background, bodies, obstacles, and viewer position.

## Performance in One Frame

Use observable behavior rather than emotion labels:

- gaze target and focus delay;
- eyelid, jaw, lip, swallow, or breath trace;
- weight, turn, withdrawal, approach, freeze, or recovery;
- grip, release, fold, align, set down, miss, or unfinished object action;
- distance, touch, refusal, barrier, and residual posture.

Choose only 2–4 dominant channels visible at the selected framing.

## Motivated Lighting

Default to one primary source plus one plausible reflection, ambient source, or practical when needed.

Define:

```text
source: window, sky, lamp, fire, screen, doorway, reflected wall, water, snow
direction and falloff
which relationship or story fact it reveals
what remains underexposed or unresolved
how color enters through physical surfaces
```

Lighting serves the viewer task. It should not outline every character, illuminate every prop, or replace blocking and performance with decorative drama.

## Cinematic Ultrawide Preset

Use when horizontal space carries narrative meaning:

```json
{
  "canvas": {
    "profile": "cinematic_ultrawide",
    "aspect_ratio": "21:9",
    "dimensions": {"width": 1792, "height": 768}
  }
}
```

The profile also accepts an explicitly requested `2.35:1` or `2.39:1` ratio. Use the width for lateral distance, barriers, opposing movement, offscreen pressure, giant-scale comparison, or layered geography—not as a cosmetic crop.

## Posterization Guard

Rewrite when several appear together:

- centered full-body hero plus fully visible enemies and props;
- all actions and consequences presented at once;
- symmetrical or triangular showcase composition without a viewer position;
- magic, smoke, sparks, rim light, and clouds acting as graphic decoration;
- equal sharpness and polish across the frame;
- every character facing the viewer or posed for recognition;
- clean silhouette separation that destroys believable overlap and occlusion;
- “epic”, “masterpiece”, or “cinematic” replacing camera logic.

## Review

- Can the visible event and relationship pressure be stated without style words?
- Is the frozen moment more informative than a generic action pose?
- Is the viewer position physically and narratively explainable?
- Do blocking, eyelines, axis, distance, and occlusion agree?
- Do camera height, distance, focal length, and shot size serve the same viewer task?
- Does light come from named sources and prioritize decisive information?
- Does the frame preserve offscreen space, partial information, and ordinary areas?
