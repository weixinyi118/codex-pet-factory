# Pipeline Contract

## Stages

1. `intake`: lock the pet ID, name, identity, style, and output directory.
2. `preflight`: locate Codex, `hatch-pet`, Python/Pillow, provider configuration, and the pets directory.
3. `references`: create a compact local reference pack and manifest.
4. `base`: approve one canonical base at full view and `192x208` preview size.
5. `standard-rows`: produce and validate rows 0-8.
6. `cardinals`: approve up, screen-right, down, and screen-left anchors.
7. `look-row-9`: produce `000` through `157.5` as one strip.
8. `look-row-10`: produce `180` through `337.5` as one strip using approved row 9 as continuity evidence.
9. `assembly`: build the 8x11 atlas, apply one deterministic despill pass, and validate v2 geometry.
10. `qa`: run consistency, previews, semantic direction review, and adaptive blind review.
11. `package`: write UTF-8 `pet.json` and stage the WebP.
12. `installed`: copy the two package files to the Codex pets directory and verify hashes.

## Resume Rules

- Trust a stage only when its checkpoint is `passed` and each recorded artifact still exists.
- Downgrade a stale checkpoint to `in_progress`; do not delete its artifacts.
- Prefer a valid rejected candidate over a new provider call when the rejection reason no longer applies.
- Preserve sources under `generated/`; preserve normalized row files under `decoded/`; preserve all evidence under `qa/`.
- When a conversation is interrupted, a new task must be able to resume from `pet-factory.json` plus local files alone.

## Standard Row Contract

| Row | State | Frames |
| ---: | --- | ---: |
| 0 | idle | 6 |
| 1 | running-right | 8 |
| 2 | running-left | 8 |
| 3 | waving | 4 |
| 4 | jumping | 5 |
| 5 | failed | 8 |
| 6 | waiting | 6 |
| 7 | running | 6 |
| 8 | review | 6 |
| 9 | look directions A | 8 |
| 10 | look directions B | 8 |

Rows 0-8 must not contain detached smoke, glows, trails, dust, guide marks, text, or scene fragments. Row 7 means active task work, not literal foot-running.

## Look Direction Contract

- Row 9: `000, 022.5, 045, 067.5, 090, 112.5, 135, 157.5`.
- Row 10: `180, 202.5, 225, 247.5, 270, 292.5, 315, 337.5`.
- `000` means up; `090` screen-right; `180` down; `270` screen-left.
- Preserve a coherent clockwise loop and a stable foot/bottom baseline.
- Reject whole-sprite tilting used to fake gaze unless the character is literally a rotating object.

## Fast-Path Scheduling

- Launch independent rows 0, 1, 3, 4, 5, 6, 7, and 8 concurrently when safe.
- Derive row 2 from row 1 only if props, hair, text, and asymmetric markings remain correct.
- Start cardinals alongside standard rows after canonical-base approval.
- Do not start row 9 until cardinals pass.
- Do not start row 10 until row 9 passes extraction, edge, direction, and source-scale checks.
- Start contact-sheet and palette QA as soon as all row files exist; do not wait for packaging.
