import json
import os
import sys
from pathlib import Path
from typing import Any


PLUGIN_NAME = "codex-fursona-pet-forge"
DISABLE_MARKER = ".codex-pet-disable"


def plugin_root() -> Path:
    value = os.environ.get("PLUGIN_ROOT")
    if value:
        return Path(value).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def codex_home() -> Path:
    _add_scripts_path()
    from data_paths import codex_home as resolve_codex_home

    return resolve_codex_home()


def plugin_data_dir() -> Path:
    _add_scripts_path()
    from data_paths import plugin_data_dir as resolve_plugin_data_dir

    return resolve_plugin_data_dir(PLUGIN_NAME)


def load_config(data_dir: Path | None = None) -> dict[str, Any]:
    config_path = (data_dir or plugin_data_dir()) / "config.yaml"
    if not config_path.exists():
        return {}

    try:
        loaded = _load_simple_yaml(config_path.read_text(encoding="utf-8"))
    except ValueError:
        return {}

    return loaded if isinstance(loaded, dict) else {}


def should_skip(payload: dict[str, Any], config: dict[str, Any] | None = None) -> tuple[bool, str]:
    settings = config or {}
    short_circuit = settings.get("short_circuit", {})
    if not isinstance(short_circuit, dict):
        short_circuit = {}

    if short_circuit.get("env_var", True) and os.environ.get("CODEX_PET_DISABLE") == "1":
        return True, "env-var"

    if short_circuit.get("cwd_marker", True) and _has_cwd_marker(payload.get("cwd")):
        return True, "cwd-marker"

    if short_circuit.get("full_auto", False) and payload.get("permission_mode") in {
        "full-auto",
        "full_auto",
    }:
        return True, "full-auto"

    return False, ""


def read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    value = json.loads(raw)
    return value if isinstance(value, dict) else {}


def emit_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def _has_cwd_marker(cwd: Any) -> bool:
    if not cwd:
        return False

    try:
        current = Path(str(cwd)).expanduser().resolve()
    except OSError:
        return False

    candidates = [current, *current.parents]
    return any((candidate / DISABLE_MARKER).exists() for candidate in candidates)


def _load_simple_yaml(text: str) -> dict[str, Any]:
    _add_scripts_path()

    import simple_yaml

    return simple_yaml.load(text)


def _add_scripts_path() -> None:
    scripts_dir = plugin_root() / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
