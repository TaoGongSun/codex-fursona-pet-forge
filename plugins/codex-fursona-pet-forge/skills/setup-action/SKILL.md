---
name: setup-action
description: Run whitelisted Codex Fursona Pet Forge onboarding actions with dry-run and confirmation safeguards.
---

# setup-action

這個 skill 只執行 codex-fursona-pet-forge onboarding 需要的少量白名單動作。

白名單：

- `enable-codex-memories`：更新 `~/.codex/config.toml`。
- `add-claude-dispatch-rule`：更新 `~/.claude/CLAUDE.md`。
- `validate-persona`：只讀取並驗證 `PLUGIN_DATA/persona.yaml`。
- `complete`：刪除 `PLUGIN_DATA/.onboarding-pending`。

任何會寫入檔案的 action 都必須先以 `dry_run=true` 執行，向使用者說明將修改的目標與內容；使用者明確同意後，再用 dry-run 回傳的 `confirm_token` 執行。

stdin JSON 範例：

```json
{
  "action": "enable-codex-memories",
  "dry_run": true
}
```

執行：

```bash
python3 ${PLUGIN_ROOT}/skills/setup-action/execute.py
```
