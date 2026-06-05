---
name: stretch-reminder
description: Configure Codex Fursona Pet Forge break reminders using Codex thread automations.
---

# stretch-reminder

Use this skill when the user asks to start, stop, pause, resume, change, snooze, or check a recurring reminder to stand up, stretch, drink water, or take a short movement break.

This skill does not monitor OS activity. It must not claim to know whether the user is physically at the computer.

## Behavior

- Use Codex thread automations for the recurring schedule.
- Use `reminder_config.py` to update `PLUGIN_DATA/config.yaml` and generate the durable automation prompt.
- Keep wording short, warm, and low-pressure.
- Time-aware phrasing is allowed as a soft guess only:
  - morning start: "早安"
  - lunch no-response: "是去吃飯了嗎？"
  - after midnight: "是不是該睡了？"
- Never say you know the user is eating, sleeping, away, or overworking.
- Do not edit project files, run commands, browse the web, or inspect private data as part of reminder wake-ups.

## Actions

Use these action names with `reminder_config.py`:

- `start`: enable reminders and generate an active thread automation proposal.
- `pause`: disable reminders without deleting the automation.
- `resume`: re-enable reminders.
- `stop`: disable reminders and prefer pausing the automation unless the user explicitly asks to delete it.
- `status`: report the current reminder settings.

stdin JSON examples:

```json
{
  "action": "start",
  "interval_minutes": 50,
  "activity_minutes": 3
}
```

```json
{
  "action": "pause"
}
```

Run:

```bash
python3 ${PLUGIN_ROOT}/skills/stretch-reminder/reminder_config.py
```

After `start`, `resume`, or interval changes, create or update a Codex thread automation using the returned `automation.name`, `automation.rrule`, `automation.status`, and `automation.prompt`.

If the Codex automation tool is unavailable, tell the user that the config was prepared but recurring reminders cannot be scheduled from this surface.
