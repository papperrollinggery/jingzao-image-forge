# Visual Direction Profiles

Use this reference to translate a request into an appropriate visual treatment without forcing all images into grounded realism or poster spectacle.

## Analysis Matrix

Resolve these dimensions independently:

```text
deliverable: narrative_film_frame / cinematic_key_art / poster / concept_art
treatment: grounded_cinematic / heightened_cinematic / graphic_stylized
spectacle_scale: intimate / dramatic / monumental / mythic
camera_freedom: physical / heightened / impossible
genre and world rule
effect logic and medium
viewer result
```

The dimensions can combine. A Chinese-fantasy narrative frame may be `heightened_cinematic + monumental + heightened camera`; a giant-creature poster may be `cinematic_key_art + graphic_stylized + mythic + impossible camera`.

## Grounded Cinematic

Use for naturalistic drama, documentary observation, realistic history, grounded suspense, practical action, and any request where the camera should feel physically present.

- camera has a plausible position and access path;
- lens, distance, and height preserve believable perspective;
- blocking, eyelines, barriers, and offscreen space carry relationship;
- one primary source plus plausible ambient or reflected light;
- VFX remains invisible, restrained, or physically integrated;
- allow partial occlusion, ordinary surfaces, uneven exposure, and unresolved areas.

Failure: polished advertising, decorative rim light, every face evenly lit, montage-like simultaneous information.

## Heightened Cinematic

Use when the user wants expressive angles, strong perspective, designed light, subjective distortion, dream logic, horror pressure, operatic action, or visibly art-directed cinema while retaining story causality.

- exaggerate one primary variable: angle, lens perspective, color contrast, spatial compression, silhouette, reflection, or motion implication;
- state the viewer effect and why the exaggeration belongs to this beat;
- preserve body/space relationships, focal hierarchy, and a readable action or emotional endpoint;
- stylized light still has world ownership or a stated subjective rule;
- camera may enter a difficult but explainable position; impossible motion belongs to `graphic_stylized` or an explicitly impossible camera.

Failure: stacking dutch angle, extreme wide lens, rim light, smoke, particles, reflections, and saturated color with no primary function.

## Graphic Stylized

Use for animation, illustration, comics, ink, paper, collage, 2D/3D hybrid, designed impact frames, or deliberately impossible visual grammar.

- lock medium, palette ownership, shape/line rules, texture, layer behavior, and forbidden drift;
- graphic elements need source, spatial layer, tension state, interaction, occlusion, and consequence;
- impossible camera or scale changes remain compositionally readable;
- continuity relies on silhouette, costume, palette, repeated motifs, and layout rules rather than photoreal optics;
- film grammar may guide attention and story without converting the image to live action.

Failure: style-name salad, random effects, mixed media with no layer ownership, poster hierarchy replacing the requested story beat.

## Giant and Monumental Scale

Scale must be proven, not stated.

Use several independent cues, but keep one primary read:

- human-scale foreground witness, architecture, vehicle, terrain, weather system, or known object;
- atmospheric depth, occlusion, parallax, focus behavior, shadow extent, and delayed environment response;
- camera placed at a consequential height and distance: ground witness, interior window, rooftop, aircraft, distant observation, or impossible overview when explicitly desired;
- partial visibility can increase scale: body exits frame, cloud layer hides sections, feet or base remain unseen;
- environment reacts according to mass, displacement, wind, pressure, vibration, water, debris, or light blocking.

For a narrative frame, show one relationship between the giant force and a human-scale subject. For key art or poster, broader simultaneous display is allowed.

Failure: giant object floating cleanly against a sky, no scale reference, miniature-like depth of field, every surface equally detailed, generic superhero stance.

## Chinese Fantasy / Xianxia / Xuanhuan

Do not equate Chinese fantasy with glowing swords, random talismans, floating rocks, colored fog, and decorative particles.

Define the supernatural system:

```text
power source -> activation protocol -> governing material or symbol ->
spatial operation -> resistance or cost -> result -> residue
```

The effect must perform one operation: bind, redirect, reveal, divide, purify, exchange, suppress, summon, seal, transform, or destroy.

- owner and source are visible or inferable;
- body action, tool, breath, gesture, formation, environment, or ritual triggers the effect;
- path and depth layer are readable;
- receiver and environment respond physically or according to the world's law;
- emissive light affects nearby surfaces by distance and occlusion;
- use one dominant effect family and at most one supporting family;
- particles, smoke, debris, and light decay after the selected hero intensity;
- costume, architecture, landscape, materials, and social order carry the world before effects do.

For grounded xianxia, keep camera access and physical sets plausible. For heightened or graphic xianxia, exaggerate shape rhythm, scale, color ownership, or impossible viewpoint while preserving effect causality and character identity.

## Deep-Analysis Output

When the user asks the Skill to choose automatically, return a compact decision block before the specification or prompt:

```text
视觉意图判断：
- 操作模式：
- 交付类型：
- 处理方式：
- 奇观尺度：
- 摄影自由度：
- 题材 / 世界规则：
- 观众要获得的结果：
- 主要镜头或构图机制：
- 特效主读与边界：
- 推荐画幅及理由：
```

Keep the analysis concrete and tied to visible output. Do not expose long internal chains or generic aesthetic commentary.
