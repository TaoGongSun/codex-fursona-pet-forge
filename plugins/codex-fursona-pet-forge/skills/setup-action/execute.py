import json
import secrets
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from data_paths import plugin_data_dir as resolve_plugin_data_dir  # noqa: E402
from persona import load_persona  # noqa: E402


class SetupActionError(ValueError):
    pass


TOKEN_TTL = timedelta(minutes=10)
ACTIONS = {
    "enable-codex-memories": {"write": True},
    "add-claude-dispatch-rule": {"write": True},
    "validate-persona": {"write": False},
    "complete": {"write": True},
}
CLAUDE_DISPATCH_RULE = """<!-- codex-fursona-pet-forge:dispatch-disable -->
## Codex Fursona Pet Forge dispatch

當你從 Claude Code 派生 Codex 子工作時，請在該 subprocess 設定 `CODEX_PET_DISABLE=1`，避免把自動化工作內容寫入 Codex Fursona Pet Forge 的 personal/recent memory。
<!-- /codex-fursona-pet-forge:dispatch-disable -->
"""


def run_action(
    plugin_data: Path | str,
    action: str,
    dry_run: bool = False,
    confirm_token: str | None = None,
    home: Path | str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if action not in ACTIONS:
        raise SetupActionError(f"不支援的 action：{action}")

    data_dir = Path(plugin_data)
    home_dir = Path(home) if home is not None else Path.home()
    current_time = now or datetime.now(UTC)
    target = _target_for(action, data_dir, home_dir)
    is_write_action = bool(ACTIONS[action]["write"])

    if is_write_action:
        _refuse_symlink_target(target)
        if dry_run:
            token = _store_dry_run(data_dir, action, target, current_time)
            return {
                "ok": True,
                "dry_run": True,
                "action": action,
                "target": str(target),
                "confirm_token": token,
                "expires_at": (current_time + TOKEN_TTL).isoformat(),
                "preview": _preview_for(action, target),
            }

        _validate_confirm_token(data_dir, action, target, confirm_token, current_time)

    result = _perform_action(data_dir, action, target)
    if confirm_token:
        _delete_token(data_dir, confirm_token)
    return result


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            raise SetupActionError("stdin JSON 必須是 object")
        result = run_action(
            _plugin_data_dir(),
            action=str(payload.get("action") or ""),
            dry_run=bool(payload.get("dry_run")),
            confirm_token=payload.get("confirm_token"),
        )
    except SetupActionError as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 1

    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def _target_for(action: str, plugin_data: Path, home: Path) -> Path:
    if action == "enable-codex-memories":
        return home / ".codex" / "config.toml"
    if action == "add-claude-dispatch-rule":
        return home / ".claude" / "CLAUDE.md"
    if action == "validate-persona":
        return plugin_data / "persona.yaml"
    if action == "complete":
        return plugin_data / ".onboarding-pending"
    raise SetupActionError(f"不支援的 action：{action}")


def _preview_for(action: str, target: Path) -> str:
    previews = {
        "enable-codex-memories": "將啟用 Codex native memories 設定。",
        "add-claude-dispatch-rule": "將追加 Claude Code dispatch Codex 時停用 persona 的規則。",
        "complete": "將標記 onboarding 已完成。",
    }
    return f"{previews.get(action, '將執行白名單動作')} 目標：{target}"


def _store_dry_run(data_dir: Path, action: str, target: Path, now: datetime) -> str:
    token = secrets.token_urlsafe(24)
    records = _load_tokens(data_dir)
    records[token] = {
        "action": action,
        "target": str(target),
        "expires_at": (now + TOKEN_TTL).isoformat(),
    }
    _write_tokens(data_dir, records)
    return token


def _validate_confirm_token(
    data_dir: Path,
    action: str,
    target: Path,
    token: str | None,
    now: datetime,
) -> None:
    if not token:
        raise SetupActionError("寫入 action 必須先 dry_run 並提供 confirm_token")

    records = _load_tokens(data_dir)
    record = records.get(token)
    if not record:
        raise SetupActionError("寫入 action 必須先 dry_run 並提供有效 confirm_token")
    if record.get("action") != action or record.get("target") != str(target):
        raise SetupActionError("confirm_token 與本次 action 不符")

    expires_at = datetime.fromisoformat(str(record.get("expires_at")))
    if now > expires_at:
        raise SetupActionError("confirm_token 已過期，請重新 dry_run")


def _perform_action(data_dir: Path, action: str, target: Path) -> dict[str, Any]:
    if action == "enable-codex-memories":
        return _enable_codex_memories(target)
    if action == "add-claude-dispatch-rule":
        return _add_claude_dispatch_rule(target)
    if action == "validate-persona":
        loaded = load_persona(target)
        return {"ok": True, "action": action, "target": str(target), "persona": loaded["name"]}
    if action == "complete":
        (data_dir / ".onboarding-pending").unlink(missing_ok=True)
        return {"ok": True, "action": action, "target": str(target), "completed": True}
    raise SetupActionError(f"不支援的 action：{action}")


def _enable_codex_memories(target: Path) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    content = target.read_text(encoding="utf-8") if target.exists() else ""
    target.write_text(_set_toml_feature_memories(content), encoding="utf-8")
    return {"ok": True, "action": "enable-codex-memories", "target": str(target)}


def _add_claude_dispatch_rule(target: Path) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    content = target.read_text(encoding="utf-8") if target.exists() else ""
    if "codex-fursona-pet-forge:dispatch-disable" not in content:
        separator = "\n\n" if content.strip() else ""
        target.write_text(content.rstrip() + separator + CLAUDE_DISPATCH_RULE + "\n", encoding="utf-8")
    return {"ok": True, "action": "add-claude-dispatch-rule", "target": str(target)}


def _refuse_symlink_target(target: Path) -> None:
    if target.exists() and target.is_symlink():
        raise SetupActionError(f"拒絕寫入 symlink target：{target}")
    for parent in target.parents:
        if parent.exists() and parent.is_symlink():
            raise SetupActionError(f"拒絕寫入 symlink parent：{parent}")


def _load_tokens(data_dir: Path) -> dict[str, dict[str, str]]:
    path = _token_store(data_dir)
    if not path.exists():
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _write_tokens(data_dir: Path, records: dict[str, dict[str, str]]) -> None:
    path = _token_store(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def _delete_token(data_dir: Path, token: str) -> None:
    records = _load_tokens(data_dir)
    if token in records:
        del records[token]
        _write_tokens(data_dir, records)


def _set_toml_feature_memories(content: str) -> str:
    lines = content.splitlines()
    output: list[str] = []
    in_features = False
    saw_features = False
    wrote_memories = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_features and not wrote_memories:
                output.append("memories = true")
                wrote_memories = True
            in_features = stripped == "[features]"
            saw_features = saw_features or in_features
            output.append(line)
            continue

        if in_features and stripped.startswith("memories"):
            output.append("memories = true")
            wrote_memories = True
        else:
            output.append(line)

    if in_features and not wrote_memories:
        output.append("memories = true")
    if not saw_features:
        if output and output[-1].strip():
            output.append("")
        output.extend(["[features]", "memories = true"])

    return "\n".join(output).rstrip() + "\n"


def _token_store(data_dir: Path) -> Path:
    return data_dir / "markers" / "setup-action-dry-runs.json"


def _plugin_data_dir() -> Path:
    return resolve_plugin_data_dir()


if __name__ == "__main__":
    raise SystemExit(main())
