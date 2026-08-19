# Render Pipeline and Engine-Reference Vocabulary

Use this reference for Blender, Unreal Engine, RenderMan, Arnold, V-Ray, Octane, Redshift, real-time rendering, path tracing, ray tracing, global illumination, or professional CG material requests.

An engine name is a high-density visual anchor. In a prompt, label it as `appearance_reference` unless the user is describing an actual production pipeline. Do not claim an image model literally ran Blender Cycles or Unreal Engine.

## Render Domains

- `physically_based_offline`: production rendering with material/light transport as the main quality driver.
- `path_traced`: multi-bounce physically based appearance, controlled samples, noise, caustics, and denoising.
- `real_time`: dynamic lighting and reflections with an explicit fidelity/performance tradeoff.
- `rasterized`: fast direct/indirect approximations, probes, baked lighting, or screen-space methods.
- `npr`: cel, toon, line, painterly, graphic, or hybrid non-photoreal rendering with declared shading rules.
- `hybrid_layered`: a single generated image whose practical/live-action, CG, matte, projection, or 2D appearance layers have explicit ownership and matching rules.
- `custom`: a user-defined render behavior.

## Engine References

### Blender Cycles

Use for physically based path-traced appearance, flexible shading nodes, diffuse/glossy/transmission/volume light paths, controlled bounce depth, caustic/noise tradeoffs, and visible pass-separation intent.

### Blender Eevee

Use for physically based real-time appearance, faster iteration, probes/screen-space or ray-traced features where supported, and deliberate approximation rather than pretending it is identical to offline path tracing.

### Unreal Engine 5

Use for real-time cinematic environments, Lumen-style dynamic diffuse interreflection and reflections, sky shadowing, emissive bounce with noise limits, roughness-aware reflections, virtual-production or game-camera context, and a declared performance/fidelity balance.

### Offline Production Renderers

RenderMan, Arnold, V-Ray, Octane, Redshift, and similar systems can anchor production-CG appearance, but the visible rules still need to state material layering, light transport, sampling/noise, volumes, and single-image layer integration. Do not stack several renderer names as style adjectives.

## Light Transport

Describe only relevant mechanisms:

- direct light and shadow;
- diffuse global illumination and color bleed;
- indirect specular/reflections across roughness values;
- transmission/refraction and IOR behavior;
- subsurface scattering for skin, wax, leaves, marble, or food;
- caustics when visible and worth the noise/complexity;
- ambient occlusion/contact darkening as a local grounding aid, not fake global shading;
- volumetric absorption/scattering, fog, smoke, cloud, and light shafts;
- emissive surfaces with a declared size, intensity, and noise risk.

## PBR Material Workflow

For every hero material, specify:

```text
base material and microstructure
metallic/dielectric behavior
roughness and specular lobe width
IOR, transmission, translucency, or subsurface behavior
coat, sheen, anisotropy, or thin-film behavior when relevant
normal/bump/displacement scale
wear, patina, fingerprints, dust, water, or damage only at plausible zones
contact, compression, deformation, and environment reflection
```

Principled/OpenPBR-style language is most useful when tied to a visible surface. “PBR” alone does not create realism.

## Sampling, Denoising, and Artifacts

- More samples reduce stochastic noise but do not fix wrong materials or lighting.
- Denoising must preserve texture, hair, thin geometry, and small highlights.
- Fireflies often come from difficult high-energy specular, transmission, or caustic paths; do not solve them by flattening every highlight.
- Real-time GI/reflection systems may show screen-space loss, temporal instability, emissive noise, or low-resolution indirect lighting; name only the relevant risk.
- Avoid plastic uniform roughness, floating contact, light leaks, shadow acne, over-dark AO, texture-scale mismatch, smeared denoise, and identical detail at every distance.

## Render Pass Intent

Useful pass concepts include diffuse, specular, emission, transmission, volume, shadow, normal, depth, motion vector, cryptomatte/object ID, and ambient occlusion. In prompts, use them only to explain visible separation or balance inside one generated image. Jingzao never turns these concepts into a post-generation compositing step.

## Prompt Examples

```text
Render pipeline: Blender Cycles appearance reference only; physically based path-traced product render with soft multi-bounce global illumination, roughness-aware reflections, clean contact shadows, controlled transmission through frosted glass, subtle anisotropic brushed-metal highlights, scale-accurate microtexture, high samples with detail-preserving denoise, and separate diffuse/specular/transmission passes. Avoid fireflies, over-dark AO, plastic roughness, floating contact, and denoise-smudged label edges.
```

```text
Render pipeline: Unreal Engine 5 real-time cinematic appearance reference only; dynamic Lumen-like diffuse interreflection and indirect specular, sky-shadowed interior depth, roughness-correct reflections, restrained emissive bounce from large practical surfaces, virtual-shadow-map-like contact precision, and a cinematic camera path. Preserve plausible real-time constraints; avoid tiny overbright emissives, temporal reflection noise, screen-space disappearance, and generic game-CG gloss.
```

## Gate

- Engine reference scope is explicit.
- Lighting transport matches the target renderer class.
- Hero materials have distinct BRDF/BSDF behavior.
- GI, reflection, volume, and contact serve the scene rather than inflate jargon.
- Sampling/denoise language protects actual detail.
- The prompt never claims engine execution without an actual engine workflow.
