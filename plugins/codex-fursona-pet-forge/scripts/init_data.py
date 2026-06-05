import os
import re
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

from data_paths import LEGACY_PLUGIN_NAME, legacy_plugin_data_dir


DEFAULT_CONFIG: dict[str, Any] = {
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
DEFAULT_CONFIG_TEXT = """short_circuit:
  env_var: true
  cwd_marker: true
  full_auto: false
context:
  recent_limit: 3
  max_words: 1200
wellness:
  break_reminder:
    enabled: false
    interval_minutes: 50
    activity_minutes: 3
    timezone: local
    inactivity_threshold_minutes: 60
    max_unanswered_reminders: 2
    quiet_hours:
      enabled: true
      start: "22:00"
      end: "09:00"
    time_context:
      enabled: true
      style: gentle_guess
    tone: gentle
    last_started_at: ""
    last_user_interaction_at: ""
    last_reminder_at: ""
    unanswered_count: 0
    automation:
      kind: thread
      name: Codex Pet Break Reminder
"""

DEFAULT_MEMORY = """# Personal facts

目前還沒有已記住的個人事實。
"""
DEFAULT_LOCALE = "zh-TW"


def ensure_initialized(plugin_root: Path | str, plugin_data: Path | str) -> None:
    root = Path(plugin_root)
    data_dir = Path(plugin_data)
    persona_path = data_dir / "persona.yaml"
    config_path = data_dir / "config.yaml"
    memory_path = data_dir / "personal-facts" / "MEMORY.md"

    _ensure_directories(data_dir)
    _migrate_legacy_data(data_dir)

    first_initialization = (
        not persona_path.exists() and not config_path.exists() and not memory_path.exists()
    )

    if not persona_path.exists():
        default_persona = _default_persona_path(root)
        if not default_persona.exists():
            raise FileNotFoundError(f"找不到預設 persona：{default_persona}")
        shutil.copyfile(default_persona, persona_path)

    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
    else:
        ensure_config_defaults(data_dir)

    if not memory_path.exists():
        memory_path.write_text(DEFAULT_MEMORY, encoding="utf-8")

    if first_initialization:
        (data_dir / ".onboarding-pending").touch()


def ensure_config_defaults(plugin_data: Path | str) -> None:
    data_dir = Path(plugin_data)
    config_path = data_dir / "config.yaml"
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
        return

    try:
        loaded = _load_config(config_path)
    except ValueError:
        return

    merged = _merge_defaults(loaded, DEFAULT_CONFIG)
    if merged != loaded:
        config_path.write_text(_dump_yaml(merged), encoding="utf-8")


def _ensure_directories(data_dir: Path) -> None:
    for relative in ["personal-facts", "recent", "markers", "logs"]:
        (data_dir / relative).mkdir(parents=True, exist_ok=True)


def _default_persona_path(root: Path) -> Path:
    personas_dir = root / "personas"
    requested_locale = os.environ.get("CODEX_PET_LOCALE", DEFAULT_LOCALE).strip()
    locale = requested_locale or DEFAULT_LOCALE

    localized = personas_dir / f"default-ralf.{locale}.yaml"
    if localized.exists():
        return localized

    default_localized = personas_dir / f"default-ralf.{DEFAULT_LOCALE}.yaml"
    if default_localized.exists():
        return default_localized

    return personas_dir / "default-ralf.yaml"


def _migrate_legacy_data(data_dir: Path) -> None:
    primary_legacy_dir = legacy_plugin_data_dir()
    managed_root = primary_legacy_dir.parents[1] / "data"
    try:
        data_dir.resolve().relative_to(managed_root.resolve())
    except ValueError:
        return

    legacy_dirs = [primary_legacy_dir, legacy_plugin_data_dir(LEGACY_PLUGIN_NAME)]
    for legacy_dir in legacy_dirs:
        if legacy_dir == data_dir or not legacy_dir.exists():
            continue

        copied_facts = _copy_legacy_facts(legacy_dir, data_dir)
        if copied_facts:
            _rebuild_memory_index(data_dir / "personal-facts")

        legacy_marker = legacy_dir / ".onboarding-pending"
        target_marker = data_dir / ".onboarding-pending"
        if legacy_marker.exists():
            target_marker.touch(exist_ok=True)
        elif _has_legacy_state(legacy_dir):
            target_marker.unlink(missing_ok=True)


def _copy_legacy_facts(legacy_dir: Path, data_dir: Path) -> bool:
    legacy_facts = legacy_dir / "personal-facts"
    target_facts = data_dir / "personal-facts"
    if not legacy_facts.exists():
        return False

    copied = False
    for source in sorted(legacy_facts.glob("*.md")):
        if source.name == "MEMORY.md":
            continue
        target = target_facts / source.name
        if target.exists():
            continue
        shutil.copyfile(source, target)
        copied = True
    return copied


def _has_legacy_state(legacy_dir: Path) -> bool:
    fact_files = list((legacy_dir / "personal-facts").glob("*.md"))
    return any(path.name != "MEMORY.md" for path in fact_files) or any(
        (legacy_dir / name).exists() for name in ["persona.yaml", "config.yaml"]
    )


def _rebuild_memory_index(facts_dir: Path) -> None:
    grouped: dict[str, list[tuple[str, str]]] = {}

    for path in sorted(facts_dir.glob("*.md")):
        if path.name == "MEMORY.md":
            continue
        metadata, body = _read_fact(path)
        fact_type = str(metadata.get("type") or "general")
        grouped.setdefault(fact_type, []).append((path.name, _summary(body)))

    lines = ["# Personal facts", ""]
    if not grouped:
        lines.append("目前還沒有已記住的個人事實。")
    else:
        for fact_type in sorted(grouped):
            lines.extend([f"## {fact_type}", ""])
            for filename, summary in grouped[fact_type]:
                slug = filename.removesuffix(".md")
                lines.append(f"- [{slug}]({filename}) — {summary}")
            lines.append("")

    (facts_dir / "MEMORY.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _read_fact(path: Path) -> tuple[dict[str, str], str]:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    metadata = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, match.group(2).strip()


def _summary(body: str) -> str:
    for line in body.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return "未提供摘要"


def _load_config(config_path: Path) -> dict[str, Any]:
    import simple_yaml

    loaded = simple_yaml.load(config_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _merge_defaults(current: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(current)
    for key, default_value in defaults.items():
        current_value = merged.get(key)
        if isinstance(current_value, dict) and isinstance(default_value, dict):
            merged[key] = _merge_defaults(current_value, default_value)
        elif key not in merged:
            merged[key] = deepcopy(default_value)
    return merged


def _dump_yaml(value: dict[str, Any], indent: int = 0) -> str:
    lines: list[str] = []
    for key, item in value.items():
        prefix = " " * indent + f"{key}:"
        if isinstance(item, dict):
            lines.append(prefix)
            lines.append(_dump_yaml(item, indent + 2).rstrip())
        else:
            lines.append(f"{prefix} {_format_scalar(item)}")
    return "\n".join(lines).rstrip() + "\n"


def _format_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value == "":
        return '""'
    if isinstance(value, int):
        return str(value)

    text = str(value)
    if ":" in text or text.strip() != text:
        return '"' + text.replace('"', '\\"') + '"'
    return text
