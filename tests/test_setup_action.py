from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import tomlkit

import init_data
import execute


def test_whitelist_includes_mvp_actions() -> None:
    assert set(execute.ACTIONS) == {
        "enable-codex-memories",
        "add-claude-dispatch-rule",
        "validate-persona",
        "complete",
    }


def test_write_actions_reject_execution_before_dry_run(
    plugin_data: Path, isolated_home: Path
) -> None:
    with pytest.raises(execute.SetupActionError, match="dry_run"):
        execute.run_action(
            plugin_data,
            "enable-codex-memories",
            dry_run=False,
            home=isolated_home,
            now=datetime(2026, 5, 24, tzinfo=UTC),
        )


def test_confirm_token_expires(plugin_data: Path, isolated_home: Path) -> None:
    now = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    preview = execute.run_action(
        plugin_data,
        "enable-codex-memories",
        dry_run=True,
        home=isolated_home,
        now=now,
    )

    with pytest.raises(execute.SetupActionError, match="過期"):
        execute.run_action(
            plugin_data,
            "enable-codex-memories",
            dry_run=False,
            confirm_token=preview["confirm_token"],
            home=isolated_home,
            now=now + timedelta(minutes=11),
        )


def test_symlink_target_is_refused(plugin_data: Path, isolated_home: Path) -> None:
    codex_dir = isolated_home / ".codex"
    codex_dir.mkdir()
    target = isolated_home / "outside.toml"
    target.write_text("", encoding="utf-8")
    (codex_dir / "config.toml").symlink_to(target)

    with pytest.raises(execute.SetupActionError, match="symlink"):
        execute.run_action(
            plugin_data,
            "enable-codex-memories",
            dry_run=True,
            home=isolated_home,
            now=datetime(2026, 5, 24, tzinfo=UTC),
        )


def test_enable_codex_memories_writes_config(plugin_data: Path, isolated_home: Path) -> None:
    run_with_approval(plugin_data, isolated_home, "enable-codex-memories")

    config = tomlkit.parse((isolated_home / ".codex" / "config.toml").read_text(encoding="utf-8"))
    assert config["features"]["memories"] is True


def test_add_claude_dispatch_rule_appends_disable_instruction(
    plugin_data: Path, isolated_home: Path
) -> None:
    run_with_approval(plugin_data, isolated_home, "add-claude-dispatch-rule")

    content = (isolated_home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "CODEX_PET_DISABLE=1" in content
    assert "codex-fursona-pet-forge" in content


def test_validate_persona_is_read_only(
    plugin_root: Path, plugin_data: Path, isolated_home: Path
) -> None:
    init_data.ensure_initialized(plugin_root, plugin_data)

    result = execute.run_action(
        plugin_data,
        "validate-persona",
        home=isolated_home,
        now=datetime(2026, 5, 24, tzinfo=UTC),
    )

    assert result["ok"] is True
    assert result["persona"] == "拉爾夫"


def test_complete_deletes_onboarding_marker(plugin_data: Path, isolated_home: Path) -> None:
    marker = plugin_data / ".onboarding-pending"
    marker.touch()

    run_with_approval(plugin_data, isolated_home, "complete")

    assert not marker.exists()


def test_plugin_data_dir_uses_installed_plugin_data_from_config(
    codex_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PLUGIN_DATA", raising=False)
    (codex_home / "config.toml").write_text(
        '[plugins."codex-fursona-pet-forge@codex-fursona-local"]\n'
        "enabled = true\n",
        encoding="utf-8",
    )

    assert (
        execute._plugin_data_dir()
        == codex_home / "plugins" / "data" / "codex-fursona-pet-forge-codex-fursona-local"
    )


def run_with_approval(plugin_data: Path, home: Path, action: str) -> dict[str, object]:
    now = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    preview = execute.run_action(plugin_data, action, dry_run=True, home=home, now=now)
    return execute.run_action(
        plugin_data,
        action,
        dry_run=False,
        confirm_token=preview["confirm_token"],
        home=home,
        now=now,
    )
