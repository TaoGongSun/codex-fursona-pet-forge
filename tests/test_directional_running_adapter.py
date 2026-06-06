import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

import directional_running_adapter as adapter


def test_prepare_run_replaces_directional_jobs_with_three_pose_contract(
    tmp_path: Path,
) -> None:
    run_dir = make_run(tmp_path)

    adapter.prepare_run(run_dir)

    for state in adapter.DIRECTIONAL_STATES:
        prompt = (run_dir / f"prompts/rows/{state}.md").read_text(encoding="utf-8")
        retry = (run_dir / f"prompts/row-retries/{state}.md").read_text(
            encoding="utf-8"
        )
        assert "exactly 3 full-body key poses" in prompt
        assert "exactly 3 full-body key poses" in retry
        assert "12321232" in prompt
        assert "8 independently generated frames" in prompt

        guide = run_dir / f"references/layout-guides-3/{state}.png"
        with Image.open(guide) as image:
            assert image.size == (576, 208)

    manifest = json.loads(
        (run_dir / "imagegen-jobs.json").read_text(encoding="utf-8")
    )
    for state in adapter.DIRECTIONAL_STATES:
        job = next(job for job in manifest["jobs"] if job["id"] == state)
        guide_input = next(
            item for item in job["input_images"] if "layout guide" in item["role"]
        )
        assert guide_input["path"] == f"references/layout-guides-3/{state}.png"
        assert "3 key-pose slots" in guide_input["role"]


def test_expand_state_reuses_three_source_slots_as_12321232(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    decoded = run_dir / "decoded"
    decoded.mkdir(parents=True)
    source = decoded / "running-right.png"
    make_three_pose_strip(source)

    result = adapter.expand_state(run_dir, "running-right")

    assert result["sequence"] == "12321232"
    assert result["source_pose_count"] == 3
    assert result["output_frame_count"] == 8
    assert (run_dir / "decoded/key-poses/running-right.png").exists()

    with Image.open(source) as image:
        assert image.size == (8 * 12, 10)
        slots = [
            image.crop((index * 12, 0, (index + 1) * 12, 10)).tobytes()
            for index in range(8)
        ]
    assert slots == [slots[index] for index in (0, 1, 2, 1, 0, 1, 2, 1)]


def test_expand_state_rejects_non_directional_state(tmp_path: Path) -> None:
    with pytest.raises(adapter.AdapterError, match="directional"):
        adapter.expand_state(tmp_path, "idle")


def test_expand_state_normalizes_strip_width_not_divisible_by_three(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run"
    decoded = run_dir / "decoded"
    decoded.mkdir(parents=True)
    source = decoded / "running-right.png"
    Image.new("RGB", (38, 10), "magenta").save(source)

    adapter.expand_state(run_dir, "running-right")

    with Image.open(source) as image:
        assert image.width % 8 == 0


def make_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    for directory in ("prompts/rows", "prompts/row-retries"):
        (run_dir / directory).mkdir(parents=True)
    for state in adapter.DIRECTIONAL_STATES:
        text = (
            f"Create `{state}` with exactly 8 full-body frames. "
            "Output exactly 8 full-body frames in one left-to-right row. "
            "Treat the row as 8 invisible equal-width slots."
        )
        (run_dir / f"prompts/rows/{state}.md").write_text(text, encoding="utf-8")
        (run_dir / f"prompts/row-retries/{state}.md").write_text(
            text, encoding="utf-8"
        )
    manifest = {
        "jobs": [
            {
                "id": state,
                "input_images": [
                    {
                        "path": f"references/layout-guides/{state}.png",
                        "role": "layout guide for 8 frame slots",
                    }
                ],
            }
            for state in adapter.DIRECTIONAL_STATES
        ]
    }
    (run_dir / "imagegen-jobs.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return run_dir


def make_three_pose_strip(path: Path) -> None:
    image = Image.new("RGB", (36, 10), "white")
    draw = ImageDraw.Draw(image)
    for index, color in enumerate(("red", "green", "blue")):
        draw.rectangle((index * 12, 0, (index + 1) * 12 - 1, 9), fill=color)
        draw.point((index * 12 + index + 1, 2), fill="black")
    image.save(path)
