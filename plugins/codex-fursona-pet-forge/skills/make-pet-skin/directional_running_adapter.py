#!/usr/bin/env python3
"""Adapt hatch-pet directional rows to three generated key poses."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


DIRECTIONAL_STATES = ("running-right", "running-left")
SEQUENCE = (0, 1, 2, 1, 0, 1, 2, 1)
SEQUENCE_LABEL = "12321232"
CELL_WIDTH = 192
CELL_HEIGHT = 208
PROMPT_MARKER = "Codex Fursona Pet Forge directional-running override"


class AdapterError(ValueError):
    pass


def prepare_run(run_dir: Path | str) -> dict[str, Any]:
    root = Path(run_dir)
    manifest_path = root / "imagegen-jobs.json"
    if not manifest_path.is_file():
        raise AdapterError(f"hatch-pet manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list):
        raise AdapterError("hatch-pet manifest must contain a jobs list")

    for state in DIRECTIONAL_STATES:
        guide_path = root / "references" / "layout-guides-3" / f"{state}.png"
        create_three_pose_guide(guide_path)
        for prompt_kind in ("rows", "row-retries"):
            prompt_path = root / "prompts" / prompt_kind / f"{state}.md"
            if not prompt_path.is_file():
                raise AdapterError(f"directional prompt not found: {prompt_path}")
            prompt = prompt_path.read_text(encoding="utf-8")
            prompt_path.write_text(adapt_prompt(prompt, state), encoding="utf-8")

        job = next(
            (candidate for candidate in jobs if candidate.get("id") == state),
            None,
        )
        if not isinstance(job, dict):
            raise AdapterError(f"directional job not found in manifest: {state}")
        inputs = job.get("input_images")
        if not isinstance(inputs, list):
            raise AdapterError(f"directional job has no input_images list: {state}")
        guide_input = next(
            (
                item
                for item in inputs
                if isinstance(item, dict)
                and "layout guide" in str(item.get("role", "")).lower()
            ),
            None,
        )
        if not isinstance(guide_input, dict):
            raise AdapterError(f"layout guide input not found for: {state}")
        guide_input["path"] = f"references/layout-guides-3/{state}.png"
        guide_input["role"] = (
            "layout guide for 3 key-pose slots; use for spacing only, "
            "do not copy guide lines"
        )

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "states": list(DIRECTIONAL_STATES),
        "source_pose_count": 3,
        "sequence": SEQUENCE_LABEL,
    }


def adapt_prompt(prompt: str, state: str) -> str:
    if PROMPT_MARKER in prompt:
        return prompt

    replacements = {
        "exactly 8 full-body frames": "exactly 3 full-body key poses",
        "8 invisible equal-width slots": "3 invisible equal-width key-pose slots",
        "across the 8 frames": "across the 3 key poses",
    }
    for old, new in replacements.items():
        prompt = prompt.replace(old, new)

    direction = "right" if state == "running-right" else "left"
    override = f"""

## {PROMPT_MARKER}

Generate exactly three separated key poses facing and travelling {direction}:

1. The character's left foot is forward.
2. The legs cross or pass under the body during weight transfer.
3. The character's right foot is forward.

For a non-biped, use three equivalent locomotion phases. Generate only these
three source poses. Do not generate 8 independently generated frames. The
local adapter will reuse them as `{SEQUENCE_LABEL}` after generation.
"""
    return prompt.rstrip() + override


def create_three_pose_guide(path: Path) -> None:
    image = Image.new("RGB", (CELL_WIDTH * 3, CELL_HEIGHT), "#f7f7f7")
    draw = ImageDraw.Draw(image)
    for index in range(3):
        left = index * CELL_WIDTH
        right = left + CELL_WIDTH - 1
        draw.rectangle((left, 0, right, CELL_HEIGHT - 1), outline="#111111", width=2)
        draw.rectangle(
            (left + 12, 10, right - 12, CELL_HEIGHT - 11),
            outline="#2f80ed",
            width=2,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def expand_state(run_dir: Path | str, state: str) -> dict[str, Any]:
    if state not in DIRECTIONAL_STATES:
        raise AdapterError(f"state must be directional: {state}")

    root = Path(run_dir)
    decoded_path = root / "decoded" / f"{state}.png"
    backup_path = root / "decoded" / "key-poses" / f"{state}.png"
    if backup_path.is_file():
        source_path = backup_path
    else:
        if not decoded_path.is_file():
            raise AdapterError(f"generated three-pose strip not found: {decoded_path}")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(decoded_path, backup_path)
        source_path = backup_path

    with Image.open(source_path) as opened:
        source = opened.copy()

    boundaries = [round(index * source.width / 3) for index in range(4)]
    raw_poses = [
        source.crop((boundaries[index], 0, boundaries[index + 1], source.height))
        for index in range(3)
    ]
    slot_width = min(pose.width for pose in raw_poses)
    poses = []
    for pose in raw_poses:
        left = (pose.width - slot_width) // 2
        poses.append(pose.crop((left, 0, left + slot_width, source.height)))
    expanded = Image.new(source.mode, (slot_width * 8, source.height))
    for output_index, pose_index in enumerate(SEQUENCE):
        expanded.paste(poses[pose_index], (output_index * slot_width, 0))

    decoded_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = decoded_path.with_name(f".{decoded_path.stem}.expanded.png")
    expanded.save(temporary_path)
    temporary_path.replace(decoded_path)
    verify_expanded_strip(decoded_path, poses)

    result = {
        "state": state,
        "source": str(backup_path),
        "output": str(decoded_path),
        "source_pose_count": 3,
        "output_frame_count": 8,
        "sequence": SEQUENCE_LABEL,
        "repeated_poses_pixel_identical": True,
    }
    write_report(root, state, result)
    return result


def verify_expanded_strip(path: Path, poses: list[Image.Image]) -> None:
    with Image.open(path) as opened:
        output = opened.copy()
    slot_width = output.width // 8
    for output_index, pose_index in enumerate(SEQUENCE):
        actual = output.crop(
            (output_index * slot_width, 0, (output_index + 1) * slot_width, output.height)
        )
        expected = poses[pose_index]
        if actual.mode != expected.mode or actual.size != expected.size:
            raise AdapterError(f"expanded frame shape mismatch at index {output_index}")
        if actual.tobytes() != expected.tobytes():
            raise AdapterError(f"expanded frame pixels mismatch at index {output_index}")


def write_report(root: Path, state: str, result: dict[str, Any]) -> None:
    report_path = root / "qa" / "directional-running-adapter.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {}
    if report_path.is_file():
        loaded = json.loads(report_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            report = loaded
    report[state] = result
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare-run")
    prepare_parser.add_argument("--run-dir", required=True)
    expand_parser = subparsers.add_parser("expand")
    expand_parser.add_argument("--run-dir", required=True)
    expand_parser.add_argument("--state", choices=DIRECTIONAL_STATES, required=True)
    args = parser.parse_args()

    try:
        if args.command == "prepare-run":
            result = prepare_run(args.run_dir)
        else:
            result = expand_state(args.run_dir, args.state)
    except (AdapterError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
