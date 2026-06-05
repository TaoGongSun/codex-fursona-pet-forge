import os
import tomllib
from pathlib import Path
from typing import Any


PLUGIN_NAME = "codex-fursona-pet-forge"
LEGACY_PLUGIN_NAME = "-".join(("codex", "pet", "persona"))


def codex_home() -> Path:
    value = os.environ.get("CODEX_HOME")
    if value:
        return Path(value).expanduser().resolve()
    return Path.home() / ".codex"


def plugin_data_dir(plugin_name: str = PLUGIN_NAME) -> Path:
    value = os.environ.get("PLUGIN_DATA")
    if value:
        return Path(value).expanduser().resolve()

    home = codex_home()
    managed = _managed_plugin_data_dir(home, plugin_name)
    if managed:
        return managed

    if plugin_name == PLUGIN_NAME:
        legacy_managed = _managed_plugin_data_dir(home, LEGACY_PLUGIN_NAME)
        if legacy_managed:
            return legacy_managed

        legacy = legacy_plugin_data_dir(LEGACY_PLUGIN_NAME)
        if legacy.exists():
            return legacy

    return home / "plugins" / plugin_name / "data"


def legacy_plugin_data_dir(plugin_name: str = PLUGIN_NAME) -> Path:
    return codex_home() / "plugins" / plugin_name / "data"


def _managed_plugin_data_dir(home: Path, plugin_name: str) -> Path | None:
    marketplace = _enabled_marketplace(home / "config.toml", plugin_name)
    if marketplace:
        return home / "plugins" / "data" / f"{plugin_name}-{marketplace}"

    data_root = home / "plugins" / "data"
    if not data_root.exists():
        return None

    candidates = sorted(data_root.glob(f"{plugin_name}-*"))
    return candidates[0] if len(candidates) == 1 else None


def _enabled_marketplace(config_path: Path, plugin_name: str) -> str:
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return ""

    plugins = config.get("plugins")
    if not isinstance(plugins, dict):
        return ""

    marketplaces = [
        selector.split("@", 1)[1]
        for selector, settings in plugins.items()
        if _is_enabled_plugin(selector, settings, plugin_name)
    ]
    return marketplaces[0] if len(marketplaces) == 1 else ""


def _is_enabled_plugin(selector: str, settings: Any, plugin_name: str) -> bool:
    if not selector.startswith(f"{plugin_name}@"):
        return False
    if not isinstance(settings, dict):
        return False
    return settings.get("enabled") is True
