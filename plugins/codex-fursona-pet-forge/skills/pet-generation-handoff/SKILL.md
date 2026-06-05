---
name: pet-generation-handoff
description: Create a compact copyable continuation summary for long Codex pet generation runs, especially /goal checkpoints, including run directory, canonical base, accepted rows, failed or risky rows, GIF previews, metrics, package paths, and next action.
---

# pet-generation-handoff

Use this when a pet generation run needs to continue in a later message, later conversation, or resumed `/goal`.

Read `docs/pet-generation-handoff.md` for the field list and template.

## Output Rules

- Return one copyable text block.
- Keep it compact.
- Include exact paths.
- Separate accepted rows from failed or risky rows.
- Include the transparent GIF path for every accepted row.
- Include the next action and prompt corrections.
- Do not duplicate the same information in prose outside the block.

## Required Content

The block must include:

- run directory
- pet id and display name
- canonical base path
- accepted rows
- failed or risky rows
- rejected variants worth comparing
- transparent GIF paths
- checker GIF paths when available
- metrics paths or short bbox/bottom summaries
- package paths when available
- known unresolved issues
- next action
