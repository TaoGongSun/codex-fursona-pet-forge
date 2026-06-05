from pathlib import Path

import yaml

import init_data
import write_fact


def test_first_run_creates_default_data(tmp_path: Path, monkeypatch) -> None:
    root = plugin_root_with_default_persona(tmp_path)
    data_dir = tmp_path / "data"
    monkeypatch.delenv("CODEX_PET_LOCALE", raising=False)

    init_data.ensure_initialized(root, data_dir)

    assert (data_dir / "persona.yaml").read_text(encoding="utf-8") == (
        root / "personas" / "default-ralf.zh-TW.yaml"
    ).read_text(encoding="utf-8")
    assert yaml.safe_load((data_dir / "config.yaml").read_text(encoding="utf-8")) == {
        "short_circuit": {
            "env_var": True,
            "cwd_marker": True,
            "full_auto": False,
        },
        "context": {
            "recent_limit": 3,
            "max_words": 1200,
        },
        "wellness": {
            "break_reminder": {
                "enabled": False,
                "interval_minutes": 50,
                "activity_minutes": 3,
                "timezone": "local",
                "inactivity_threshold_minutes": 60,
                "max_unanswered_reminders": 2,
                "quiet_hours": {
                    "enabled": True,
                    "start": "22:00",
                    "end": "09:00",
                },
                "time_context": {
                    "enabled": True,
                    "style": "gentle_guess",
                },
                "tone": "gentle",
                "last_started_at": "",
                "last_user_interaction_at": "",
                "last_reminder_at": "",
                "unanswered_count": 0,
                "automation": {
                    "kind": "thread",
                    "name": "Codex Pet Break Reminder",
                },
            },
        },
    }
    assert (data_dir / "personal-facts" / "MEMORY.md").read_text(
        encoding="utf-8"
    ).startswith("# Personal facts")
    assert (data_dir / ".onboarding-pending").exists()


def test_first_run_uses_requested_locale(tmp_path: Path, monkeypatch) -> None:
    root = plugin_root_with_default_persona(tmp_path)
    data_dir = tmp_path / "data"
    monkeypatch.setenv("CODEX_PET_LOCALE", "en")

    init_data.ensure_initialized(root, data_dir)

    assert "Ralf" in (data_dir / "persona.yaml").read_text(encoding="utf-8")


def test_unknown_locale_falls_back_to_default_locale(tmp_path: Path, monkeypatch) -> None:
    root = plugin_root_with_default_persona(tmp_path)
    data_dir = tmp_path / "data"
    monkeypatch.setenv("CODEX_PET_LOCALE", "fr")

    init_data.ensure_initialized(root, data_dir)

    assert "拉爾夫" in (data_dir / "persona.yaml").read_text(encoding="utf-8")


def test_legacy_facts_and_completed_onboarding_migrate_to_managed_data(
    tmp_path: Path, codex_home: Path
) -> None:
    root = plugin_root_with_default_persona(tmp_path)
    legacy_data = codex_home / "plugins" / "-".join(("codex", "pet", "persona")) / "data"
    managed_data = codex_home / "plugins" / "data" / "codex-fursona-pet-forge-codex-fursona-local"
    (managed_data / "personal-facts").mkdir(parents=True)
    (managed_data / "personal-facts" / "MEMORY.md").write_text(
        init_data.DEFAULT_MEMORY,
        encoding="utf-8",
    )
    (managed_data / ".onboarding-pending").touch()
    write_fact.write_fact(
        legacy_data,
        {
            "name": "user-call-name",
            "fact": "使用者偏好被叫做小雅。",
            "type": "identity",
        },
    )

    init_data.ensure_initialized(root, managed_data)

    assert (managed_data / "personal-facts" / "user-call-name.md").exists()
    assert "小雅" in (managed_data / "personal-facts" / "MEMORY.md").read_text(
        encoding="utf-8"
    )
    assert not (managed_data / ".onboarding-pending").exists()


def test_rerun_does_not_overwrite_customized_persona(tmp_path: Path) -> None:
    root = plugin_root_with_default_persona(tmp_path)
    data_dir = tmp_path / "data"
    init_data.ensure_initialized(root, data_dir)

    custom = "name: 自訂角色\nspecies: test\n"
    (data_dir / "persona.yaml").write_text(custom, encoding="utf-8")
    (data_dir / ".onboarding-pending").unlink()

    init_data.ensure_initialized(root, data_dir)

    assert (data_dir / "persona.yaml").read_text(encoding="utf-8") == custom
    assert not (data_dir / ".onboarding-pending").exists()


def test_missing_subdirectories_are_recreated(tmp_path: Path) -> None:
    root = plugin_root_with_default_persona(tmp_path)
    data_dir = tmp_path / "data"
    init_data.ensure_initialized(root, data_dir)

    for name in ["personal-facts", "recent", "markers", "logs"]:
        remove_empty_dir(data_dir / name)

    init_data.ensure_initialized(root, data_dir)

    for name in ["personal-facts", "recent", "markers", "logs"]:
        assert (data_dir / name).is_dir()
    assert (data_dir / "personal-facts" / "MEMORY.md").exists()


def test_existing_config_gets_break_reminder_defaults_without_losing_keys(
    tmp_path: Path,
) -> None:
    root = plugin_root_with_default_persona(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "config.yaml").write_text(
        "\n".join(
            [
                "short_circuit:",
                "  env_var: false",
                "context:",
                "  recent_limit: 5",
                "custom:",
                "  keep: kept",
                "",
            ]
        ),
        encoding="utf-8",
    )

    init_data.ensure_initialized(root, data_dir)

    config = yaml.safe_load((data_dir / "config.yaml").read_text(encoding="utf-8"))
    assert config["short_circuit"]["env_var"] is False
    assert config["context"]["recent_limit"] == 5
    assert config["custom"]["keep"] == "kept"
    assert config["wellness"]["break_reminder"]["interval_minutes"] == 50
    assert config["wellness"]["break_reminder"]["time_context"]["enabled"] is True


def plugin_root_with_default_persona(tmp_path: Path) -> Path:
    root = tmp_path / "plugin-root"
    personas = root / "personas"
    personas.mkdir(parents=True)
    (personas / "default-ralf.yaml").write_text(
        zh_tw_persona,
        encoding="utf-8",
    )
    (personas / "default-ralf.zh-TW.yaml").write_text(
        zh_tw_persona,
        encoding="utf-8",
    )
    (personas / "default-ralf.en.yaml").write_text(
        "\n".join(
            [
                "name: Ralf",
                "species: German Shepherd anthro",
                "background: Test default persona",
                "voice:",
                "  style: warm and focused",
                "addressing:",
                "  default: you",
                "memory_directive: Only remember personal facts the user explicitly allows.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return root


zh_tw_persona = "\n".join(
    [
        "name: 拉爾夫",
        "species: 黑白邊境牧羊犬",
        "background: 測試用預設人格",
        "voice:",
        "  style: 溫暖、專注",
        "addressing:",
        "  default: 你",
        "memory_directive: 只記住使用者明確允許的個人事實",
        "",
    ]
)


def remove_empty_dir(path: Path) -> None:
    for child in sorted(path.iterdir(), reverse=True):
        if child.is_file():
            child.unlink()
    path.rmdir()
