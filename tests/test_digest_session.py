import json
from datetime import UTC, datetime
from pathlib import Path

import digest_session


def test_parser_handles_current_transcript_jsonl_samples(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        "\n".join(
            [
                json.dumps({"type": "user_message", "message": "我喜歡被叫小雅。"}),
                json.dumps(
                    {
                        "type": "response_item",
                        "item": {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "我記住了，小雅。"}],
                        },
                    }
                ),
                json.dumps(
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": "也請慢慢來。"}],
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    messages = digest_session.parse_transcript(transcript)

    assert messages == [
        digest_session.Message("user", "我喜歡被叫小雅。"),
        digest_session.Message("assistant", "我記住了，小雅。"),
        digest_session.Message("user", "也請慢慢來。"),
    ]


def test_parse_failure_logs_and_exits_zero(plugin_data: Path, tmp_path: Path) -> None:
    transcript = tmp_path / "bad.jsonl"
    transcript.write_text("{not json\n", encoding="utf-8")

    result = digest_session.digest(
        plugin_data,
        session_id="session-1",
        turn_id="turn-1",
        transcript_path=transcript,
    )

    assert result == 0
    assert "parse failed" in (plugin_data / "logs" / "digest.log").read_text(encoding="utf-8")


def test_summary_file_lands_in_recent_with_timestamp_and_session(
    plugin_data: Path, tmp_path: Path
) -> None:
    transcript = write_conversation(tmp_path)

    digest_session.digest(
        plugin_data,
        session_id="session-1",
        turn_id="turn-1",
        transcript_path=transcript,
        now=datetime(2026, 5, 24, 12, 30, tzinfo=UTC),
    )

    summary = plugin_data / "recent" / "20260524T123000Z-session-1.md"
    assert summary.exists()
    assert "我喜歡被叫小雅" in summary.read_text(encoding="utf-8")


def test_recent_retention_keeps_three_newest_summaries(
    plugin_data: Path, tmp_path: Path
) -> None:
    recent = plugin_data / "recent"
    recent.mkdir()
    for index in range(3):
        path = recent / f"old-{index}.md"
        path.write_text("old", encoding="utf-8")
    transcript = write_conversation(tmp_path)

    digest_session.digest(
        plugin_data,
        session_id="session-4",
        turn_id="turn-4",
        transcript_path=transcript,
        now=datetime(2026, 5, 24, 12, 30, tzinfo=UTC),
        recent_limit=3,
    )

    assert len(list(recent.glob("*.md"))) == 3
    assert (recent / "20260524T123000Z-session-4.md").exists()


def write_conversation(tmp_path: Path) -> Path:
    transcript = tmp_path / "transcript.jsonl"
    lines = [
        {"type": "user_message", "message": "我喜歡被叫小雅。"},
        {"type": "assistant_message", "message": "好，我會這樣稱呼你。"},
        {"type": "user_message", "message": "工作時請慢慢來。"},
    ]
    transcript.write_text(
        "\n".join(json.dumps(line, ensure_ascii=False) for line in lines) + "\n",
        encoding="utf-8",
    )
    return transcript
