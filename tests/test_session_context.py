from pathlib import Path

import init_data
import session_context


def test_context_includes_persona_fields(plugin_root: Path, plugin_data: Path) -> None:
    init_data.ensure_initialized(plugin_root, plugin_data)

    rendered = session_context.render_session_context(plugin_root, plugin_data)

    assert "# Pet Persona" in rendered
    assert "拉爾夫" in rendered
    assert "沉穩、溫柔" in rendered
    assert "穩定" in rendered
    assert "不假裝知道" in rendered
    assert "remember-this" in rendered


def test_onboarding_directive_depends_on_marker(plugin_root: Path, plugin_data: Path) -> None:
    init_data.ensure_initialized(plugin_root, plugin_data)

    assert "# First-time setup" in session_context.render_session_context(plugin_root, plugin_data)

    (plugin_data / ".onboarding-pending").unlink()

    assert "# First-time setup" not in session_context.render_session_context(
        plugin_root, plugin_data
    )


def test_onboarding_directive_points_to_pet_skin_goal_flow(
    plugin_root: Path, plugin_data: Path
) -> None:
    init_data.ensure_initialized(plugin_root, plugin_data)

    rendered = session_context.render_session_context(plugin_root, plugin_data)

    assert "make-pet-skin" in rendered
    assert "/goal" in rendered
    assert "hatch-pet" in rendered
    assert "Restart Codex" in rendered


def test_output_order_is_persona_onboarding_facts_recent(
    plugin_root: Path, plugin_data: Path
) -> None:
    init_data.ensure_initialized(plugin_root, plugin_data)
    (plugin_data / "personal-facts" / "MEMORY.md").write_text(
        "# Personal facts\n\n- 使用者喜歡被叫做小雅。\n",
        encoding="utf-8",
    )
    (plugin_data / "recent" / "session.md").write_text(
        "上次聊到她想做一個安靜的工作同伴。",
        encoding="utf-8",
    )

    rendered = session_context.render_session_context(plugin_root, plugin_data)

    assert rendered.index("# Pet Persona") < rendered.index("# First-time setup")
    assert rendered.index("# First-time setup") < rendered.index("# Personal facts")
    assert rendered.index("# Personal facts") < rendered.index("# Recent talk")


def test_budget_overflow_drops_recent_talk_first(
    plugin_root: Path, plugin_data: Path
) -> None:
    init_data.ensure_initialized(plugin_root, plugin_data)
    (plugin_data / ".onboarding-pending").unlink()
    (plugin_data / "personal-facts" / "MEMORY.md").write_text(
        "# Personal facts\n\n- 使用者喜歡被叫做小雅。\n",
        encoding="utf-8",
    )
    (plugin_data / "recent" / "long.md").write_text(
        " ".join(["recent-memory"] * 400),
        encoding="utf-8",
    )

    rendered = session_context.render_session_context(
        plugin_root,
        plugin_data,
        config={"context": {"recent_limit": 3, "max_words": 130}},
    )

    assert "# Pet Persona" in rendered
    assert "# Personal facts" in rendered
    assert "# Recent talk" not in rendered
    assert "recent-memory" not in rendered
