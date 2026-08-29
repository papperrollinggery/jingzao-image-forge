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
- Treats a repeated oily/noisy report as demonstrated risk, chooses `clean_reset`, and does not leave the artifact budget at neutral `auto`.
- Establishes 3–7 low-frequency shape groups, one or two focal-detail clusters, at least one continuous calm surface, and explicit texture ownership before adding microdetail.
- Keeps AO/contact shadows local to real seams, overlaps, creases, and support points; separates glossy/matte and wet/dry regions through material response instead of global sheen.
- Defines positive material and lighting targets before a compact current-risk avoid block.
- Replaces generic `ultra detailed` or `hyper detailed` language with selective, camera-readable detail.
- Prefers clean-slate regeneration for widespread dirty residue unless preserving the original image is a stronger requirement.
- Preserves requested film grain, practical flare, wet gloss, brush texture, or particles when they are intentional and physically or stylistically motivated.
- Reviews both thumbnail hierarchy and 100% surface behavior; a valid prompt or successful tool call cannot override a failed clean-surface gate.
- Freezes passing controls and changes one main variable per retry.
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

## 16. Broad Scenario Routing

Scenario set: a product tabletop, fashion beauty close-up, architecture interior, food still life, scientific field guide, game asset, social campaign, and experimental projection piece.

Pass criteria:

- Selects one primary `scenario_profile` per request instead of treating everything as cinematic key art.
- States the delivery context and audience effect when they change hierarchy, text density, crop safety, or viewing distance.
- Uses at most three spatial `scene_archetypes` and then describes the actual place.
- Applies scenario-specific gates: material/label truth for products, garment/skin hierarchy for fashion, circulation/material junctions for architecture, factual structure for science, and functional readability for interfaces or game assets.

## 17. Coherent Aesthetic Selection

Request: Explore noir, surreal dream, romantic sublime, retro analog, luxury editorial, tactile handcrafted, painterly, animation, documentary, and mixed-media treatments for different briefs.

Pass criteria:

- Chooses one primary `aesthetic_family` based on viewer function rather than stacking adjectives.
- Keeps genre, aesthetic, and capture/render method separate.
- Allows at most one `secondary_influence` and requires a `mix_rule` that assigns it one layer.
- Preserves medium-owned grain, brushwork, seams, misregistration, or handmade marks when intentional.
- Names likely forbidden drift without turning the exclusions into an exhaustive style blacklist.

## 18. Stop-Motion Product and Architecture

Scenario A: a tactile handcrafted tea-tin product still. Scenario B: a wide material-research pavilion in a gallery.

Pass criteria:

- Product route prioritizes silhouette, label truth, contact shadow, paper/metal behavior, and clean negative space.
- Architecture route prioritizes massing, circulation, human scale, daylight path, and material junctions.
- Stop-motion or miniature language produces physical tactility rather than plastic CG or accidental toy scale.
- A shared aesthetic capsule may influence palette and hierarchy without forcing both scenarios into the same composition.

## 19. Learn Style From an Actual Reference

Request: Analyze an attached reference image and save its reusable visual style for later prompts.

Pass criteria:

- Actually inspects the image and uses `learn_style`.
- Separates observed mechanisms, inferred traits, and unknown production details.
- Extracts medium behavior, palette ownership, shape/line, texture/material, lighting, composition, typography, optics/rendering, and limited motifs.
- Does not learn the source face, identity, exact text, logo, signature, protected character design, subject inventory, or exact layout coordinates as style.
- Exports a capsule with `raw_images_stored: false` and explicit transfer/forbidden-transfer rules.

## 20. Style Capsule Transfer and Adoption

Scenario: Apply one learned capsule to a product and an architecture image, then consider adding it to the installed/public Skill.

Pass criteria:

- Compiles the target scenario before the capsule and says the target specification remains authoritative.
- Both images preserve recognizable palette/material/hierarchy mechanisms while using different subjects, ratios, spaces, and production methods.
- Source content does not reappear unless independently requested.
- Requires two visually inspected transfer tests, different-scenario evidence records, and review notes before `validated` or `adopted` status.
- Creates a draft candidate automatically when requested, but does not persist private images or publish/adopt a capsule without user authorization.

## 21. Professional Film Color Pipeline

Request: Create a predawn relationship scene with restrained film texture, cool exterior ambient, one weak amber practical, natural skin, and no generic teal-orange grade.

Pass criteria:

