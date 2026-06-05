import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_RECENT_LIMIT = 3


@dataclass(frozen=True)
class Message:
    role: str
    text: str


def parse_transcript(path: Path | str) -> list[Message]:
    messages: list[Message] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"parse failed at line {line_number}: {exc}") from exc

            message = _message_from_record(record)
            if message:
                messages.append(message)

    return messages


def digest(
    plugin_data: Path | str,
    session_id: str,
    turn_id: str,
    transcript_path: Path | str,
    now: datetime | None = None,
    recent_limit: int = DEFAULT_RECENT_LIMIT,
) -> int:
    data_dir = Path(plugin_data)
    try:
        messages = parse_transcript(transcript_path)
    except (OSError, ValueError) as exc:
        _log(data_dir, f"parse failed: {exc}")
        return 0

    if len(messages) < 3:
        _remove_marker(data_dir, _safe_id(turn_id))
        return 0

    timestamp = (now or datetime.now(UTC)).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_session = _safe_id(session_id)
    recent_dir = data_dir / "recent"
    recent_dir.mkdir(parents=True, exist_ok=True)
    summary_path = recent_dir / f"{timestamp}-{safe_session}.md"
    summary_path.write_text(
        _render_summary(session_id=safe_session, messages=messages),
        encoding="utf-8",
    )
    _remove_marker(data_dir, _safe_id(turn_id))
    _enforce_recent_retention(recent_dir, recent_limit)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-data", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--transcript", required=True)
    args = parser.parse_args(argv)
    return digest(args.plugin_data, args.session_id, args.turn_id, args.transcript)


def _message_from_record(record: Any) -> Message | None:
    if not isinstance(record, dict):
        return None

    candidates = [record]
    for key in ["item", "message", "payload"]:
        nested = record.get(key)
        if isinstance(nested, dict):
            candidates.append(nested)

    for candidate in candidates:
        role = _role_from_record(candidate)
        text = _text_from_record(candidate)
        if role and text:
            return Message(role, text)

    if record.get("type") == "user_message" and isinstance(record.get("message"), str):
        return Message("user", record["message"].strip())
    if record.get("type") == "assistant_message" and isinstance(record.get("message"), str):
        return Message("assistant", record["message"].strip())

    return None


def _role_from_record(record: dict[str, Any]) -> str:
    role = record.get("role")
    if isinstance(role, str) and role in {"user", "assistant"}:
        return role

    record_type = record.get("type")
    if record_type == "user_message":
        return "user"
    if record_type == "assistant_message":
        return "assistant"
    return ""


def _text_from_record(record: dict[str, Any]) -> str:
    message = record.get("message")
    if isinstance(message, str):
        return message.strip()

    content = record.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        pieces = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str) and text.strip():
                    pieces.append(text.strip())
            elif isinstance(item, str) and item.strip():
                pieces.append(item.strip())
        return "\n".join(pieces).strip()

    text = record.get("text")
    return text.strip() if isinstance(text, str) else ""


def _render_summary(session_id: str, messages: list[Message]) -> str:
    user_notes = [message.text for message in messages if message.role == "user"]
    assistant_notes = [message.text for message in messages if message.role == "assistant"]
    lines = [
        "# Recent talk",
        "",
        f"- Session: {session_id}",
        f"- 使用者談到：{_join_notes(user_notes)}",
    ]
    if assistant_notes:
        lines.append(f"- 助手回應：{_join_notes(assistant_notes)}")
    return "\n".join(lines).rstrip() + "\n"


def _join_notes(notes: list[str]) -> str:
    return " / ".join(note.replace("\n", " ").strip() for note in notes[:3] if note.strip())


def _enforce_recent_retention(recent_dir: Path, limit: int) -> None:
    files = sorted(
        recent_dir.glob("*.md"),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )
    for path in files[limit:]:
        path.unlink(missing_ok=True)


def _remove_marker(data_dir: Path, turn_id: str) -> None:
    marker = data_dir / "markers" / f"{turn_id}.pending"
    marker.unlink(missing_ok=True)


def _safe_id(value: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in "._-" else "-" for character in value)
    cleaned = cleaned.strip("-")
    return cleaned or "unknown"


def _log(data_dir: Path, message: str) -> None:
    try:
        log_dir = data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
        with (log_dir / "digest.log").open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} {message}\n")
    except OSError:
        return


if __name__ == "__main__":
    raise SystemExit(main())
