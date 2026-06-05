# Pet Skin Quality Checklist

Use this checklist before accepting a row or final package. The `make-pet-skin` skill should turn these into concrete tool checks whenever possible.

## Base Checks

- The character reads correctly at 192x208.
- Must-keep silhouette landmarks are visible.
- Must-remove traits are absent.
- The image can be separated from its background.
- The base is suitable as the canonical identity reference for every row.

## Raw Row Checks

- The row uses the expected frame count.
- Every frame has clear chroma-key space around the subject.
- Raw slot overlay shows no subject bbox touching slot boundaries.
- Raw strip edges show no source-art clipping; tails, robes, wings, hair, capes, gauntlets, weapons, and other wide features must not look truncated before extraction.
- Neighboring frames do not overlap or share detached fragments.
- Near-key magenta gradients, lighting bands, or uneven chroma-key backgrounds are normalized before extraction instead of accepted as prompt quirks.
- The pet is not over-shrunk so far that extracted frames become unreadable.
- Wide features such as tails, capes, hair, wings, gauntlets, and weapons stay inside the slot.

## Extraction Checks

- Extracted frames are 192x208.
- The transparent 192x208 animated GIF exists before user approval.
- A checker or light-background GIF exists when edge artifacts are possible.
- Alpha bbox wraps the pet, not the whole frame.
- Important body parts are not cropped.
- Bottom anchor, face anchor, or chosen perceptual anchor is stable enough for the row.
- Crouch, bow, raised-arm, and hover poses keep character proportion instead of being scaled to fill the cell.
- Crouch, bow, slump, and hover poses keep the head, face, ears, muzzle, and mane visually consistent with `idle`.

## Transparency Checks

- Fully transparent pixels do not retain hidden key-color residue.
- Visible key-color residue is 0 or explicitly repaired before acceptance.
- Low-alpha key-color residue is 0 in source PNG frames before GIF export.
- Transparent and checker GIF scans report 0 key-like green pixels.
- Edge cleanup changes alpha only; it must not crop, resize, or move frames.

## Animation Checks

- The loop reads as the intended action.
- The final frame returns cleanly to the first frame or to idle.
- The pet does not flicker, float, grow, shrink, or change identity between frames.
- Run a semantic anatomy pass across every frame: reject duplicate tails, extra or missing limbs, duplicated ears, duplicated horns or wings, ghost props, ghost accessories, or anatomy changes that appear in only one frame.
- Use a zoomed body-part crop contact sheet when tails, wings, horns, hair, capes, weapons, or signature accessories are too small to inspect reliably in the full contact sheet.
- `idle` is neither nearly static nor over-animated.
- `idle` must not hide a one-frame semantic anatomy artifact such as duplicate tails or an extra appendage just because the motion is subtle.
- `running-left` and `running-right` preserve identity and cadence.
- A derived `running-left` uses framewise mirror output from extracted `running-right` frames, or has an explicit non-mirror approval note.
- A framewise mirror derivation proves every `running-left` frame equals the horizontal mirror of the matching `running-right` frame.
- `jumping` reads as hover attention unless the user requested a literal jump.
- `jumping` does not solve slot spacing by making the head or face smaller than `idle`.
- `failed` reads as failure through facial acting and posture, not merely crouching.
- `failed` preserves identity while frames 2-5 show closed or nearly closed eyes, lowered ears, bowed head, and disappointment.
- `running` reads as active work rather than directional locomotion.
- `review` is distinct from `waiting`.

## Final Package Checks

- Package contains `pet.json`.
- Package contains `spritesheet.webp`.
- Spritesheet dimensions match the current package spec.
- Final WebP encoding preserves transparent RGB cleanup, for example by using an exact/preserve-transparent-RGB encoder option when available.
- Atlas rows match the expected action order.
- Unused cells are transparent.
- Contact sheet and per-row GIF previews exist.
- Validation report records warnings and failed or risky rows.
- Run summary records `human_review_items`, `repaired_rows`, and `manual_frame_repairs` when applicable.
- Manual frame repairs record state, frame id, replacement source, backup path, and reason.
- Semantic anatomy repairs, including duplicate tails or extra limbs, are recorded with the same manual frame repair fields.
- Final reporting separates structural validation status from visual acceptance and remaining subjective concerns.
- User approval is requested for subjective look before install or sharing.

## User Approval

Codex owns structural checks. The user owns taste. Do not argue that a structurally valid row is aesthetically good. If the user dislikes a result, preserve useful variants and offer per-action refinement.
