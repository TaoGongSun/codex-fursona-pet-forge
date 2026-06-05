import subprocess
from pathlib import Path

import pytest

import stop


def test_stop_returns_json_output(plugin_root: Path, plugin_data: Path, tmp_path: Path) -> None:
    transcript = write_transcript(tmp_path, lines=1)

    result = stop.handle(
        payload(transcript),
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        popen=fail_if_called,
    )

    assert result == {"continue": True}


def test_short_transcript_skips_digest(plugin_root: Path, plugin_data: Path, tmp_path: Path) -> None:
    transcript = write_transcript(tmp_path, lines=2)

    stop.handle(
        payload(transcript),
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        popen=fail_if_called,
    )

    assert not (plugin_data / "markers" / "turn-1.pending").exists()


def test_duplicate_turn_marker_skips_digest(
    plugin_root: Path, plugin_data: Path, tmp_path: Path
) -> None:
    transcript = write_transcript(tmp_path, lines=3)
    marker = plugin_data / "markers" / "turn-1.pending"
    marker.parent.mkdir(parents=True)
    marker.write_text("already queued", encoding="utf-8")

    stop.handle(
        payload(transcript),
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        popen=fail_if_called,
    )

    assert marker.read_text(encoding="utf-8") == "already queued"


def test_skip_path_returns_quickly_without_marker(
    plugin_root: Path, plugin_data: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CODEX_PET_DISABLE", "1")
    transcript = write_transcript(tmp_path, lines=3)

    stop.handle(
        payload(transcript),
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        popen=fail_if_called,
    )

    assert not (plugin_data / "markers").exists()


def test_valid_payload_spawns_digest_with_sanitized_args(
    plugin_root: Path, plugin_data: Path, tmp_path: Path
) -> None:
    transcript = write_transcript(tmp_path, lines=3)
    calls: list[list[str]] = []

    def capture(args: list[str], **_kwargs: object) -> object:
        calls.append(args)
        return object()

    stop.handle(
        payload(transcript, session_id="session/../x", turn_id="turn:1"),
        plugin_root=plugin_root,
        plugin_data=plugin_data,
        popen=capture,
    )

    assert (plugin_data / "markers" / "turn-1.pending").exists()
    assert calls
    args = calls[0]
    assert str(plugin_root / "scripts" / "digest_session.py") in args
    assert "--session-id" in args
    assert "session-..-x" in args
    assert "--turn-id" in args
    assert "turn-1" in args
    assert all(isinstance(arg, str) for arg in args)


def payload(transcript: Path, session_id: str = "session-1", turn_id: str = "turn-1") -> str:
    return (
        "{"
        f'"session_id": "{session_id}", '
        f'"turn_id": "{turn_id}", '
        f'"transcript_path": "{transcript}", '
        '"last_assistant_message": "done"'
        "}"
    )


def write_transcript(tmp_path: Path, lines: int) -> Path:
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(["{}"] * lines) + "\n", encoding="utf-8")
    return path


def fail_if_called(*_args: object, **_kwargs: object) -> subprocess.Popen[bytes]:
    raise AssertionError("不應啟動 digest subprocess")
