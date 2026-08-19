# Built-in Style Capsules

Use these capsules only when the user explicitly asks for the named treatment or when a supplied reference has been inspected and the user approves the match. A capsule transfers visual mechanisms; it never substitutes for the target subject, scene, exact text, identity, product, logo, or attached reference image.

## Graphite Copper Editorial

- File: `../examples/style-capsule-graphite-copper.json`
- Status: validated example
- Best for: restrained product, architecture, exhibition, editorial, and tactile material studies
- Core transfer: graphite-black field, warm copper ownership, disciplined negative space, clean shadow structure, and selective material detail
- Evidence: forward-tested on a square tactile tea product and a wide architecture pavilion

## Crimson Nocturne Wuxia Print Montage / 绯夜武侠胶片拼贴

- File: `style-capsules/crimson-nocturne-wuxia-montage.json`
- Status: adopted
- Best for: vertical character portraits, martial-arts or period-fantasy mood pieces, album or editorial imagery, memory/danger double exposure, and any brief that benefits from a dominant face plus a miniature narrative layer
- Core transfer: deep-black negative field, crimson dominant portrait, cyan secondary story layer, amber skin bridge, asymmetrical crop pressure, controlled double exposure, uneven analog print grain, restrained scratches/light leaks, soft highlight shoulder, and sparse user-supplied vertical copy
- Do not transfer: source faces, costume, jewelry, weapons, landscape, wording, signature, watermark, or exact layer coordinates
- Evidence: derived from three user-supplied references without storing the raw images; forward-tested on an unrelated contemporary jazz singer and an unrelated desert science-fiction courier. Both tests retained the hierarchy, palette ownership, print behavior, and double-exposure logic while changing subject and world. Results were visually inspected on 2026-08-19; they do not guarantee exact repeatability.

## Use

Validate before applying:

```bash
python3 scripts/validate_style_capsule.py references/style-capsules/crimson-nocturne-wuxia-montage.json
```

Apply to a target specification:

```bash
python3 scripts/compile_prompt.py path/to/target-spec.json \
  --style-capsule references/style-capsules/crimson-nocturne-wuxia-montage.json \
  --platform openai
```

The target specification remains authoritative. If the user also supplies a face, wardrobe, product, logo, prop, or scene reference, the actual image must still be attached through the normal reference-delivery path.
