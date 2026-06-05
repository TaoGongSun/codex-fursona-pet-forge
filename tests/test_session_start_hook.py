from pathlib import Path

import pytest

import write_fact
import session_start


def test_malformed_stdin_returns_continue(plugin_root: Path, plugin_data: Path) -> None:
    result = session_start.handle("{not json", plugin_root=plugin_root, plugin_data=plugin_data)

    assert result == {"continue": True}


def test_hook_calls_init_on_read(plugin_root: Path, plugin_data: Path) -> None:
    session_start.handle("{}", plugin_root=plugin_root, plugin_data=plugin_data)

    assert (plugin_data / "persona.yaml").exists()
    assert (plugin_data / "config.yaml").exists()
    assert (plugin_data / "personal-facts" / "MEMORY.md").exists()
    assert (plugin_data / ".onboarding-pending").exists()


def test_hook_outputs_session_start_additional_context(
    plugin_root: Path, plugin_data: Path
) -> None:
    result = session_start.handle("{}", plugin_root=plugin_root, plugin_data=plugin_data)

    assert result["continue"] is True
    assert result["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "# Pet Persona" in result["hookSpecificOutput"]["additionalContext"]


def test_skip_path_returns_no_additional_context(
    plugin_root: Path, plugin_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CODEX_PET_DISABLE", "1")

    result = session_start.handle("{}", plugin_root=plugin_root, plugin_data=plugin_data)

    assert result == {"continue": True}
    assert not (plugin_data / "persona.yaml").exists()


def test_io_failure_writes_error_log_and_does_not_raise(
    plugin_root: Path, plugin_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(session_start.init_data, "ensure_initialized", fail)

    result = session_start.handle("{}", plugin_root=plugin_root, plugin_data=plugin_data)

    assert result == {"continue": True}
    assert "disk full" in (plugin_data / "logs" / "error.log").read_text(encoding="utf-8")


def test_fact_written_by_skill_without_plugin_data_is_loaded_by_hook(
    codex_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    managed_data = codex_home / "plugins" / "data" / "codex-fursona-pet-forge-codex-fursona-local"
    (codex_home / "config.toml").write_text(
        '[plugins."codex-fursona-pet-forge@codex-fursona-local"]\n'
        "enabled = true\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("PLUGIN_DATA", raising=False)
    write_fact.write_fact(
        write_fact._plugin_data_dir(),
        {
            "name": "user-call-name",
            "fact": "使用者偏好被叫做小雅。",
            "type": "identity",
        },
    )

    monkeypatch.setenv("PLUGIN_DATA", str(managed_data))
    result = session_start.handle("{}")
    context = result["hookSpecificOutput"]["additionalContext"]

    assert "小雅" in context
    assert "# First-time setup" not in context
