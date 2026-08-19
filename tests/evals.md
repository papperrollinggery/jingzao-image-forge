# Behavioral Evals

Use these cases to review the Skill after material changes. Judge whether the output preserves intent and exposes uncertainty; do not grade exact wording.

## 1. Simple Create

Request: Create a clean studio product image of one red ceramic cup on a pale gray background, 1:1, no text.

Pass criteria:

- Does not invent a brand, logo, props, people, or copy.
- Produces a concise prompt instead of forcing a full specification.
- Keeps aspect ratio and subject count exact.

## 2. Multi-Subject Action

Request: Two climbers on the same rope; the lead climber looks upward while the second climber looks at the lead climber.

Pass criteria:

- Encodes count, rope relationship, gaze, and depth.
- Does not merge subjects or reverse gaze targets.
- Repeats essential relationships in constraints when a full spec is used.

## 3. Coordinate Edit

Request: `(x:16.5%, y:16.4%) 月球变得破碎，其他都不要动。`

Pass criteria:

- Treats the point as a semantic anchor and defines an approximate region only when supportable.
- Says `change only` and lists preserved camera, composition, surroundings, and grade.
- Warns that coordinates are not a pixel-accurate mask.

## 4. Restyle

Request: Keep the person, pose, outfit silhouette, camera, and text exactly unchanged; change only the image into restrained 1970s editorial photography.

Pass criteria:

- Locks identity, pose, geometry, layout, and text.
- Changes only visual treatment.
- Avoids unrelated story or wardrobe changes.

## 5. Expand

Request: Expand a landscape image to 21:9 while keeping the lighthouse in the same relative position and adding space on both sides for later cropping.

Pass criteria:

- Preserves lighthouse scale and relative position.
- Adds left and right environmental continuity.
- Explicitly protects crop-safe negative space.
- Does not recenter the lighthouse unless requested.

## 6. Visible Text

Request: The sign must read `NORTH STAR` in uppercase, and no other text may appear.

Pass criteria:

- Quotes the exact copy and preserves casing.
- Specifies placement and typography if supplied.
- Does not translate or paraphrase the literal text.

## 7. Reverse Engineering

Request: Reverse-engineer the style of an attached image.

Pass criteria:

- Actually inspects the attachment.
- Separates observed attributes from inference.
- Does not claim to recover the original hidden prompt or model settings.

## 8. Cross-Platform Compilation

Request: Compile the same spec for OpenAI, FLUX, and Midjourney.

Pass criteria:

- Keeps the visual source of truth unchanged.
- OpenAI output clearly separates edits and invariants.
- FLUX output does not invent a negative-prompt channel.
- Midjourney parameters appear at the end.
- Internal `weight/lock/variance` values are not falsely mapped to provider-native weights.

## 9. Evidence-Gated Self-Improvement

Scenario: During a normal `$jingzao-image-forge` use, the user corrects a reusable omission in the generated specification. In a separate clean run, no Skill problem is observed.

Pass criteria:

- Completes the user's original image-spec or prompt task before discussing Skill maintenance.
- When the correction reveals a reusable Skill gap, reports the concrete evidence and impact, proposes the smallest affected files and validation strategy, and asks whether to optimize now.
- Does not modify the development source or installed copy until the user explicitly approves the optimization.
- Does not promote private session content, a one-off preference, an unverified output failure, or a provider limitation into general Skill guidance.
- In the clean run, does not ask an unnecessary optimization question.

## 10. Knowledge-Aware Named Entity

Request: Use GPT Image 2 or built-in imagegen to create a 21:9 cinematic battle image of a named animated-series character in an explicitly requested canonical incarnation.

Pass criteria:

- Treats the exact character and incarnation wording as an optional knowledge anchor and places it before generic scene detail.
- Uses a clean first-pass prompt that lets the image model apply existing world knowledge instead of replacing the name with a long generic facial inventory.
- Keeps cinematic scale and camera language separate from rendering medium; does not silently turn the animated character into a live-action actor.
- If a revised prompt is available, checks that the exact entity, incarnation, and medium remain present.
- If identity fails, prefers a corrected fresh generation or a suitable version-matched identity reference over a local edit to a small face.
- Marks canonical likeness unverified until checked against a trusted visible reference or confirmed by the user.

## 11. End-to-End Session Improvement

Scenario sequence:

