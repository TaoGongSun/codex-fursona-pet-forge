from pathlib import Path

import pytest

import write_fact


def test_new_fact_creates_slug_file(plugin_data: Path) -> None:
    result = write_fact.write_fact(
        plugin_data,
        {
            "name": "preferred name",
            "fact": "使用者喜歡被叫做小雅。",
            "type": "identity",
            "sensitivity": "normal",
            "source": "conversation",
        },
    )

    fact_path = plugin_data / "personal-facts" / "preferred-name.md"
    assert result["path"] == str(fact_path)
    assert fact_path.exists()
    assert "使用者喜歡被叫做小雅。" in fact_path.read_text(encoding="utf-8")


def test_same_slug_updates_instead_of_duplicating(plugin_data: Path) -> None:
    write_fact.write_fact(
        plugin_data,
        {
            "name": "preferred-name",
            "fact": "使用者喜歡被叫做小雅。",
            "type": "identity",
        },
    )
    write_fact.write_fact(
        plugin_data,
        {
            "name": "preferred name",
            "fact": "使用者現在喜歡被叫做老師。",
            "type": "identity",
        },
    )

    files = list((plugin_data / "personal-facts").glob("*.md"))
    assert sorted(path.name for path in files) == ["MEMORY.md", "preferred-name.md"]
    assert "老師" in (plugin_data / "personal-facts" / "preferred-name.md").read_text(
        encoding="utf-8"
    )


def test_memory_index_groups_facts_by_type(plugin_data: Path) -> None:
    write_fact.write_fact(
        plugin_data,
        {"name": "preferred-name", "fact": "使用者喜歡被叫做小雅。", "type": "identity"},
    )
    write_fact.write_fact(
        plugin_data,
        {"name": "focus-style", "fact": "使用者偏好一次處理一件事。", "type": "preference"},
    )

    memory = (plugin_data / "personal-facts" / "MEMORY.md").read_text(encoding="utf-8")

    assert "## identity" in memory
    assert "[preferred-name](preferred-name.md)" in memory
    assert "## preference" in memory
    assert "[focus-style](focus-style.md)" in memory


def test_secret_like_input_is_rejected_without_override(plugin_data: Path) -> None:
    with pytest.raises(write_fact.FactError, match="敏感"):
        write_fact.write_fact(
            plugin_data,
            {
                "name": "api-token",
                "fact": "我的 token 是 sk-test-secret",
                "type": "credential",
                "sensitivity": "secret",
            },
        )

    assert not (plugin_data / "personal-facts" / "api-token.md").exists()


def test_secret_like_input_can_be_saved_with_explicit_override(plugin_data: Path) -> None:
    write_fact.write_fact(
        plugin_data,
        {
            "name": "local-test-token-note",
            "fact": "使用者明確要求本機保存測試 token 註記：sk-test-secret。",
            "type": "credential",
            "sensitivity": "secret",
            "allow_sensitive": True,
        },
    )

    assert (plugin_data / "personal-facts" / "local-test-token-note.md").exists()


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
        write_fact._plugin_data_dir()
        == codex_home / "plugins" / "data" / "codex-fursona-pet-forge-codex-fursona-local"
    )
