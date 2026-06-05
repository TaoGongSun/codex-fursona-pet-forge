import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import _common


SCRIPTS_DIR = _common.plugin_root() / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import init_data  # noqa: E402
import session_context  # noqa: E402


CONTINUE = {"continue": True}


def handle(
    raw_stdin: str,
    plugin_root: Path | str | None = None,
    plugin_data: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(plugin_root) if plugin_root is not None else _common.plugin_root()
    data_dir = Path(plugin_data) if plugin_data is not None else _common.plugin_data_dir()

    try:
        payload = _parse_payload(raw_stdin)
    except ValueError as exc:
        _log_error(data_dir, f"SessionStart payload parse failed: {exc}")
        return CONTINUE

    try:
        config = _common.load_config(data_dir)
        skip, _reason = _common.should_skip(payload, config)
        if skip:
            return CONTINUE

        init_data.ensure_initialized(root, data_dir)
        config = _common.load_config(data_dir)
        additional_context = session_context.render_session_context(root, data_dir, config)
    except Exception as exc:  # noqa: BLE001
        _log_error(data_dir, f"SessionStart failed: {exc}")
        return CONTINUE

    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        },
    }


def main() -> int:
    _common.emit_json(handle(sys.stdin.read()))
    return 0


def _parse_payload(raw: str) -> dict[str, Any]:
    if not raw.strip():
        return {}

    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    return value


def _log_error(data_dir: Path, message: str) -> None:
    try:
        log_dir = data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
        with (log_dir / "error.log").open("a", encoding="utf-8") as handle_file:
            handle_file.write(f"{timestamp} {message}\n")
    except OSError:
        return


if __name__ == "__main__":
    raise SystemExit(main())
