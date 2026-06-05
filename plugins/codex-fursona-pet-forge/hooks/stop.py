import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import _common


CONTINUE = {"continue": True}
MIN_TRANSCRIPT_LINES = 3


def handle(
    raw_stdin: str,
    plugin_root: Path | str | None = None,
    plugin_data: Path | str | None = None,
    popen: Callable[..., object] = subprocess.Popen,
) -> dict[str, Any]:
    root = Path(plugin_root) if plugin_root is not None else _common.plugin_root()
    data_dir = Path(plugin_data) if plugin_data is not None else _common.plugin_data_dir()

    try:
        payload = _parse_payload(raw_stdin)
        config = _common.load_config(data_dir)
        skip, _reason = _common.should_skip(payload, config)
        if skip:
            return CONTINUE

        transcript = Path(str(payload.get("transcript_path") or ""))
        if not _has_enough_transcript(transcript):
            return CONTINUE

        turn_id = _safe_id(str(payload.get("turn_id") or payload.get("session_id") or "turn"))
        session_id = _safe_id(str(payload.get("session_id") or "session"))
        marker = data_dir / "markers" / f"{turn_id}.pending"
        if marker.exists():
            return CONTINUE

        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        _spawn_digest(root, data_dir, session_id, turn_id, transcript, popen)
    except Exception as exc:  # noqa: BLE001
        _log_error(data_dir, f"Stop failed: {exc}")

    return CONTINUE


def main() -> int:
    _common.emit_json(handle(sys.stdin.read()))
    return 0


def _spawn_digest(
    root: Path,
    data_dir: Path,
    session_id: str,
    turn_id: str,
    transcript: Path,
    popen: Callable[..., object],
) -> None:
    script = root / "scripts" / "digest_session.py"
    args = [
        sys.executable,
        str(script),
        "--plugin-data",
        str(data_dir),
        "--session-id",
        session_id,
        "--turn-id",
        turn_id,
        "--transcript",
        str(transcript),
    ]
    popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _parse_payload(raw: str) -> dict[str, Any]:
    if not raw.strip():
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    return value


def _has_enough_transcript(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False

    count = 0
    with path.open(encoding="utf-8") as handle_file:
        for line in handle_file:
            if line.strip():
                count += 1
            if count >= MIN_TRANSCRIPT_LINES:
                return True
    return False


def _safe_id(value: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in "._-" else "-" for character in value)
    cleaned = cleaned.strip("-")
    return cleaned or "unknown"


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
