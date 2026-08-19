# Same-Model Prompt Quality Benchmark — 2026-08-19

This is a controlled qualitative forward test, not a statistical model evaluation. All variants used the same built-in ImageGen in one session. Subject facts and requested ratios were held constant; only prompt strategy changed.

Outputs are intentionally stored under ignored `output/benchmark/` and are not part of the public Skill package.

## Rubric

Each dimension is visually reviewed from 1–10:

1. factual and constraint adherence;
2. dominant-read/action or product hierarchy;
3. foreground-midground-background depth;
4. camera/composition/distortion control;
5. material and light response;
6. color, tone, and film/digital finishing;
7. artifact and unwanted-content control;
8. distinctive aesthetic result.

Scores summarize this one generation set and should not be generalized to every seed or model update.

## Battle Frame

Brief: one grounded Chinese-fantasy cultivator redirects one mountain-sized descending circular formation above a flooded mountain sanctuary.

| Prompt strategy | Facts | Read | Depth | Camera | Material | Color | Control | Aesthetic | Total / 80 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Simple one-sentence prompt | 4 | 6 | 8 | 7 | 6 | 5 | 4 | 8 | 48 |
| Cinema DNA professional film prompt | 8 | 8 | 8 | 8 | 8 | 8 | 9 | 8 | 65 |
| Jingzao structured prompt | 9 | 9 | 9 | 9 | 8 | 8 | 8 | 9 | 69 |

Observed:

- Simple prompt produced the largest immediate spectacle but drifted into game-poster grammar: many flying figures, decorative lightning, global detail, and a weaker one-owner causal event.
- Cinema DNA produced the strongest grounded live-action still, body/ground contact, natural dark tone, and film restraint, but the supernatural operation and multi-layer consequence were less explicit.
- Jingzao best preserved one subject, action/counterforce, readable depth, formation scale, contact path, and environment response while retaining restrained color. Its remaining risk is length: a model may selectively ignore lower-priority micro-rules.

## Product Frame

Brief: one matte-ivory jasmine-tea tin with a blank deep-green label in a tactile folded-paper garden, square, no people, no logo, no new text.

| Prompt strategy | Facts | Read | Depth | Camera | Material | Color | Control | Aesthetic | Total / 80 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Simple one-sentence prompt | 6 | 8 | 8 | 8 | 8 | 8 | 6 | 8 | 60 |
| GPT-Image professional product prompt | 9 | 9 | 8 | 9 | 8 | 7 | 10 | 8 | 68 |
| Jingzao initial structured prompt | 6 | 9 | 9 | 9 | 9 | 9 | 6 | 9 | 66 |
| Jingzao targeted no-text retry | 10 | 9 | 9 | 9 | 9 | 9 | 10 | 9 | 74 |

Observed:

- Simple prompt was attractive but invented readable packaging copy and mixed literal plant imagery with paper craft.
- GPT-Image craft prompt was the cleanest initial product result and best suppressed fake copy, with disciplined spacing and undistorted geometry; its material/color identity was intentionally conservative.
- Jingzao initial result had the strongest material, color, and depth signature but invented Chinese/English label text because the target label was not explicitly blank.
- The smallest supported correction—declare a blank label with no lettering and exclude `new text`—removed the copy while preserving the same product, paper, copper, color, and render identity. No new policy layer was added.

## Reusable Conclusions

- Simple prompts can produce excellent isolated images; Jingzao should not force full specifications on low-risk requests.
- Cinema DNA remains a strong restraint benchmark for live-action film texture and incomplete narrative moments.
- GPT-Image's product craft is a strong benchmark for concise structure and text suppression.
- Jingzao's difference is the combined control of scenario, tone authority, spatial dynamics, causal effects, professional color, render/material behavior, style learning, actual reference delivery, validation, and multi-platform compilation.
- More fields are not automatically better. Prompt sections must remain conditional, scenario-relevant, and ordered by visual priority.
- Benchmark-driven changes require visual evidence and regression coverage; one lucky image does not justify a universal rule.
