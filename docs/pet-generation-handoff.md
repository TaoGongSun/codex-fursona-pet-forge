# Pet Generation Handoff

Use this format when a pet generation run becomes too long, when `/goal` needs a checkpoint, or when a new conversation should continue the same run. The output should be one copyable block.

## Required Fields

- run directory
- pet id and display name
- mode: supervised mode or one-shot goal mode
- canonical base path
- base 192x208 preview path
- accepted rows
- failed or risky rows
- rejected variants worth comparing
- extracted frames paths
- transparent GIF paths
- checker GIF paths
- raw slot overlay paths
- metrics paths or short bbox/bottom summary
- package paths if created
- known unresolved issues
- next action
- prompt corrections for the next action

## Copyable Block Template

```text
Continue Codex pet generation.

Run directory:
<absolute path>

Mode:
<supervised mode | one-shot goal mode>

Pet:
- id: <pet-id>
- display name: <name>

Canonical base:
- image: <path>
- 192x208 preview: <path>
- must keep: <short traits>
- must avoid: <short traits>

Accepted rows:
- idle: row=<path>; frames=<path>; gif=<path>; checker=<path>; metrics=<path or summary>
- running-right: row=<path>; frames=<path>; gif=<path>; checker=<path>; metrics=<path or summary>
- running-left: row=<path>; frames=<path>; gif=<path>; checker=<path>; metrics=<path or summary>
- waving: row=<path>; frames=<path>; gif=<path>; checker=<path>; metrics=<path or summary>
- jumping: row=<path>; frames=<path>; gif=<path>; checker=<path>; metrics=<path or summary>
- failed: row=<path>; frames=<path>; gif=<path>; checker=<path>; metrics=<path or summary>
- waiting: row=<path>; frames=<path>; gif=<path>; checker=<path>; metrics=<path or summary>
- running: row=<path>; frames=<path>; gif=<path>; checker=<path>; metrics=<path or summary>
- review: row=<path>; frames=<path>; gif=<path>; checker=<path>; metrics=<path or summary>

Failed or risky rows:
- <row>: <reason, retry count, best artifact>

Rejected variants worth comparing:
- <row>: <path> - <reason>

Package:
- pet.json: <path>
- spritesheet.webp: <path>
- validation: <path>
- contact sheet: <path>

Known issues:
- <issue>

Next action:
<exact next step>

Prompt corrections:
<short instructions the next worker should preserve>
```

## Rules

- Keep the block compact and factual.
- Do not include long visual descriptions when a path and decision are enough.
- Prefer exact paths over prose.
- Mention whether Codex should continue automatically or wait for user approval.
- If a row was accepted from a transparent 192x208 animated GIF, include that GIF path.
- Do not list every debug image; include only artifacts needed to continue safely.
