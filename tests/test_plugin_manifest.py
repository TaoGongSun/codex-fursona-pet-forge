import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_ROOT = REPO_ROOT / "plugins" / "codex-fursona-pet-forge"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
HOOKS_PATH = PLUGIN_ROOT / "hooks" / "hooks.json"
RALF_PACKAGE_PATH = PLUGIN_ROOT / "assets" / "sprites" / "ralf" / "package" / "ralf"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_marketplace_manifest_references_local_plugin_path():
    marketplace = load_json(MARKETPLACE_PATH)

    assert marketplace["name"] == "codex-fursona-local"
    plugin = marketplace["plugins"][0]
    assert plugin["name"] == "codex-fursona-pet-forge"
    assert plugin["source"] == {
        "source": "local",
        "path": "./plugins/codex-fursona-pet-forge",
    }
    assert (REPO_ROOT / plugin["source"]["path"]).exists()


def test_plugin_manifest_references_existing_skills_and_hooks():
    manifest = load_json(PLUGIN_MANIFEST_PATH)
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    base_version = manifest["version"].split("+", 1)[0]

    assert manifest["name"] == "codex-fursona-pet-forge"
    assert base_version == "0.2.7"
    assert base_version == project["project"]["version"]
    if "+" in manifest["version"]:
        assert manifest["version"].startswith(f"{base_version}+codex.")
    assert manifest["skills"] == "./skills/"
    assert manifest["hooks"] == "./hooks/hooks.json"
    assert (PLUGIN_ROOT / manifest["skills"]).exists()
    assert (PLUGIN_ROOT / manifest["hooks"]).exists()


def test_plugin_skills_have_discovery_frontmatter():
    manifest = load_json(PLUGIN_MANIFEST_PATH)
    skills_root = PLUGIN_ROOT / manifest["skills"]

    skill_files = sorted(skills_root.glob("*/SKILL.md"))

    assert [path.parent.name for path in skill_files] == [
        "make-pet-skin",
        "pet-generation-handoff",
        "remember-this",
        "setup-action",
        "stretch-reminder",
    ]
    for path in skill_files:
        content = path.read_text(encoding="utf-8")
        assert content.startswith("---\n"), f"{path} must start with YAML frontmatter"
        _, frontmatter, _ = content.split("---", 2)
        lines = {
            key.strip(): value.strip()
            for line in frontmatter.splitlines()
            if ":" in line
            for key, value in [line.split(":", 1)]
        }
        assert lines.get("name") == path.parent.name
        assert lines.get("description")


def test_hooks_manifest_declares_session_start_and_stop_commands():
    hooks = load_json(HOOKS_PATH)["hooks"]

    assert set(hooks) == {"SessionStart", "Stop"}
    session_start_command = hooks["SessionStart"][0]["hooks"][0]["command"]
    stop_command = hooks["Stop"][0]["hooks"][0]["command"]
    assert session_start_command == "python3 ${PLUGIN_ROOT}/hooks/session_start.py"
    assert stop_command == "python3 ${PLUGIN_ROOT}/hooks/stop.py"


def test_ralf_sprite_package_is_bundled_for_installation():
    pet_json_path = RALF_PACKAGE_PATH / "pet.json"
    spritesheet_path = RALF_PACKAGE_PATH / "spritesheet.webp"

    pet = load_json(pet_json_path)

    assert pet["id"] == "ralf"
    assert pet["spritesheetPath"] == "spritesheet.webp"
    assert spritesheet_path.exists()
    assert _webp_dimensions(spritesheet_path) == (1536, 1872)


def _webp_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WEBP"

    offset = 12
    while offset + 8 <= len(data):
        chunk_type = data[offset : offset + 4]
        chunk_size = int.from_bytes(data[offset + 4 : offset + 8], "little")
        payload = data[offset + 8 : offset + 8 + chunk_size]
        if chunk_type == b"VP8X":
            width = int.from_bytes(payload[4:7], "little") + 1
            height = int.from_bytes(payload[7:10], "little") + 1
            return width, height
        if chunk_type == b"VP8L":
            bits = int.from_bytes(payload[1:5], "little")
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
            return width, height
        if chunk_type == b"VP8 ":
            width = int.from_bytes(payload[6:8], "little") & 0x3FFF
            height = int.from_bytes(payload[8:10], "little") & 0x3FFF
            return width, height
        offset += 8 + chunk_size + (chunk_size % 2)
    raise AssertionError(f"Could not read WebP dimensions from {path}")
