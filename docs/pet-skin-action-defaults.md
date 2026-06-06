# Pet Skin Action Defaults

These defaults are for the `make-pet-skin` skill and any pet generation worker. They are not a user-facing form.

## Global Row Rules

- Preserve the canonical base identity in every frame.
- Prefer a few core poses with held or tiny variant frames over nine unrelated drawings.
- Keep the pet centered inside each invisible slot with clear chroma-key gutters.
- Avoid text, UI, symbols, punctuation, detached effects, shadows, speed lines, dust, scenery, and fake transparency.
- Use pose, expression, ears, head angle, hands, tail, props already in the base identity, and body weight to express action.
- Produce row strips only as raw generation artifacts; user acceptance happens through extracted 192x208 GIF previews.

## `idle`

Purpose: calm presence.

Default pattern: six frames using breathing, blink, tiny head or shoulder change, tail-tip or accessory micro-motion.

Avoid:

- Waving.
- Walking or running.
- Tool use.
- Large arm movement.
- A loop where only one blink frame changes.
- Whole-body twisting or restless movement.

## `running-right`

Purpose: directional drag movement to the right.

Default pattern for bipeds: generate one three-cell strip containing only three key poses:

1. Left foot forward.
2. Legs crossing or passing under the body.
3. Right foot forward.

Extract those three poses, then assemble the eight final frames deterministically as `12321232`. Repeated pose numbers must reuse the same extracted image; do not ask the image model to generate eight separate frames.

Quadrupeds, legless, wheeled, floating, and other characters should use three equivalent readable locomotion phases instead of forced biped foot positions, then use the same `12321232` assembly.

Avoid:

- Eight independently generated running frames.
- Speed lines.
- Dust.
- Floor shadows.
- Motion trails.
- Detached effects.
- A static single-pose slide.

## `running-left`

Purpose: directional drag movement to the left.

Default: mirror the accepted `running-right` frame by frame after checking that mirroring does not break important asymmetry.

Generate independently only when:

- The character has non-mirrorable readable marks.
- A one-sided tool, limb, scar, or accessory would become wrong.
- The user explicitly chooses redraw over consistency.

An independently generated `running-left` must also use three key poses and deterministic `12321232` assembly.

## `waving`

Purpose: greeting.

Default pattern: four frames: arm low, arm rising, wave high point, return. Keep it as one clear waving limb unless the character design demands otherwise.

Avoid:

- Wave marks.
- Sparkles.
- Punctuation.
- Alternating left-hand/right-hand semantics unless intentional.
- Per-frame fit-to-cell extraction that makes raised-arm frames float.

## `jumping`

Purpose: hover attention, not necessarily a literal jump.

Default pattern: notices the user, perks up or half-crouches, small bounce or pleased attention, returns to idle-compatible stance.

Avoid:

- Large unexplained vertical leaps.
- Bounce pads.
- Floor marks.
- Dust.
- Shadows.
- Detached attention symbols.

For wide silhouettes, require compact square-ish footprints and generous slot gutters.

## `failed`

Purpose: blocked or failed-task reaction.

Default pattern: visible setback, lowered shoulders or head, lowered hands or tail, then recovery to idle-compatible stance.

Avoid:

- Red X marks.
- Floating symbols.
- Detached smoke.
- Detached stars.
- Loose tear drops.
- Comic helplessness unless the user asks for it.

Express failure through body language first.

## `waiting`

Purpose: Codex is waiting for user approval, input, or help.

Default pattern: expectant but calm pose. Hands, ears, head tilt, and body lean can show that the pet is waiting for the user.

Avoid:

- Ordinary idle.
- Review focus.
- Failure reaction.
- Text prompts or UI props.
- Large pleading effects.

For wide characters, treat calm semantics and slot safety as separate checks.

## `running`

Purpose: active work, processing, or task execution.

Default pattern: planted task-processing loop, such as focused stance, controlled arm/hand movement, small tool-like motion only if the prop already belongs to the pet.

Avoid:

- Literal foot running.
- Jogging.
- Sprinting.
- Treadmill motion.
- Speed lines.
- Dust.
- UI, code, text, or floating icons.

Reject rows that become either too wide for slots or too tiny after extraction.

## `review`

Purpose: checking, judging, or reviewing results.

Default pattern: focused lean, narrowed eyes, slight head movement, hand near chin/chest, stable thoughtful posture.

Avoid:

- Magnifying glasses.
- Papers.
- Screens.
- UI.
- Question marks.
- Exclamation marks.
- Stars.
- Floating symbols.

Use posture and gaze rather than new props.
