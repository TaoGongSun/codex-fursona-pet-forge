from pathlib import Path
from typing import Any

from persona import load_persona
import simple_yaml


DEFAULT_CONTEXT = {
    "recent_limit": 3,
    "max_words": 1200,
}


def render_session_context(
    plugin_root: Path | str,
    plugin_data: Path | str,
    config: dict[str, Any] | None = None,
) -> str:
    root = Path(plugin_root)
    data_dir = Path(plugin_data)
    settings = config or _load_config(data_dir)
    context_settings = _context_settings(settings)

    sections = [
        _render_persona(root, data_dir),
    ]

    onboarding = _read_onboarding(root, data_dir)
    if onboarding:
        sections.append(onboarding)

    facts = _read_personal_facts(data_dir)
    if facts:
        sections.append(facts)

    recent = _read_recent_talk(data_dir, context_settings["recent_limit"])
    if recent:
        sections.append(recent)

    return _apply_budget(sections, has_recent=bool(recent), max_words=context_settings["max_words"])


def _render_persona(root: Path, data_dir: Path) -> str:
    data = load_persona(data_dir / "persona.yaml")
    template = (root / "prompts" / "persona-context.md").read_text(encoding="utf-8")
    addressing = data["addressing"]
    return template.format(
        name=data["name"],
        species=data["species"],
        voice_tone=data["voice"]["tone"],
        user_term=addressing["user_term"],
        self_term=addressing["self_term"],
        background=data["background"].strip(),
        values=_format_list(data.get("values", [])),
        taboos=_format_list(data.get("taboos", [])),
        memory_directive=data["memory_directive"].strip(),
    ).strip()


def _read_onboarding(root: Path, data_dir: Path) -> str:
    if not (data_dir / ".onboarding-pending").exists():
        return ""
    return (root / "prompts" / "onboarding-directive.md").read_text(encoding="utf-8").strip()


def _read_personal_facts(data_dir: Path) -> str:
    memory = data_dir / "personal-facts" / "MEMORY.md"
    if not memory.exists():
        return ""
    content = memory.read_text(encoding="utf-8").strip()
    return content if content else ""


def _read_recent_talk(data_dir: Path, limit: int) -> str:
    recent_dir = data_dir / "recent"
    if not recent_dir.exists():
        return ""

    files = sorted(recent_dir.glob("*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    entries = [
        path.read_text(encoding="utf-8").strip()
        for path in files[:limit]
        if path.read_text(encoding="utf-8").strip()
    ]
    if not entries:
        return ""

    return "# Recent talk\n\n" + "\n\n---\n\n".join(entries)


def _apply_budget(sections: list[str], has_recent: bool, max_words: int) -> str:
    if _word_count(_join(sections)) <= max_words:
        return _join(sections)

    if has_recent and len(sections) > 1:
        without_recent = sections[:-1]
        if _word_count(_join(without_recent)) <= max_words:
            return _join(without_recent)
        sections = without_recent

    if len(sections) >= 3 and _word_count(_join(sections)) > max_words:
        sections[2] = _truncate_words(sections[2], max_words // 4)

    return _join(sections)


def _context_settings(config: dict[str, Any]) -> dict[str, int]:
    context = config.get("context", {}) if isinstance(config, dict) else {}
    if not isinstance(context, dict):
        context = {}
    return {
        "recent_limit": int(context.get("recent_limit", DEFAULT_CONTEXT["recent_limit"])),
        "max_words": int(context.get("max_words", DEFAULT_CONTEXT["max_words"])),
    }


def _load_config(data_dir: Path) -> dict[str, Any]:
    config_path = data_dir / "config.yaml"
    if not config_path.exists():
        return {}

    loaded = simple_yaml.load(config_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _format_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _join(sections: list[str]) -> str:
    return "\n\n".join(section.strip() for section in sections if section.strip()) + "\n"


def _word_count(value: str) -> int:
    return len(value.split())


def _truncate_words(value: str, limit: int) -> str:
    words = value.split()
    if len(words) <= limit:
        return value
    return " ".join(words[:limit]).rstrip() + "\n\n[Personal facts truncated by budget]\n"