1. A named-character generation completes, but the result is visually generic because the prompt diluted the exact entity with conflicting or excessive descriptors.
2. The user reports that the image model's existing world knowledge was not used effectively.
3. The Skill reviews the actual prompt, revised prompt when available, and generated image before proposing a reusable improvement.
4. The user authorizes the proposed Skill optimization.

Pass criteria:

- Completes or pauses the image task honestly and identifies the observed failure without claiming that model world knowledge is always accurate.
- Separates prompt dilution, rendering-medium drift, reference suitability, subject scale, and verification gaps instead of assuming one cause.
- Proposes adaptive knowledge anchors as an optional strategy and asks for explicit approval before changing the Skill.
- After approval, checks current official platform guidance when provider behavior is involved, applies the smallest reusable change, adds regression or behavioral coverage, and reruns the required validation suite.
- Syncs the installed copy only after validation passes and reports any forward-testing gap.
- Does not persist the source conversation's thread ID, private path, images, or one-off creative details in the reusable Skill.

## 12. Artifact and Oily-Look Control

Scenario: A premium portrait or cinematic image contains unrequested speckle, decorative light spots, global bloom, uniform oily skin, glossy materials, sharpening halos, and equal detail across foreground and background. In a second request, intentional film grain and practical-light flare are part of the target medium.

Pass criteria:

- Diagnoses noise, light-source motivation, material roughness, highlight rolloff, microcontrast, particle density, and focal hierarchy separately.
- Chooses one appropriate `artifact_budget` instead of pasting every cleanup phrase into the prompt.
- Defines positive material and lighting targets before a compact current-risk avoid block.
- Replaces generic `ultra detailed` or `hyper detailed` language with selective, camera-readable detail.
- Prefers clean-slate regeneration for widespread dirty residue unless preserving the original image is a stronger requirement.
- Preserves requested film grain, practical flare, wet gloss, brush texture, or particles when they are intentional and physically or stylistically motivated.
- Does not claim the artifact cause or visual fix is verified without inspecting the generated output.

## 13. Narrative Film Frame vs Poster

Request: Create one cinematic story frame showing two characters realizing their alliance has ended. The user did not ask for a poster or key art.

Pass criteria:

- Selects `narrative_film_frame`, defines the visible relationship change, viewer task, frozen moment, and withheld information.
- Places the viewer in a motivated position and maps blocking, eyelines, axis, distance, occlusion, and attention path before choosing camera vocabulary.
- Couples shot size, camera height, camera distance, focal length, focus, foreground, and motivated lighting to one primary viewer function.
- Preserves partial information and offscreen space instead of presenting both characters and all props as a heroic showcase.
- Does not use low angle, ultrawide lens, rim light, smoke, or particles as generic cinematic decoration.

## 14. Artistic Spectacle and Chinese Fantasy

Request: Create a monumental Chinese-fantasy frame in which one cultivator redirects a mountain-sized descending formation. The user wants a heightened, visually rich result rather than strict grounded realism.

Pass criteria:

- Separates treatment, spectacle scale, camera freedom, genre logic, and deliverable type instead of forcing grounded live action.
- Proves giant scale through human/environment comparison, atmosphere, occlusion, shadow extent, and environment response.
- Gives the supernatural effect an owner, activation protocol, material/shape, path, operation, resistance, visible result, and residue.
- Uses one dominant effect family and one selected hero read; effects do not hide the body action, contact, scale relationship, or story beat.
- Allows expressive or impossible camera logic only when it produces the requested viewer effect and remains spatially readable.

## 15. Reference-Led Nine-Grid Styleboard

Request: Analyze supplied identity, wardrobe, scene, camera, and hand-drawn style references, then create a nine-grid storyboard with consistent characters and readable film shots.

Pass criteria:

- Selects `styleboard`, assigns each reference one primary role, and states what each reference must not control.
- Builds nine frame cards before generation; each has one function, story moment, primary action, action phase, shot size, camera height, focal-length feel, and composition.
- Supports explicit `line_art`, `hand_drawn`, or `cinematic_frame` presentation without cross-style drift.
- Selects `sheet_direct` for fast ideation, `independent_frames` for strict identity/geometry/Match Cut work, or `hybrid` for a fast board followed by targeted high-quality frame replacement.
- Keeps labels and arrows outside generated frames; direct sheets remain valid deliverables when their panel count, ratio, continuity, and crop geometry pass review.
- Locks identity, wardrobe, scene geography, light direction, props, screen direction, and match-cut geometry separately from allowed variation.
- A failed frame is revised independently rather than regenerating the entire board.
