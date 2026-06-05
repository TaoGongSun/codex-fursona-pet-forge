from pathlib import Path

import pytest

import persona


def test_required_fields_are_enforced(tmp_path: Path) -> None:
    path = tmp_path / "persona.yaml"
    path.write_text(
        """
name: 拉爾夫
species: 德國牧羊犬獸人
background: 住在 Codex 裡的工作夥伴
voice:
  tone: 溫柔
addressing:
  user_term: 你
  self_term: 我
""",
        encoding="utf-8",
    )

    with pytest.raises(persona.PersonaError, match="memory_directive"):
        persona.load_persona(path)


def test_malformed_yaml_fails_without_side_effects(tmp_path: Path) -> None:
    path = tmp_path / "persona.yaml"
    path.write_text("name: [拉爾夫\n", encoding="utf-8")

    with pytest.raises(persona.PersonaError, match="YAML"):
        persona.load_persona(path)

    assert list(tmp_path.iterdir()) == [path]


def test_length_caps_reject_overlong_instruction_fields(tmp_path: Path) -> None:
    path = tmp_path / "persona.yaml"
    path.write_text(
        valid_persona_yaml(memory_directive="過長" * 2500),
        encoding="utf-8",
    )

    with pytest.raises(persona.PersonaError, match="memory_directive"):
        persona.load_persona(path)


def test_default_ralf_yaml_loads(plugin_root: Path) -> None:
    loaded = persona.load_persona(plugin_root / "personas" / "default-ralf.yaml")

    assert loaded["name"] == "拉爾夫"
    assert loaded["species"]
    assert loaded["voice"]["tone"]
    assert loaded["addressing"]["user_term"]
    assert loaded["memory_directive"]


def test_default_ralf_locale_yamls_load(plugin_root: Path) -> None:
    zh_tw = persona.load_persona(plugin_root / "personas" / "default-ralf.zh-TW.yaml")
    en = persona.load_persona(plugin_root / "personas" / "default-ralf.en.yaml")

    assert zh_tw["name"] == "拉爾夫"
    assert en["name"] == "Ralf"
    assert en["addressing"]["user_term"] == "you"


def valid_persona_yaml(memory_directive: str = "主動記住長期有用且非敏感的個人事實。") -> str:
    return f"""
name: 拉爾夫
species: 德國牧羊犬獸人
background: 住在 Codex 裡的工作夥伴。
voice:
  tone: 沉穩、溫柔
  examples:
    - 我在，慢慢來。
values:
  - 穩定
taboos:
  - 不假裝知道沒被記錄的事
addressing:
  user_term: 你
  self_term: 我
memory_directive: {memory_directive}
"""
