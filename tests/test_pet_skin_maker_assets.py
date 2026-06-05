from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
PLUGIN_ROOT = REPO_ROOT / "plugins" / "codex-fursona-pet-forge"
SKILLS_ROOT = PLUGIN_ROOT / "skills"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pet_skin_reference_docs_exist_and_cover_goal_mode():
    required_docs = {
        "pet-skin-workflow.md": [
            "/goal",
            "hatch-pet",
            "preflight",
            "python3 -m pip install -e .",
            "Pillow",
            "one-shot goal mode",
            "supervised mode",
            "framewise mirroring",
            "structural validation",
            "visual acceptance",
            "semantic anatomy",
            "duplicate tails",
            "human_review_items",
            "manual_frame_repairs",
        ],
        "pet-skin-action-defaults.md": [
            "idle",
            "running-right",
            "running-left",
            "waving",
            "jumping",
            "failed",
            "waiting",
            "running",
            "review",
        ],
        "pet-skin-quality-checklist.md": [
            "transparent 192x208 animated GIF",
            "raw slot overlay",
            "source-art clipping",
            "framewise mirror",
            "low-alpha",
            "key-like green",
            "structural validation",
            "visual acceptance",
            "semantic anatomy",
            "duplicate tails",
            "magenta",
            "zoomed body-part crop",
            "user approval",
        ],
        "pet-generation-handoff.md": [
            "run directory",
            "canonical base",
            "accepted rows",
            "next action",
            "copyable",
        ],
        "pet-package-spec.md": [
            "pet.json",
            "spritesheet.webp",
            "8 columns x 9 rows",
            "192 x 208",
            "official docs",
        ],
    }

    for filename, required_phrases in required_docs.items():
        content = read(DOCS_ROOT / filename)
        lower_content = content.lower()
        for phrase in required_phrases:
            assert phrase.lower() in lower_content, f"{filename} should mention {phrase}"


def test_make_pet_skin_skill_routes_goal_mode_and_dependency_preflight():
    content = read(SKILLS_ROOT / "make-pet-skin" / "SKILL.md")

    assert content.startswith("---\n")
    assert "name: make-pet-skin" in content
    assert "description:" in content
    assert "/goal" in content
    assert "hatch-pet" in content
    assert "preflight" in content
    assert "python3 -m pip install -e ." in content
    assert "PIL" in content
    assert "Restart Codex" in content
    assert "pet-skin-workflow.md" in content
    assert "pet-skin-action-defaults.md" in content
    assert "pet-skin-quality-checklist.md" in content
    assert "structural validation status" in content
    assert "repaired rows" in content
    assert "human review" in content
    assert "manual frame repairs" in content
    assert "semantic anatomy" in content
    assert "duplicate tails" in content
    assert "zoomed body-part crop" in content


def test_pet_generation_handoff_skill_is_structured_for_long_goal_runs():
    content = read(SKILLS_ROOT / "pet-generation-handoff" / "SKILL.md")

    assert content.startswith("---\n")
    assert "name: pet-generation-handoff" in content
    assert "description:" in content
    assert "copyable" in content
    assert "run directory" in content
    assert "accepted rows" in content
    assert "failed or risky rows" in content
    assert "next action" in content
