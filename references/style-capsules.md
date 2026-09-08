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

## 长生·华构人间 / Inhabited Chinese Fantasy

- File: `style-capsules/changsheng-inhabited-fantasy.json`
- Read [scene and costume guidance](changsheng-style.md) when the user names 《继承者大会初试：何为长生？》 or its style.
- Core: inhabited architectural depth and character-led wardrobe decisions; plain, pale, colorful, rich, tailored or fluid outfits retain differentiated material and construction quality. Read [the revised wardrobe system](changsheng-wardrobe-system.md).
- Source: costume-focused resurvey of 149 original-resolution samples and 31 native-frame close inspections from one film; raw frames are not distributed.
- Validation and adoption status: see the capsule and `tests/forward-evidence/changsheng-wardrobe-v2-review.json`. Prior v1.7.0 execution inputs are frozen in a test fixture.

## 晴海·角色写真 / Azure Summer Character Photography

- File: `style-capsules/azure-summer-character-photography.json`
- Read [lighting branches, format adaptation and mixed-style ownership](azure-summer-style.md).
- Core: airy blue/ivory daylight, warm readable skin, physical styled hair and layered fabrics, soft near-depth framing and event-grounded camera relationships. Shade and warm sunset are explicit branches.
- Derived from eight inspected user references without storing source pixels or copying identities, emblems, costume designs or text.
- Evidence status: see capsule and `tests/forward-evidence/azure-summer-style-review.json`; generated pixels remain local-only.

## 柔映·人物质感 / Soft Editorial Character

- File: `style-capsules/soft-editorial-character.json`
- Read [three branches and body-profile observations](soft-editorial-style.md).
- Shared core: soft modeled skin, selective eye/lip detail, coherent hair strands, tactile garment layers, close portrait relationships and target-owned body volume. Select daylight, cream-rose couture or crimson-black couture in the target specification.
- Status of the generic capsule: user-authorized inclusion as **draft**, partially verified. Its original male portrait has deviations and two female tests were output-blocked. [Capsule evidence](../tests/forward-evidence/soft-editorial-style-review.json). For selected hair/expression/pose/body/wardrobe fidelity use the newer reference profiles in the style guide: four subsequent female-profile calls returned images, with attached and text-only outcomes reported separately in [profile evidence](../tests/forward-evidence/reference-profile-style-review.json). These calls do not validate the older capsule or prove a moderation fix. Raw sources remain private; one refined text-only sample is publicly available.

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
