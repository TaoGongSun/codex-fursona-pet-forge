# Pet Skin Workflow

This is the agent-facing workflow for turning one character reference image into a Codex desktop pet package. Normal users should not need to read this file; the `make-pet-skin` skill reads it and drives the work.

## Modes

### Supervised mode

Use supervised mode when the user wants quality control over each action. After the canonical base is approved, produce and QA one action row at a time. Do not ask the user to approve a raw strip or frame sheet; each row approval must use a transparent 192x208 animated GIF, with a checker or light-background GIF when edge cleanup is uncertain.

### One-shot goal mode

Use one-shot goal mode when the user explicitly uses `/goal` or asks to make the whole pet in one run. Keep the same internal gates, but do not stop for user approval after every row unless a gate fails repeatedly.

One-shot goal mode phases:

1. Preflight.
2. Canonical base and 192x208 preview.
3. Action rows.
4. Row QA and bounded repair.
5. Atlas and package.
6. Final report for user approval.

In goal mode, write compact progress updates and checkpoint artifacts after each phase. If the context becomes too heavy, use `pet-generation-handoff` to produce a copyable continuation block before stopping.

Goal mode must distinguish structural validation from visual acceptance. A row
or package can pass dimensions, alpha, residue, and frame-count checks while
still needing visual repair or human review for source-art clipping, scale
drift, semantic overlap, identity drift, loop pops, or semantic anatomy errors.
Semantic anatomy errors include duplicate tails, extra or missing limbs,
duplicated ears, duplicated horns or wings, ghost accessories, or one-frame
anatomy changes. Keep those statuses separate in the final report.

## Preflight

Before any real image generation:

- Confirm the user supplied, or wants to create, one character reference image.
- Confirm local project image tooling is installed before `/goal` pet production. Recommended setup from the repo root:

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  python3 -m pip install -e .
  ```

- Confirm `Pillow` is available by importing `PIL` in the same Python environment that will run local QA scripts. Pillow is required for deterministic PNG/WebP/GIF reads and writes, transparent-background cleanup, sprite cropping, contact sheets, and pixel-level QA.
- Check whether the `hatch-pet` skill is installed and available.
- If `hatch-pet` is missing, stop before generation and ask the user to install it from `https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet`. For novice users, tell them to ask Codex: "Install the hatch-pet skill from https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet". Tell them that Codex must be restarted after installation before `make-pet-skin` can continue.
- Treat `generate2dsprite` as optional. Mention it only as a possible upgrade for game-sprite-style work; do not block on it.
- Confirm a writable run directory under the repo, usually `.tmp/hatch-pet-<pet-id>`.
- Do not ask personality setup questions unless the user wants the visual design to reflect a specific personality.

## Inputs

Minimum input:

- One character reference image, or a clear text concept when the user has no image.

Useful optional input:

- Pet id.
- Display name.
- Style notes.
- Must-keep silhouette features.
- Must-remove features.
- Whether asymmetrical marks may be mirrored for `running-left`.

## Base Phase

Create a canonical base before any action rows. The base must be readable at pet size, not only as a large illustration.

Deliverables:

- Canonical base image.
- 192x208 preview on a transparent or neutral cell.
- Notes on must-keep and must-remove visual traits.

Do not proceed into action rows if the base has the wrong species, body type, major props, or silhouette landmarks.

## Action Row Order

Default order:

1. `idle`
2. `running-right`
3. `running-left`
4. `waving`
5. `jumping`
6. `failed`
7. `waiting`
8. `running`
9. `review`

Generate `running-right` before `running-left`. Prefer deterministic framewise mirroring for `running-left` unless the character has important asymmetry that cannot be mirrored. Framewise mirroring means mirroring the already-extracted `frames/running-right/00.png` through `frames/running-right/07.png` into 192x208 `frames/running-left/*.png`; do not mirror an arbitrary raw `decoded/running-right.png` strip for accepted package output. If a generated or derived `running-left` is accepted, record whether it was a framewise mirror or an explicitly approved non-mirror row.

## Row Acceptance

For every accepted row, produce:

- Raw selected row path.
- Extracted 192x208 frames path.
- Transparent 192x208 animated GIF.
- Checker or light-background GIF when useful.
- Bbox, bottom, width, height, and green-residue metrics.
- Known rejected variants worth preserving.
- Any suspected source-art clipping, even when the extracted frame bbox has safe margins.
- Any semantic anatomy concerns such as duplicate tails, extra limbs, duplicated ears or horns, missing appendages, ghost props, or anatomy changes that appear in only one frame of a loop.
- Optional zoomed body-part crop contact sheet when the character has important tails, wings, horns, hair, capes, or accessories that are hard to inspect at full contact-sheet scale.
- For derived `running-left`, proof that each left frame equals the framewise mirror of the matching right frame, or an explicit non-mirror approval note.

Do not mark a row accepted from a raw row strip, frames sheet, contact sheet, or numeric metrics alone.

`qa/run-summary.json` should include `human_review_items`, `repaired_rows`, and `manual_frame_repairs` when applicable. Manual frame repairs should record the state, frame id, replacement source, backup path, and reason.

## Repair Policy

In one-shot goal mode, automatically retry when a deterministic gate finds:

- Missing or failed transparent extraction.
- Raw slot boundary contact.
- Cropped body parts.
- Strong identity drift.
- Low-alpha key-color residue.
- Key-like green pixels in transparent or checker GIF previews.
- Magenta gradients or near-key background bands that require raw-row normalization before extraction.
- Suspected source-art clipping at raw strip edges, including tails, robes, wings, hair, capes, or other wide features that appear cut off before extraction.
- Semantic anatomy errors such as duplicate tails, extra or missing limbs, duplicated ears, duplicated horns or wings, ghost props, or one-frame anatomy changes.
- Unsafe `running-left` derivation from a raw strip instead of extracted frames.
- Severe scale drift or unreadable tiny frames.

Use a small retry budget per row. If the row still fails, keep the best failed artifacts, mark the row as needing human review, and continue only if packaging can clearly label the risk.

## Final Package

Final deliverables:

- `pet.json`.
- `spritesheet.webp`.
- Transparent or checker contact sheet.
- Per-row transparent GIF previews.
- Validation report.
- Any rows that need human review.
- `qa/run-summary.json` with `human_review_items`, `repaired_rows`, and `manual_frame_repairs` when those lists are non-empty.
- Semantic frame repairs, including any duplicate-tail or extra-limb fixes, with state, frame id, replacement source, backup path, and reason.

The final package can be structurally valid while still needing visual acceptance or user approval for taste. In the final response, report structural validation status, repaired rows, manual frame repairs, and remaining human review items separately before treating the skin as ready to install or share.
