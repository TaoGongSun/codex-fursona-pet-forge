---
name: make-pet-skin
description: Create, refine, QA, package, or install a Codex desktop pet skin from one character reference image, including /goal one-shot pet generation, supervised per-action refinement, hatch-pet dependency checks, action GIF review, atlas packaging, and final validation.
---

# make-pet-skin

Use this as the single conversational entry point for pet skin creation. Keep the user-facing path simple: one image in, Codex pet package out.

## Reference Docs

When running inside the repo, read only what the current task needs. If these repo docs are not available from the current workspace, continue with the core rules in this skill and ask the user for the repo checkout only when a missing file blocks the run.

- `docs/pet-skin-workflow.md`: overall flow, supervised mode, one-shot goal mode, and hatch-pet preflight.
- `docs/pet-skin-action-defaults.md`: state-specific action defaults.
- `docs/pet-skin-quality-checklist.md`: row and package QA gates.
- `docs/pet-package-spec.md`: current package shape and atlas assumptions.
- `docs/pet-generation-handoff.md`: copyable checkpoint format.

## Preflight

Before generating images or editing package files:

1. Check whether the external `hatch-pet` skill is available.
2. If `hatch-pet` is missing, stop and ask the user to install it before continuing. Tell them: "Install the hatch-pet skill from https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet, then Restart Codex to pick up new skills."
3. Treat `generate2dsprite` as optional. Mention it only as a possible upgrade for sprite-heavy work; do not require it.
4. Confirm local image tooling is installed in the repo Python environment before `/goal` pet production:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python3 -m pip install -e .
   ```

5. Confirm `PIL` imports from that environment. The repo depends on Pillow for deterministic PNG/WebP/GIF processing, transparent cleanup, contact sheets, and pixel-level QA.
6. Confirm the input reference image or text concept.
7. Confirm the run directory, usually under `.tmp/hatch-pet-<pet-id>`.

Do not ask the user a large setup questionnaire. Ask only for missing information that blocks the next step.

## Mode Selection

If the user uses `/goal` or asks for one-click/full automatic creation, use one-shot goal mode. Run all phases with internal checkpoints and bounded repair attempts. Do not require per-row user approval unless quality gates fail repeatedly.

If the user asks to inspect each action, use supervised mode. After base approval, handle one row at a time and ask for user approval from the transparent 192x208 animated GIF.

## Delegation

Use `hatch-pet` for visual generation, deterministic extraction, row QA, atlas composition, and package creation. Do not reimplement its image-generation workflow inside this skill.

Keep long policy text out of image prompts. Use concise row prompts and let the reference docs plus `hatch-pet` own the detailed QA rules.

For directional running, use the repo-local `directional_running_adapter.py` without modifying the installed `hatch-pet` skill. Immediately after `hatch-pet` prepares the run directory, adapt that run before invoking any directional row worker:

```bash
python "<make-pet-skin-skill-dir>/directional_running_adapter.py" prepare-run \
  --run-dir "<run-dir>"
```

This replaces the current run's directional prompts and layout-guide inputs with a three-key-pose contract. For bipeds the poses are left foot forward, legs passing under the body, and right foot forward. Other locomotion types use three equivalent movement phases. Do not generate eight independent running frames.

After the selected three-pose `running-right` image has been copied to `decoded/running-right.png`, expand it before running `hatch-pet` extraction or mirror derivation:

```bash
python "<make-pet-skin-skill-dir>/directional_running_adapter.py" expand \
  --run-dir "<run-dir>" \
  --state running-right
```

The adapter preserves the source under `decoded/key-poses/` and replaces the decoded row with the deterministic eight-frame `12321232` strip expected by `hatch-pet`. If asymmetry requires separately generating `running-left`, expand it with the same command and `--state running-left`. A mirrored left row is derived only after the right row has been expanded.

## Required Gates

Every accepted action row must have:

- selected raw row path
- extracted 192x208 frames path
- transparent 192x208 animated GIF
- checker or light-background GIF when useful
- bbox/bottom/size metrics
- green-residue scan for PNG frames and GIF previews

Do not accept a row from a raw strip, contact sheet, frames sheet, or metrics alone.

For `/goal` runs, treat visual QA as an acceptance gate separate from structural validation. Structural validation status covers dimensions, alpha, frame counts, atlas order, transparent RGB residue, and required files. Visual acceptance covers source-art clipping, row scale relative to `idle`, semantic separation between `waiting`, `running`, and `review`, loop boundary pops, semantic anatomy errors, and whether `running-left` was safely derived.

Run a final semantic anatomy pass before calling a row visually accepted. Check for duplicate tails, extra or missing limbs, duplicated ears, duplicated horns or wings, ghost props or accessories, and anatomy changes that appear in only one frame. When the important body part is small, create or request a zoomed body-part crop contact sheet before accepting the package.

When `running-left` is mirrored, require framewise mirroring from extracted `frames/running-right/*.png` into extracted `frames/running-left/*.png`. Do not accept raw-strip mirroring from `decoded/running-right.png` as package output. If the row is not a mirror, record the explicit non-mirror approval reason.

Require structural proof that directional rows use three key poses, follow `12321232`, and reuse pixel-identical images for repeated pose numbers. A separately generated asymmetric `running-left` follows the same contract.

Require `qa/directional-running-adapter.json` for newly generated directional rows. Do not continue to final packaging if the adapter report is missing or does not report `repeated_poses_pixel_identical: true`.

Record repairs in `qa/run-summary.json` when applicable:

- `human_review_items`
- `repaired_rows`
- `manual_frame_repairs`

Manual frame repairs must include state, frame id, replacement source, backup path, and reason.
Semantic repairs, such as replacing an idle frame with duplicate tails, use the same manual frame repair record.

## Goal Mode Checkpoints

For `/goal` runs, checkpoint after:

1. dependency preflight
2. canonical base
3. first identity rows: `idle` and `running-right`
4. remaining rows
5. final package

If context becomes too heavy, invoke `pet-generation-handoff` and give the user one copyable continuation block.

## Final Response

When the run completes, report:

- package folder
- `pet.json`
- `spritesheet.webp`
- contact sheet
- per-row GIF preview folder
- validation report
- structural validation status
- repaired rows
- manual frame repairs
- semantic anatomy review status
- rows that still need human review

Ask for subjective approval before calling the pet ready to install or share.
