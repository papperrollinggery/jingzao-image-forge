# Professional Color Pipeline and Film Finishing

Use this reference when color, grading, a film look, continuity, skin tone, archival reproduction, or final display character materially affects the image. A professional color direction is a tonal and chromatic system, not a named LUT or the phrase “cinematic color grading.”

## Routing Order

```text
capture/render intent -> color science and display target -> exposure ->
tonal curve -> black/white points -> highlight/shadow behavior ->
color separation and biases -> skin/saturation/gamut policy ->
film or digital finishing -> shot matching and continuity
```

The prompt describes the visible result. It does not claim to perform an actual ACES, Resolve, ARRI, or film-lab transform unless the user's pipeline truly does so.

## Pipeline Intents

- `neutral_digital`: clean color, accurate material separation, minimal medium artifacts.
- `cinematic_color`: story-owned tonal and color hierarchy without requiring film emulation.
- `film_emulation`: negative/reversal and print/display character plus physically plausible grain and halation behavior.
- `print_emulation`: reduced color volume, print-density behavior, paper/ink or release-print character.
- `bleach_bypass`: retained silver-like density, reduced saturation, hard microcontrast; use only when the story needs severity.
- `black_and_white`: luminance, spectral separation, grain, and print density replace hue design.
- `cross_processed`: deliberate color crossover and contrast instability; avoid generic random casts.
- `archival_reproduction`: source format, age, scanning/reproduction, and uncertainty remain visible.
- `custom`: one user-defined color system with an explicit description.

## Tonal Design

Define:

- exposure strategy and protected information;
- black point versus readable shadow floor;
- midtone density and facial/material separation;
- white point and specular peak behavior;
- highlight rolloff, especially near skin, practical lights, windows, metal, and water;
- whether the curve is soft, firm, high-key, low-key, compressed, or deliberately harsh.

Do not use crushed blacks or clipped highlights as shorthand for cinema. Dense blacks can retain local information; bright sources can roll into white without flattening every nearby surface.

## Chromatic Design

- White balance belongs to the world source, not a universal preset.
- Color separation states how adjacent materials, skin, wardrobe, and environment remain distinguishable.
- Shadow, midtone, and highlight biases have different jobs; do not tint the entire frame uniformly.
- Skin-tone policy protects believable hue and luminance even when the environment is stylized.
- Saturation policy assigns where strong color is allowed and where it is withheld.
- Gamut policy describes how highly saturated emissive, fabric, neon, foliage, or VFX color remains controlled.
- Teal/orange is valid only when scene sources, production design, or story ownership motivates the separation.

## Film Emulation

Separate the layers:

```text
negative or reversal character
-> print or display character
-> grain
-> halation
-> bloom
-> gate weave / flicker / vignette when intentionally visible
```

- Grain follows exposure and scale; it is not a uniform noise overlay.
- Halation is restrained around sufficiently bright edges and practical sources, not a global red glow.
- Bloom is broader optical light spread and remains source-motivated.
- Gate weave, flicker, dust, scratches, and vignette are optional historical/physical artifacts, not automatic “film quality.”
- A clean digital image with filmic highlight rolloff can be more cinematic than a dirty film preset.

## Shot and Sequence Continuity

For multi-shot work, lock:

- display target and overall tone scale;
- skin and hero-material treatment;
- black floor, highlight ceiling, and saturation ceiling;
- scene-owned warm/cool relationships;
- grain scale, halation threshold, and optical finishing intensity.

Match exposure and color around the story beat. Do not flatten deliberate day/night, location, memory, threat, or subjective changes into identical grading.

## Prompt Example

```text
Color pipeline: cinematic_color for SDR display; protect one stop of highlight texture around the window and practical lamp, maintain a readable cool shadow floor, medium-dense midtones, and soft natural highlight rolloff. Warm amber belongs only to the practical and the brass object; cool blue belongs to exterior ambient light. Preserve natural skin hue between both pools. Saturation remains restrained except for the brass accent. Fine irregular grain lives mostly in shadows and midtones; low halation only at the practical bulb edge; no global teal-orange cast, clipped forehead, crushed hands, or uniform grain overlay.
```

## Research Basis

- ARRI distinguishes log capture, technical display conversion, and creative Look Files; its camera guidance emphasizes exposure latitude and film-like highlight rolloff.
- ACES separates scene-referred source data, creative Look Transforms, rendering transforms, and display encoding; output transforms are display/viewing-condition specific.
- DaVinci Resolve's film-look tools separate grain-like behavior, halation, bloom, gate weave, flicker, and vignette rather than treating “film” as one switch.

## Gate

- Color decisions serve the scene and target display.
- The tonal curve names protected highlights, shadows, and midtones.
- Color biases have layer ownership.
- Film artifacts have source, threshold, scale, and intensity.
- Skin, product labels, brand color, historical source color, and VFX color receive explicit protection when relevant.
- The grade does not replace production design, lighting, material response, or camera design.
