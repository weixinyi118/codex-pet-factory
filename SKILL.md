---
name: codex-pet-factory
description: Build, resume, repair, validate, and install Codex v2 desktop pets efficiently from one or many reference images. Use for repeated custom-pet production, large multi-image jobs, 413 request failures, interrupted hatch-pet runs, identity or color drift across animation rows, or any workflow that needs disk-first checkpoints, compact reference packs, provider preflight, adaptive QA, and an 8x11 spriteVersionNumber 2 package.
---

# Codex Pet Factory

## Objective

Deliver a valid Codex v2 pet without redoing completed work or placing large images in the conversation history. Keep every durable input, generated row, QA result, and checkpoint inside one project run directory.

Treat `1536x2288`, `8x11`, `192x208` cells, and `spriteVersionNumber: 2` as the final contract. Treat the `8x9` atlas as intermediate-only.

## Choose A Route

1. Search the current workspace for `pet-factory.json`, `pet_request.json`, `hatch_pet_handoff.json`, and existing `hatch-run` directories.
2. Resume the newest valid run when the user wants to continue or repair. Never regenerate rows that already pass deterministic and visual QA.
3. Start a fresh run only when no usable run exists or the user explicitly requests a new pet.
4. Use `fast` mode by default. Use `strict` mode only for a high-stakes public or brand deliverable, or when the user asks.

Read [pipeline.md](references/pipeline.md) for the complete stage contract. Read [provider-routing.md](references/provider-routing.md) before any external image-provider fallback. Read [qa-policy.md](references/qa-policy.md) before accepting or repairing generated rows.

## Resolve The Runtime

Do not assume `python` is on `PATH`. Resolve it through the app's bundled workspace dependencies first. On the standard Windows desktop install, also check:

```powershell
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" }
if (-not (Test-Path -LiteralPath $python)) { throw "Python runtime not found" }
```

## Start Or Resume A Run

Run preflight before image generation:

```powershell
& $python "<skill-dir>/scripts/preflight.py" --json-out <run-dir>/qa/preflight.json
```

Pack reference images before attaching them to any generation request:

```powershell
& $python "<skill-dir>/scripts/reference_pack.py" --output-dir <run-dir>/inputs/reference-pack <image> [<image> ...]
```

Initialize a durable run manifest:

```powershell
& $python "<skill-dir>/scripts/pet_run.py" init --run-dir <run-dir> --pet-id <id> --display-name <name> --mode fast --reference-manifest <run-dir>/inputs/reference-pack/reference-manifest.json
```

For an existing run, inspect before acting:

```powershell
& $python "<skill-dir>/scripts/pet_run.py" discover --root <workspace>
& $python "<skill-dir>/scripts/pet_run.py" status --run-dir <run-dir>
```

Write a checkpoint after each expensive or user-approved stage. Record local file paths, never base64 image data:

```powershell
& $python "<skill-dir>/scripts/pet_run.py" checkpoint --run-dir <run-dir> --stage base --status passed --artifact canonical_base=<absolute-path>
```

## Production Rules

- Keep the conversation text-only for production assets. Use local absolute paths when passing images to tools or workers.
- Keep the packed reference set under 5 MiB by default. Upload only the images required for the current row.
- Run a one-image provider smoke test before launching multiple generation jobs.
- Lock one canonical base before generating animation rows. Require it to read clearly at `192x208`.
- Generate independent standard rows in parallel when capacity permits. Generate `running-right` before deciding whether `running-left` can be mirrored.
- Approve up/right/down/left cardinal anchors before generating rows 9 and 10. Use screen coordinates: right means image/screen right.
- Generate each look row as one coherent eight-pose strip. Never patch a single look cell into the final atlas.
- Make row 10 depend on the approved row 9 so identity, source scale, lighting, and the `157.5 -> 180` boundary remain continuous.
- Specify a numeric source subject-height band for look rows. Reject a row before assembly when its median height differs from its paired row by more than 12%.
- Preserve every selected source and every rejected candidate with a short rejection note. Do not overwrite evidence.

Use `$imagegen` for normal visual generation. If its built-in route is unavailable, follow [provider-routing.md](references/provider-routing.md), ask once for any required fallback authorization, and keep provider calls out of the conversation payload.

## Deterministic Assembly

Reuse the installed `$hatch-pet` scripts for frame extraction, atlas assembly, despill, previews, contact sheets, direction sheets, continuity measurement, and v2 validation. Do not load or restate the entire `hatch-pet` instruction body when the required contract is already captured here.

Require these final files:

- `final/spritesheet-extended.webp`
- `final/validation-extended.json`
- `qa/contact-sheet-extended.png`
- `qa/look-directions.png`
- `qa/review.json`
- `qa/direction-semantics.json`
- `qa/row-consistency.json`

Run color, brightness, identity-scale, and paired-look-row checks before final visual QA:

```powershell
& $python "<skill-dir>/scripts/qa_row_consistency.py" --atlas <run-dir>/final/spritesheet-extended.webp --json-out <run-dir>/qa/row-consistency.json
```

## Adaptive QA

In `fast` mode:

1. Run all deterministic geometry, transparency, frame-count, and package checks.
2. Run `qa_row_consistency.py`.
3. Use one independent visual reviewer for the complete contact sheet, row previews, and all 16 labeled directions.
4. Run one blind cardinal review.
5. Escalate to three isolated blind reviewers only when a cardinal is wrong or ambiguous, an intermediate direction is disputed, or the independent reviewer reports identity/continuity uncertainty.

In `strict` mode, run three isolated blind reviewers unconditionally.

Repair the smallest packaging-eligible scope: one standard row or one complete coherent look row. After repair, rerun only the affected extraction checks plus final assembly, consistency, and visual QA. Do not rerun unrelated generation.

## Installation Gate

Install only when:

- v2 validation passes with no structural errors;
- rows 0-8 have correct semantics and no detached effects;
- rows 9-10 match each other and the canonical identity in palette, lighting, material, and scale;
- all four cardinals are unmistakable;
- any accepted intermediate warning is recorded;
- `pet.json` is UTF-8 and contains `spriteVersionNumber: 2`.

Copy only `pet.json` and `spritesheet.webp` into `${CODEX_HOME}/pets/<pet-id>/`. Keep the complete run directory in the project for future repair and reuse.

## Completion Report

Report the run directory, installed directory, validation result, accepted warnings, provider route used, and rows regenerated. State whether the app needs a restart to discover the new files. Never claim a settings menu or pet selector exists unless verified for the installed Codex version.
