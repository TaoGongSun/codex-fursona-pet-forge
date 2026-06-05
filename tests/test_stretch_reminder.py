from datetime import UTC, datetime
from pathlib import Path

import pytest

import reminder_config


def test_start_enables_reminder_and_returns_thread_automation(plugin_data: Path) -> None:
    result = reminder_config.run_action(
        plugin_data,
        "start",
        interval_minutes=40,
        activity_minutes=5,
        now=datetime(2026, 5, 26, 8, 30, tzinfo=UTC),
    )

    assert result["ok"] is True
    assert result["action"] == "start"
    assert result["config"]["enabled"] is True
    assert result["config"]["interval_minutes"] == 40
    assert result["config"]["activity_minutes"] == 5
    assert result["automation"]["kind"] == "thread"
    assert result["automation"]["rrule"] == "FREQ=MINUTELY;INTERVAL=40"
    assert "早安" in result["message"]
    assert "每 40 分鐘" in result["automation"]["prompt"]
    assert "不能宣稱知道使用者正在做什麼" in result["automation"]["prompt"]


def test_start_rejects_unsafe_interval(plugin_data: Path) -> None:
    with pytest.raises(reminder_config.ReminderConfigError, match="interval_minutes"):
        reminder_config.run_action(plugin_data, "start", interval_minutes=4)


def test_pause_and_resume_update_enabled_state(plugin_data: Path) -> None:
    reminder_config.run_action(plugin_data, "start", interval_minutes=25)

    paused = reminder_config.run_action(plugin_data, "pause")
    resumed = reminder_config.run_action(plugin_data, "resume")

    assert paused["config"]["enabled"] is False
    assert paused["automation"]["status"] == "PAUSED"
    assert resumed["config"]["enabled"] is True
    assert resumed["automation"]["status"] == "ACTIVE"


def test_status_reports_current_config(plugin_data: Path) -> None:
    reminder_config.run_action(plugin_data, "start", interval_minutes=55, activity_minutes=2)

    result = reminder_config.run_action(plugin_data, "status")

    assert result["ok"] is True
    assert result["config"]["interval_minutes"] == 55
    assert "55" in result["message"]


def test_time_context_uses_soft_guesses() -> None:
    lunch = reminder_config.time_context_message(datetime(2026, 5, 26, 12, 15))
    midnight = reminder_config.time_context_message(datetime(2026, 5, 27, 0, 30))

    assert "是去吃飯了嗎" in lunch
    assert "是不是該睡了" in midnight
    assert "你去吃飯了" not in lunch
    assert "你在熬夜" not in midnight
