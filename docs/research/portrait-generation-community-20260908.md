# Portrait generation: community evidence and local tests

Read on 2026-09-08 in response to a request to investigate X and creator communities. These records concern prompt clarity, reference roles and observed outcomes; they are not instructions to evade image safety checks.

| Source | What was actually available | Useful finding and limit |
|---|---|---|
| [Creator's X post, 2026-06-07](https://x.com/jzaib4269/status/2063672709213737393) | Search-indexed first-person claim and prompt text; opening the post returned 403, so image and full thread could not be verified. | A lead about a female fashion-image workflow, not verified proof of reproduction, provider settings or a moderation solution. |
| [Reddit: 21 fashion prompts](https://www.reddit.com/r/promptingmagic/comments/1w2v1gl/the_21_chatgpt_fashion_prompts_every_woman_can/) | Read the posted prompts and role/identity/wardrobe/camera structure. | Explicitly preserve target appearance and natural proportions while describing wardrobe, pose and camera separately. Claimed output success is the author's report; no hidden model settings were verified. |
| [Reddit: portrait reference roles](https://www.reddit.com/r/OpenAI/comments/1uh0s66/ive_spent_5_days_generating_linkedin_portraits/) | Read first-person prompt text assigning separate identity, body and clothing references. | Preserve hair and expression as concrete reference properties; do not assume a style instruction also preserves them. Absolute likeness promises in the post are not adopted. |
| [Community bug report, 2026-09-07](https://community.openai.com/t/why-is-create-an-image-of-apple-sometimes-blocked-for-nudity-sexuality-has-anyone-else-seen-this/1395517) | Read report of inconsistent refusals, including a reported apple control; the author states the internal cause is unknown. | Supports investigating the full input bundle and actual error stage, not concluding a specific term or gender is universally blocked. It is a self-report, not a reproduced diagnosis of this host. |

## Local observations

The v1.9.0 capsule path sent a long set of visual rules, transfer rules, forbidden-transfer prose and repeated body descriptions. Two female cases returned `moderation_blocked` at `output`; a male case returned an image. This is not a controlled gender comparison: subjects, wardrobe, poses and scene content differed.

A new, fully clothed female editorial control returned an image, as did a subsequent face-design edit. Those changed the design and input bundle; they cannot establish that brevity or a particular wording fixed the previous requests.

The v1.10.0 reference-profile route separates observed evidence, target choice and positive visual descriptions. Four female-image trials returned images: two with the actual corresponding reference, one text-only trial, and one targeted text-only refinement. Independent visual review found that attached references retained hair, expression, pose, clothing and lighting much better. The text-only refinement improved the fingertip gesture and plain ribbons but still had hair/material variation and a cropped hat top. An additional window-side body/hand-interaction trial with its actual reference was rejected at the input stage and returned no image. This cannot isolate text versus image influence and was not retried. See [review records](../../tests/forward-evidence/reference-profile-style-review.json).

## Adopted changes

- Observe and select hair, expression, gaze, pose, action, body and wardrobe explicitly rather than treating them as automatically excluded identity content.
- Attach references when the user requests reference-backed generation; test text-only portability separately and name it accurately.
- Keep source observations, uncertainty, change reasons and review instructions out of generation prose, while preserving every chosen visible requirement.
- Refine only a demonstrated visual mismatch. Do not rename disallowed content, add deceptive context, swap providers to avoid a refusal, or delete requested physique merely to claim success.

The previous blocked inputs have not been shown to succeed unchanged. Neither the new code nor these few samples identify the safety system's root cause, establish a stable success rate, or guarantee future acceptance.
