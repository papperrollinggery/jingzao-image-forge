# Artifact and Material Quality Controls

Use this reference when a prompt or generated output shows unwanted speckle, noisy microtexture, decorative light spots, uncontrolled bloom or flare, waxy skin, oily surfaces, uniform plastic gloss, sharpening halos, muddy shadows, or equally sharp detail everywhere.

These are prompt and review risks, not proof of a model's internal cause. Diagnose the visible result before changing the specification.

## Quality Model

Build quality in this order:

1. subject, identity, action, composition, and medium;
2. hero materials and their physical surface response;
3. motivated light sources, highlight rolloff, contact, and exposure;
4. focal-detail hierarchy and background falloff;
5. one compact artifact budget;
6. a short current-risk avoid block only when the platform supports or benefits from it.

Generic quality adjectives such as `8K`, `ultra detailed`, `hyper realistic`, or `cinematic` do not replace physical material and lighting decisions.

## Artifact Budgets

| Budget | Use when | Default behavior |
| --- | --- | --- |
| `auto` | first-pass generation without a demonstrated artifact risk | emit no preset; let the requested subject, medium, material, and light lead |
| `strict` | products, typography, diagrams, clean editorials | clean gradients, contained highlights, clear air, no decorative texture systems |
| `balanced` | premium imagery that explicitly needs restrained finishing | restrained source-driven effects, natural material roughness, selective focal detail |
| `expressive` | painterly, analog, fantasy, VFX-heavy work | intentional artifacts allowed only when coherent with medium, event, or visible source |
| `source_matched` | edits, restyles, expansions | inherit source grain, flare, sharpness, and surface response; add no new artifact classes |

## Visible Symptom → Positive Correction

| Symptom | Positive target |
| --- | --- |
| random dots or noisy residue | clean low-noise tonal fields; detail grouped into readable forms; texture only where scale and light reveal it |
| floating light spots or decorative sparks | clear air; sparse particles only near a named physical event or practical source |
| uncontrolled bloom or lens flare | smooth highlight rolloff; restrained bloom and flare aligned to visible bright sources |
| waxy or oily skin | natural facial planes; matte skin with soft localized specular highlights; subtle pores only at camera-readable scale |
| uniform plastic materials | separate material classes by roughness, highlight width, reflection, translucency, edge behavior, and contact |
| sharpening halos or crunchy detail | natural microcontrast; selective fine detail on focal surfaces; smooth secondary forms |
| muddy dark scene | readable shadow floor; clean value separation; controlled rim light; low-texture background |
| texture soup | large readable shape groups; one or two high-detail focal zones; secondary props softened by distance, light, focus, or occlusion |

## Material-Light Pass

For every important material, specify only what the camera can read:

```text
base material → surface finish → highlight/reflection behavior → texture scale → edge/contact behavior
```

Examples:

- skin: natural planes, matte base, localized soft specular highlights, subtle pores at portrait scale;
- fabric: visible weave only where close enough, thickness, folds, compression, grazing-light response;
- metal: roughness variation, narrow edge highlights, environment-colored reflections, non-uniform wear;
- glass/water: strict reflection boundaries, refraction, edge visibility, physically limited gloss;
- stone/ceramic: matte porous response, exposed-edge wear only, seam contact shadows, clean broad surfaces.

## Detail Hierarchy

Do not make every surface equally legible. Allocate full clarity to the primary subject and hero materials. Secondary content may lose detail through distance, atmosphere, depth of field, shadow, occlusion, or lower contrast. This produces visual hierarchy and avoids the over-processed AI look.

Replace risky phrases:

| Risky phrase | Prefer |
| --- | --- |
| `ultra detailed` | `balanced detail` |
| `hyper detailed` | `selective fine detail on focal surfaces` |
| `micro detail everywhere` | `detail concentrated on meaningful camera-readable surfaces` |
| `wet glossy` | `strict wet/dry boundaries with roughness-correct reflections` |
| `cinematic bokeh everywhere` | `clean depth separation with restrained, source-motivated bokeh` |
| `beautiful lighting` | `named key direction, controlled bounce, protected highlights` |

## Negative Hygiene

Start with the desired visible state. Add negatives only for broad, likely failure classes that cannot be expressed more clearly as positive targets.

- Keep the avoid block short and current-risk based.
- Do not copy old failed props, colors, styles, characters, or locations into a new negative list.
- Do not repeat the same constraint across many sections.
- Provider support differs: retain exclusions as warnings or prose when no native negative channel exists.

## Retry Strategy

When a generated image already contains widespread noise, ghost texture, uncontrolled light spots, global gloss, or texture buildup, prefer a clean-slate regeneration that locks subject, composition, medium, palette, and essential relationships while rebuilding material and light behavior.

Use image editing when preservation of the original geometry or content is more important than the risk of carrying artifacts forward. For `source_matched` edits, explicitly preserve intentional grain or flare while forbidding new artifact classes outside the edit target.

## Review Checklist

- Each hero material has a distinct physical response.
- Highlights come from named visible sources and retain texture.
- Grain, flare, bloom, particles, gloss, dirt, and wear are intentional.
- Only focal zones receive maximum sharpness and microdetail.
- Dark regions retain shape separation without noisy fill.
- No repeated micro-patterns, hidden text-like marks, decorative speckle, or sharpening halos appear.
- The chosen artifact budget matches the requested medium and source image.
