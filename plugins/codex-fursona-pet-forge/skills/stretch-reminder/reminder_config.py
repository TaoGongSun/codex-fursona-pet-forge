import json
import sys
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import init_data  # noqa: E402
import simple_yaml  # noqa: E402
from data_paths import plugin_data_dir as resolve_plugin_data_dir  # noqa: E402


class ReminderConfigError(ValueError):
    pass


ACTIONS = {"start", "pause", "resume", "stop", "status"}
MIN_INTERVAL_MINUTES = 5
MAX_INTERVAL_MINUTES = 180
MIN_ACTIVITY_MINUTES = 1
MAX_ACTIVITY_MINUTES = 30


def run_action(
    plugin_data: Path | str,
    action: str,
    interval_minutes: int | None = None,
    activity_minutes: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if action not in ACTIONS:
        raise ReminderConfigError(f"不支援的 action：{action}")

    data_dir = Path(plugin_data)
    current_time = now or datetime.now(UTC)
    config = _load_config(data_dir)
    reminder = _break_reminder(config)

    if action == "start":
        _apply_start(reminder, interval_minutes, activity_minutes, current_time)
    elif action == "pause":
        reminder["enabled"] = False
    elif action == "resume":
        reminder["enabled"] = True
    elif action == "stop":
        reminder["enabled"] = False
        reminder["unanswered_count"] = 0

    if action != "status":
        _save_config(data_dir, config)

    return {
        "ok": True,
        "action": action,
        "config": deepcopy(reminder),
        "automation": _automation_for(reminder, action),
        "message": _message_for(action, reminder, current_time),
    }


def time_context_message(value: datetime) -> str:
    hour = value.hour
    minute = value.minute
    as_minutes = hour * 60 + minute

    if 5 * 60 <= as_minutes <= 10 * 60 + 59:
        return "早安。今天也慢慢來，我幫你顧一下提醒。"
    if 11 * 60 + 30 <= as_minutes <= 13 * 60 + 30:
        return "是去吃飯了嗎？我先在這裡等你回來。"
    if 14 * 60 <= as_minutes <= 17 * 60 + 59:
        return "下午容易坐久，起來走三分鐘，讓肩膀也下班一下。"
    if 18 * 60 <= as_minutes <= 21 * 60 + 59:
        return "傍晚了，收個尾之前先起身活動一下。"
    if 22 * 60 <= as_minutes <= 23 * 60 + 59:
        return "時間不早了，這次伸展完，也可以想想收工了。"
    if 0 <= as_minutes <= 4 * 60 + 59:
        return "都過午夜了。是不是該睡了？如果還要收尾，我陪你把這段做穩。"
    return "該起身活動一下了。"


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            raise ReminderConfigError("stdin JSON 必須是 object")
        result = run_action(
            _plugin_data_dir(),
            action=str(payload.get("action") or ""),
            interval_minutes=_optional_int(payload.get("interval_minutes")),
            activity_minutes=_optional_int(payload.get("activity_minutes")),
        )
    except ReminderConfigError as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 1

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def _apply_start(
    reminder: dict[str, Any],
    interval_minutes: int | None,
    activity_minutes: int | None,
    now: datetime,
) -> None:
    interval = interval_minutes if interval_minutes is not None else int(reminder["interval_minutes"])
    activity = activity_minutes if activity_minutes is not None else int(reminder["activity_minutes"])
    _validate_range(
        "interval_minutes",
        interval,
        MIN_INTERVAL_MINUTES,
        MAX_INTERVAL_MINUTES,
    )
    _validate_range(
        "activity_minutes",
        activity,
        MIN_ACTIVITY_MINUTES,
        MAX_ACTIVITY_MINUTES,
    )

    reminder["enabled"] = True
    reminder["interval_minutes"] = interval
    reminder["activity_minutes"] = activity
    reminder["last_started_at"] = now.isoformat()
    reminder["unanswered_count"] = 0


def _automation_for(reminder: dict[str, Any], action: str) -> dict[str, str]:
    status = "ACTIVE" if reminder.get("enabled") else "PAUSED"
    if action in {"pause", "stop"}:
        status = "PAUSED"

    return {
        "kind": "thread",
        "name": str(reminder["automation"]["name"]),
        "rrule": f"FREQ=MINUTELY;INTERVAL={int(reminder['interval_minutes'])}",
        "status": status,
        "prompt": _automation_prompt(reminder),
    }


def _automation_prompt(reminder: dict[str, Any]) -> str:
    return "\n".join(
        [
            "用 Codex Fursona Pet Forge 的語氣提醒使用者起身活動。",
            f"每 {int(reminder['interval_minutes'])} 分鐘提醒一次。",
            f"每次建議活動 {int(reminder['activity_minutes'])} 分鐘。",
            "可以依目前本地時間做早安、中午、夜深等溫和問候。",
            "只能使用「是不是、也許、我猜、如果你正在」這類軟推測，不能宣稱知道使用者正在做什麼。",
            "不要編輯檔案、不要執行命令、不要瀏覽網路、不要檢查私人資料。",
            "若使用者連續沒有回應，請降低打擾並說明會先安靜，等使用者要求恢復。",
        ]
    )


def _message_for(action: str, reminder: dict[str, Any], now: datetime) -> str:
    if action == "start":
        prefix = time_context_message(now) if _time_context_enabled(reminder) else "提醒時間到了。"
        return f"{prefix} 已開啟每 {int(reminder['interval_minutes'])} 分鐘一次的起身提醒。"
    if action == "pause":
        return "我先暫停起身提醒。你說「恢復起身提醒」時，我再接著顧時間。"
    if action == "resume":
        return f"我恢復起身提醒了，現在是每 {int(reminder['interval_minutes'])} 分鐘一次。"
    if action == "stop":
        return "起身提醒已停止。我不會再主動提醒，除非你重新開始。"
    return (
        f"起身提醒目前{'啟用' if reminder.get('enabled') else '暫停'}，"
        f"每 {int(reminder['interval_minutes'])} 分鐘一次，"
        f"每次活動 {int(reminder['activity_minutes'])} 分鐘。"
    )


def _load_config(data_dir: Path) -> dict[str, Any]:
    init_data.ensure_config_defaults(data_dir)
    path = data_dir / "config.yaml"
    loaded = simple_yaml.load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else deepcopy(init_data.DEFAULT_CONFIG)


def _save_config(data_dir: Path, config: dict[str, Any]) -> None:
    (data_dir / "config.yaml").write_text(init_data._dump_yaml(config), encoding="utf-8")


def _break_reminder(config: dict[str, Any]) -> dict[str, Any]:
    wellness = config.setdefault("wellness", {})
    if not isinstance(wellness, dict):
        config["wellness"] = wellness = {}
    reminder = wellness.setdefault(
        "break_reminder",
        deepcopy(init_data.DEFAULT_CONFIG["wellness"]["break_reminder"]),
    )
    if not isinstance(reminder, dict):
        wellness["break_reminder"] = reminder = deepcopy(
            init_data.DEFAULT_CONFIG["wellness"]["break_reminder"]
        )
    return reminder


def _time_context_enabled(reminder: dict[str, Any]) -> bool:
    value = reminder.get("time_context", {})
    return isinstance(value, dict) and value.get("enabled") is True


def _validate_range(name: str, value: int, minimum: int, maximum: int) -> None:
    if value < minimum or value > maximum:
        raise ReminderConfigError(f"{name} 必須介於 {minimum} 到 {maximum} 之間")


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _plugin_data_dir() -> Path:
    return resolve_plugin_data_dir()


if __name__ == "__main__":
    raise SystemExit(main())
