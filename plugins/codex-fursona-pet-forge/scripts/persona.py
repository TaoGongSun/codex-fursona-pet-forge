from pathlib import Path
from typing import Any

import simple_yaml


class PersonaError(ValueError):
    pass


REQUIRED_STRING_FIELDS = ["name", "species", "background", "memory_directive"]
MAX_TEXT_LENGTHS = {
    "name": 80,
    "species": 120,
    "background": 2000,
    "voice.tone": 500,
    "addressing.user_term": 80,
    "addressing.self_term": 80,
    "memory_directive": 2000,
}


def load_persona(path: Path | str) -> dict[str, Any]:
    persona_path = Path(path)
    try:
        loaded = simple_yaml.load(persona_path.read_text(encoding="utf-8"))
    except simple_yaml.SimpleYAMLError as exc:
        raise PersonaError(f"無法解析 persona YAML：{exc}") from exc
    except OSError as exc:
        raise PersonaError(f"無法讀取 persona YAML：{persona_path}") from exc

    return validate_persona(loaded)


def validate_persona(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PersonaError("persona YAML 必須是 mapping")

    for field in REQUIRED_STRING_FIELDS:
        _require_string(value, field)

    voice = _require_mapping(value, "voice")
    _require_string(voice, "tone", "voice.tone")
    _validate_string_list(voice.get("examples", []), "voice.examples")

    addressing = _require_mapping(value, "addressing")
    _require_string(addressing, "user_term", "addressing.user_term")
    _require_string(addressing, "self_term", "addressing.self_term")

    _validate_string_list(value.get("values", []), "values")
    _validate_string_list(value.get("taboos", []), "taboos")

    onboarding = value.get("onboarding")
    if onboarding is not None and not isinstance(onboarding, dict):
        raise PersonaError("欄位 onboarding 必須是 mapping")

    return value


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise PersonaError(f"缺少或無效欄位：{key}")
    return value


def _require_string(data: dict[str, Any], key: str, label: str | None = None) -> str:
    field = label or key
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PersonaError(f"缺少或無效欄位：{field}")

    _validate_text(field, value)
    return value


def _validate_string_list(value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise PersonaError(f"欄位 {field} 必須是 list")

    for index, item in enumerate(value):
        label = f"{field}[{index}]"
        if not isinstance(item, str) or not item.strip():
            raise PersonaError(f"缺少或無效欄位：{label}")
        _validate_text(label, item)


def _validate_text(field: str, value: str) -> None:
    limit = MAX_TEXT_LENGTHS.get(field, 500)
    if len(value) > limit:
        raise PersonaError(f"欄位 {field} 太長，最多 {limit} 字")

    if any(_is_forbidden_control(character) for character in value):
        raise PersonaError(f"欄位 {field} 含有不允許的控制字元")


def _is_forbidden_control(character: str) -> bool:
    return ord(character) < 32 and character not in {"\n", "\t", "\r"}