- Separates display/color-science intent from the creative grade.
- Defines exposure strategy, tonal curve, black/white points, highlight rolloff, shadow floor, midtone density, white balance, and color separation.
- Protects skin and hero materials across warm/cool pools.
- Separates negative/reversal character, print/display character, grain, halation, bloom, gate weave, and vignette.
- Grain is exposure- and scale-aware; halation/bloom remain source-motivated.
- Includes shot-matching and continuity locks for a sequence.

## 22. Blender / Unreal / Professional CG Rendering

Scenario A: a path-traced Blender Cycles-style product or fantasy still. Scenario B: a real-time Unreal Engine 5/Lumen-style architecture or game cinematic.

Pass criteria:

- Labels engine names as appearance references unless actual engine execution is in scope.
- Distinguishes offline path tracing, real-time GI/reflections, raster/NPR, and hybrid layered single-image appearance.
- Describes visible diffuse/specular/transmission/volume transport, GI, reflections, shadows, AO, SSS, refraction, caustics, and displacement only when relevant.
- Hero materials define microstructure, roughness, specular width, transmission/subsurface/anisotropy, wear, and contact.
- Sampling/denoise and performance/fidelity rules prevent fireflies, temporal shimmer, over-dark AO, plastic uniform roughness, light leaks, and smeared detail.

## 23. Battle Tension and Beautiful Shot Design

Request: Create a visually beautiful battle frame with readable action, strong foreground/background relation, a dramatic angle, controlled distortion, and no poster pose.

Pass criteria:

- States dominant and secondary reads plus one concrete beauty mechanism.
- Defines action vector, counterforce, frozen phase, motion evidence, and physical consequence.
- Foreground proves viewer position/speed/scale; midground owns action; background proves threat or consequence.
- Couples camera height/distance, pitch/yaw/roll, focal length, lens projection, edge behavior, parallax, and crop pressure.
- Uses one exaggeration budget and one distortion strategy with a realism anchor and readability guard.
- Explicit user tone, capsule, color pipeline, medium, and material hierarchy survive the battle adaptation.

## 24. Same-Model Prompt Quality Benchmark

Scenario: Use one image model to render (A) a one-sentence baseline, (B) a professional local image/cinema Skill prompt, and (C) Jingzao's structured prompt for the same battle or CG-product brief.

Pass criteria:

- Keeps model, subject, aspect ratio, and requested facts constant.
- Scores prompt adherence, action readability, foreground/midground/background depth, camera/distortion, material response, color/film finishing, artifacts, and overall aesthetic hierarchy.
- Does not claim one Skill is superior from prompt length or one lucky image alone.
- Records concrete remaining gaps and changes only reusable mechanisms supported by the visual comparison.
- Re-runs regression and forward tests after any benchmark-driven Skill change.

## 25. Actual Multi-Image Reference Handoff

Request: Use supplied character, wardrobe-mark, product, logo, and scene images to generate a poster or film frame.

Pass criteria:

- Inspects every actual image and records its source, ordinary-language role, and `must_attach` state.
- Compiler output contains an attachment manifest; actual ImageGen tool arguments include every required image.
- Codex-target preflight rejects more than five required images, mixed local/conversation mechanisms, unresolved remote/platform assets, and an unconfirmed recent conversation-image window.
- Every manifest case with `must_attach > 0` has a sanitized receipt matching expected image IDs, order, count, mechanism, hashed tool call, and repository-relative output reference.
- Never replaces an available image with only a prose description.
- Uses the smallest sufficient multi-image set and states what each image contributes without adding a complex policy layer.
- Visually checks character identity, wardrobe mark, product form, logo shape/placement/spelling/color, and scene use after generation.
- If reference fidelity fails, retries or uses the model's own image-edit path; it does not add a post-generation compositing workflow.

## 26. Prompt Normalization and Static Quality Gate

Scenario: Compile the full causal-fantasy, narrative-film, product, and Midjourney fixtures after a schema or compiler change.

Pass criteria:

- Template `Describe...` placeholders and deprecated internal controls never reach prompt prose.
- Compilation does not silently compact explicit source fields. Over-budget output becomes `review_required`; source-spec cleanup must preserve references, exact text, visible events, relationships, actions, camera/viewer geometry, preserve/change invariants, causal owner/contact/cost/response/residue, style authority, tone locks, forbidden drift, motion evidence, readability guard, intentional film behavior, material transport, and NPR constraints.
- `prompt_metrics` are emitted and canonical fixture ceilings do not regress without a reviewed forward test.
- `prompt_review` is `blocked` for context residue outside exact visible copy and cannot be approved through. Length/reference complexity becomes `review_required`; an explicit review may approve it without auto-truncation, and the active style core remains protected.
- A complete color pipeline owns grade/contrast/saturation while `color` remains palette-focused; physical lighting is not deleted.
- Midjourney uses stronger compression and exposes an execution route instead of pretending edit/expand are ordinary imagine prompts.

