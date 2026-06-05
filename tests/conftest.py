from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def plugin_root() -> Path:
    return REPO_ROOT / "plugins" / "codex-fursona-pet-forge"


@pytest.fixture
def plugin_data(tmp_path: Path) -> Path:
    path = tmp_path / "plugin-data"
    path.mkdir()
    return path


@pytest.fixture
def codex_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "codex-home"
    path.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(path))
    return path


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "home"
    path.mkdir()
    monkeypatch.setenv("HOME", str(path))
    return path
