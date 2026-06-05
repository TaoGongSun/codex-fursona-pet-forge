# Codex Fursona Pet Forge

Codex Fursona Pet Forge helps you turn one fursona reference image into a Codex
desktop pet package. The main product is pet-skin creation: generated action
rows, QA previews, a Codex-compatible atlas, and a package you can install as a
desktop pet. Companion features are secondary: you can configure the pet's name,
voice, personality, memory, and gentle break reminders after the skin workflow is
set up.

This project is fursona-first. Other clear original character or mascot
references may also work, but the prompts, QA checks, and docs are optimized for
furry-style Codex desktop pet skins rather than generic game sprites or broad
image editing.

## What It Can Do

- Create a Codex pet skin from one fursona or character reference image.
- Run a one-shot `/goal` workflow that attempts all actions, QA, atlas creation,
  and packaging in one pass.
- Work action by action in supervised mode, which is slower but usually more
  stable because you can approve each transparent GIF before moving on.
- Use `hatch-pet` for image generation, deterministic frame extraction, row QA,
  animation previews, atlas composition, and package validation.
- Keep compact handoff notes for long generation runs with `pet-generation-handoff`.
- Let the pet act as a lightweight companion by storing non-sensitive user facts,
  names, personality settings, and recent context.
- Configure recurring stretch or break reminders through Codex thread
  automations when that Codex surface supports them.

## Included Skills

These skills come with this plugin after installation:

- `make-pet-skin`: main pet-skin creation workflow.
- `pet-generation-handoff`: compact continuation summary for long `/goal` runs.
- `remember-this`: stores stable, non-sensitive personal facts for future pet
  sessions.
- `setup-action`: guarded setup actions with dry-run and confirmation.
- `stretch-reminder`: prepares recurring break reminder settings and automation
  prompts.

External dependency:

- `hatch-pet`: required for real pet generation and packaging.

Optional:

- `generate2dsprite`: useful for broader sprite-heavy work, but not required for
  this fursona pet workflow.

## Install

### 1. Install This Plugin

From anywhere on your machine, ask Codex to install this marketplace plugin from
your local checkout, or run:

```bash
codex plugin marketplace add /path/to/codex-fursona-pet-forge
codex plugin add codex-fursona-pet-forge@codex-fursona-local
```

For a local checkout whose folder name has not been changed yet, use that
checkout path:

```bash
codex plugin marketplace add /path/to/local/checkout
codex plugin add codex-fursona-pet-forge@codex-fursona-local
```

If Codex asks you to review hooks, open `/hooks`, inspect this plugin's hooks,
trust them, then start a new Codex session.

### 2. Install Hatch Pet

`make-pet-skin` needs the external `hatch-pet` skill. In Codex, ask:

```text
Install the hatch-pet skill from https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet
```

Codex should use `skill-installer` to install it into your Codex skills folder.
After installation, restart Codex so the new skill is discovered.

Source: https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet

### 3. Install Local Python Image Tools

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

This installs Pillow and related test dependencies. The local QA scripts use
Pillow to read and write PNG, WebP, and GIF files, clean transparent
backgrounds, crop frames, build contact sheets, and run pixel-level checks.

## Make a Pet Skin

Use one clear fursona reference image if possible.

Simple request:

```text
用這張角色設定圖幫我做 Codex 桌寵。
```

One-shot run:

```text
/goal 用這張角色設定圖一鍵製作完整 Codex 桌寵，包含所有動作、QA、atlas 和 package。
```

Supervised run:

```text
用這張角色設定圖幫我做 Codex 桌寵，但一個動作一個動作慢慢做，每個 GIF 讓我確認。
```

The one-shot path is convenient for testing the full pipeline. The supervised
path is better when character details matter, because each action can be checked
as a real 192x208 transparent animation before the next one is generated.

## Companion Features

The companion layer is optional and supports the pet experience around the skin:

- Set or change how the pet addresses you.
- Set or change the pet's name, voice, personality, and background.
- Store stable, non-sensitive preferences through `remember-this`.
- Keep short recent-session context when hooks are trusted and enabled.
- Configure gentle stretch, water, or movement reminders through
  `stretch-reminder`.

The reminder feature does not monitor your keyboard, mouse, apps, screenshots,
camera, or microphone. It only prepares local settings and Codex thread
automation prompts.

## Validation

Run the test suite from the repo root:

```bash
.venv/bin/python -m pytest -q
```