## 27. Reconstruct / Restyle / Expand Contracts

Scenario A: reconstruct an attached image. Scenario B: restyle one attached image without changing geometry. Scenario C: expand an attached image for a new canvas.

Pass criteria:

- Reconstruct includes a target, directly observed facts, clearly marked inference, and explicit unknowns; it makes no hidden-prompt or software claim.
- Restyle requires non-empty preserve and change lists; only the named treatment changes.
- Expand requires non-empty preserve and change lists; original content, subject relative position/scale, perspective, exposure, and source-boundary continuity remain.
- Each mode has a validated canonical example and a visually reviewed independent forward test before a production-quality claim.

## 28. Creative Validity and Hand-Object Physics

Scenario A: a test author has five unrelated reference roles but no real delivery brief. Scenario B: a real brief requires a person to hold or receive a cylindrical product while moving.

Pass criteria:

- The test does not invent a story, location, interaction, or finished showcase merely to make all five references visible. Attachment delivery is tested as plumbing; creative quality is tested with a separate coherent brief.
- Attachment receipt success is reported separately from creative and visual quality; correct delivery alone cannot produce a public-gallery PASS.
- Delivery context, visible purpose, and viewer conclusion are grounded in the brief or project facts; every admitted reference role supports that purpose.
- Product use or exchange has a plausible action phase and affordance rather than a decorative or unexplained gesture.
- Finger wrap or palm support, wrist alignment, center of mass, load path, counterforce, contact/occlusion, and body balance agree.
- Ambiguous pinching, floating, duplicated, contested, or anatomically impossible hand-object contact fails the visual gate.
- If the premise itself is meaningless, redesign the scenario rather than retrying surface polish.

## 29. Minimal Intervention and Capability Activation

Scenario A: one red ceramic mug on a plain tabletop. Scenario B: a natural window-light portrait. Scenario C: change one object in an attached image. Scenario D: an explicitly path-traced CG material study. Scenario E: an explicitly designed narrative battle frame.

Pass criteria:

- A neutral template emits no aspect ratio, dimensions, subject anchor, camera choice, artifact preset, grain, bloom, flare, gloss, particles, color pipeline, or render pipeline.
- A neutral template is not executable: `empty_prompt` blocks `prompt_review`, prompt lint, and the ImageGen call plan even when Midjourney provider flags exist.
- The mug and portrait compile only brief-grounded core content; “cinematic” alone does not activate a full film, camera, color, or render vocabulary.
- A basic edit compiles the actual reference role, smallest requested change, preserve list, and necessary constraints without unrelated art direction.
- Professional controls activate when explicitly required: CG transport for the material study; event, relationship, staging, camera, action/counterforce, motivated light, and requested finishing for the battle frame.
- Explicit focal length, distortion, film behavior, material response, stylization, and quality controls survive normalization. Minimal intervention never flattens requested style or complex-scene design.
- A failed output is corrected with the smallest cause-specific change; retry history and speculative cleanup phrases do not become defaults.

## 30. Standalone Prompt-Contamination Guard

Scenario A: a GitHub-only Jingzao installation receives a complex retry prompt containing old-scene nouns, negative correction history, a habitual camera template, loaded style labels, and several paraphrases of one effect. `$prompt-contamination-guard` is not installed. Scenario B: a simple clean single-subject prompt needs delivery.

Pass criteria:

- Uses the bundled `references/prompt-hygiene.md`; no external Skill is required and its absence does not block or weaken the audit.
- Applies only the fast gate to the simple prompt and does not expose a backstage trace table or semantic ledger in the paste-ready output.
- For the complex retry, traces suspicious clauses to current sources, classifies old-context, correction/exclusion, default-template, loaded-label, internal-control, conflicting-anchor, and positive-overweighting contamination, then keeps, rewrites, or deletes each clause.
- Builds a semantic ledger only for mechanisms whose ownership is unclear; each geometry, path, lifecycle, result, endpoint, camera behavior, or material response has one authoritative owner.
- Deletes stale nouns instead of explaining them through negation and rewrites loaded labels as current visible evidence.
- Performs a stateless-generator read and preserves every unique current identity, reference role, style, camera, material, continuity, edit, and risk-control decision.
- Treats deterministic compiler/lint checks as a partial static gate, not proof that semantic duplication or template carryover is absent.
- Audit-only output contains findings, collisions, and `PASS` / `FAIL`; cleanup output keeps diagnosis outside one self-contained model-facing prompt.
