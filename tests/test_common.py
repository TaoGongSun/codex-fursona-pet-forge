from pathlib import Path

import pytest

import _common


def test_plugin_root_prefers_env(plugin_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLUGIN_ROOT", str(plugin_root))

    assert _common.plugin_root() == plugin_root


def test_plugin_data_dir_prefers_env(plugin_data: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLUGIN_DATA", str(plugin_data))

    assert _common.plugin_data_dir() == plugin_data


def test_plugin_data_dir_falls_back_to_codex_home(
    codex_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PLUGIN_DATA", raising=False)

    assert _common.plugin_data_dir() == codex_home / "plugins" / "codex-fursona-pet-forge" / "data"


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
        _common.plugin_data_dir()
        == codex_home / "plugins" / "data" / "codex-fursona-pet-forge-codex-fursona-local"
    )


def test_plugin_data_dir_can_read_old_managed_data_after_rename(
    codex_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PLUGIN_DATA", raising=False)
    old_name = "-".join(("codex", "pet", "persona"))
    old_marketplace = "-".join(("codex", "pet", "local"))
    old_data = codex_home / "plugins" / "data" / f"{old_name}-{old_marketplace}"
    old_data.mkdir(parents=True)

    assert _common.plugin_data_dir() == old_data


def test_should_skip_handles_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_PET_DISABLE", "1")

    assert _common.should_skip({}, {}) == (True, "env-var")


def test_should_skip_respects_env_var_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_PET_DISABLE", "1")

    assert _common.should_skip({}, {"short_circuit": {"env_var": False}}) == (False, "")


def test_should_skip_handles_cwd_marker(tmp_path: Path) -> None:
    (tmp_path / ".codex-pet-disable").write_text("", encoding="utf-8")

    assert _common.should_skip({"cwd": str(tmp_path)}, {}) == (True, "cwd-marker")


def test_should_skip_handles_full_auto_config() -> None:
    config = {"short_circuit": {"full_auto": True}}

    assert _common.should_skip({"permission_mode": "full-auto"}, config) == (
        True,
        "full-auto",
    )


def test_should_skip_ignores_full_auto_by_default() -> None:
    assert _common.should_skip({"permission_mode": "full-auto"}, {}) == (False, "")
