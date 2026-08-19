# Prompt Hygiene Without Style Flattening

Use this before sending a complex compiled prompt to an image model, especially when `prompt_review.status` is `review_required`, four or more references are required, several sections paraphrase one action, or a correction keeps reintroducing old failures.

The maintained `visual_generation_spec` is lossless design memory. The model-facing prompt is a scene-specific projection, not a dump of every field.

## 1. Establish Current Truth

Trace each model-facing fact to one current source:

- user brief or approved project fact;
- actual reference and its assigned role;
- required identity, product, text, continuity, edit, or mode contract;
- current style, palette, medium, camera, material, or effect decision.

Remove invented test scenes, habitual templates, old attempts, and source-image nouns named only to reject them. Do not create a story, location, or interaction merely to make every attachment visible.

## 2. Build One Causal Spine

For the current image, write one compact governing structure:

```text
delivery purpose -> viewer conclusion -> visible event or product promise ->
subject/action/contact -> camera proof -> style and material system -> output constraints
```

For a single narrative/action frame, this is one primary causal/read spine. For a styleboard, apply it per panel plus board progression. For key art or montage, use one focal hierarchy; for an infographic, one information argument; for experimental work, one governing transformation rule. Secondary reads may exist but must not compete with the primary structure. If the brief cannot support the relevant structure, resolve the premise or split the deliverables before adding detail.

For hand-object or body-object action, the event owner states only the necessary mechanics: action phase, grip/support surface, load path, counterforce, body balance, and readable contact. Do not repeat the same exchange in intent, subject, staging, dynamics, composition, and exclusions.

## 3. Give Each Fact One Owner

Use one authoritative location per semantic fact:

| Fact | Owner |
| --- | --- |
| purpose, visible event, frozen phase | intent / cinematic contract |
| identity, appearance, unique action contribution | subject |
| positions, eyelines, axis, occlusion | staging |
| force, counterforce, layer roles, distortion | spatial dynamics |
| viewer position, camera, lens, crop | composition |
| physical sources and direction | lighting |
| palette, tone, film behavior | color pipeline |
| medium, aesthetic, transferable surface behavior | style / style capsule |
| roughness, transmission, wear, contact deformation | materials |
| exact required and forbidden output facts | constraints |

A short mechanism name may recur as a handle. Its geometry, lifecycle, grip, path, result, camera behavior, or material response should not be paraphrased across sections. Hard invariants may receive one explicit enforcement echo at the final boundary—`Change only`, `Preserve`, or `Exact visible text`—without being treated as contamination.

## 4. Protect the Style Core

Prompt cleanup must not impose universal realism or flatten expressive work. Preserve the current:

- medium and primary aesthetic;
- style authority and tone locks;
- palette ownership and color separation;
- silhouette/shape/line language;
- hero material and light behavior;
- camera/lens relationship and declared exaggeration budget;
- intentional grain, halation, print defects, brushwork, distortion, or impossible space.

Interaction truth is style-relative. Product photography needs plausible support and anatomy. Animation may exaggerate anatomy and timing. Surreal or graphic work may violate physics deliberately. In every case the choice must be intentional, coherent with the medium, and readable—not an accidental compromise between competing clauses. For product-use imagery, name the functional state and the visible fact that proves correct use: open/closed, worn/held, active/inactive, oriented control surface, supported handle, or completed transfer.

## 5. Remove Contamination, Not Detail

Delete or rewrite:

- old-context nouns kept alive by `no`, `not`, `avoid`, `不要`, or `别`;
- default locations, props, poses, colors, camera moves, or endings not requested now;
- loaded labels that replace visible evidence;
- internal workflow notes, reference IDs without roles, and correction history;
- mutually incompatible camera, medium, action, or visibility requirements;
- positive synonyms that accidentally overweight one effect, pose, object, or contact.

Keep every unique current design choice. Character count alone is not a reason to remove identity, style, material, camera, continuity, or risk-control facts.

Literal user-required copy is exempt from conversation-residue matching when it appears in `Exact visible text`. The same wording outside that protected literal block remains contamination. Do not let a regex intended for backstage phrases reject a poster, chat UI, or version-history graphic that must visibly contain words such as “上一版” or “继续保持”.

## 6. Feasibility and Visibility Budget

One image should have one primary viewer conclusion and a small number of mandatory reads. If a prompt requires a moving body, exact identity, precise hand interaction, full product truth, multiple references, complex architecture, deep focus, and simultaneous style proof, decide what may become secondary or split the test.

Reference-delivery tests prove attachment mechanics. Creative forward tests begin with a coherent use case and only then choose necessary references. Never turn maximum reference count into a composition goal.

## 7. Gate

PASS only when:

- every clause has a current source and one unique job;
- the causal spine is clear without reference to conversation history;
- no fact is semantically overweighted through repetition;
- action/contact instructions agree with the frozen phase;
- style core and intentional exaggeration remain intact;
- reference roles support the brief instead of defining it;
- prompt length or density has been reviewed when the compiler marks `review_required`.

Execution remains blocked until this gate is consumed. `blocked` contamination must be rewritten and recompiled. Length/reference-only `review_required` may be explicitly approved after the audit; approval never overrides residue.

If `$prompt-contamination-guard` is installed, use its source-trace, semantic-ledger, deletion-test, and stateless-generator read as the audit workflow. Its output cleans the prompt; it does not own or redesign the creative facts.
