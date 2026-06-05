import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from data_paths import plugin_data_dir as resolve_plugin_data_dir  # noqa: E402


class FactError(ValueError):
    pass


SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\b[A-Za-z0-9_]*(token|secret|password|passwd|api[_-]?key)[A-Za-z0-9_]*\b", re.I),
]
SENSITIVE_LABELS = {"secret", "sensitive", "private", "credential", "credentials"}


def write_fact(plugin_data: Path | str, payload: dict[str, Any]) -> dict[str, str]:
    data_dir = Path(plugin_data)
    facts_dir = data_dir / "personal-facts"
    facts_dir.mkdir(parents=True, exist_ok=True)

    name = _required_string(payload, "name")
    fact = _required_string(payload, "fact")
    fact_type = str(payload.get("type") or "general").strip() or "general"
    sensitivity = str(payload.get("sensitivity") or "normal").strip() or "normal"
    source = str(payload.get("source") or "conversation").strip() or "conversation"

    if _looks_sensitive(name, fact, sensitivity) and not payload.get("allow_sensitive"):
        raise FactError("內容疑似敏感；若使用者明確要求本機保存，請傳入 allow_sensitive=true")

    slug = _slugify(name)
    fact_path = facts_dir / f"{slug}.md"
    metadata = {
        "name": slug,
        "type": fact_type,
        "sensitivity": sensitivity,
        "source": source,
        "updated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
    }
    fact_path.write_text(_render_fact(metadata, fact), encoding="utf-8")
    rebuild_memory_index(facts_dir)

    return {"slug": slug, "path": str(fact_path)}


def rebuild_memory_index(facts_dir: Path | str) -> None:
    root = Path(facts_dir)
    grouped: dict[str, list[tuple[str, str]]] = {}

    for path in sorted(root.glob("*.md")):
        if path.name == "MEMORY.md":
            continue
        metadata, body = _read_fact(path)
        fact_type = str(metadata.get("type") or "general")
        grouped.setdefault(fact_type, []).append((path.name, _summary(body)))

    lines = ["# Personal facts", ""]
    if not grouped:
        lines.append("目前還沒有已記住的個人事實。")
    else:
        for fact_type in sorted(grouped):
            lines.extend([f"## {fact_type}", ""])
            for filename, summary in grouped[fact_type]:
                slug = filename.removesuffix(".md")
                lines.append(f"- [{slug}]({filename}) — {summary}")
            lines.append("")

    (root / "MEMORY.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            raise FactError("stdin JSON 必須是 object")
        result = write_fact(_plugin_data_dir(), payload)
    except (FactError, OSError) as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 1

    json.dump({"ok": True, **result}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def _render_fact(metadata: dict[str, str], fact: str) -> str:
    frontmatter = "\n".join(f"{key}: {value}" for key, value in metadata.items())
    return f"---\n{frontmatter}\n---\n\n{fact.strip()}\n"


def _read_fact(path: Path) -> tuple[dict[str, Any], str]:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    metadata = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, match.group(2).strip()


def _summary(body: str) -> str:
    for line in body.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return "未提供摘要"


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FactError(f"缺少必要欄位：{key}")
    return value.strip()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or "fact"


def _looks_sensitive(name: str, fact: str, sensitivity: str) -> bool:
    if sensitivity.lower() in SENSITIVE_LABELS:
        return True
    haystack = f"{name}\n{fact}"
    return any(pattern.search(haystack) for pattern in SECRET_PATTERNS)


def _plugin_data_dir() -> Path:
    return resolve_plugin_data_dir()


if __name__ == "__main__":
    raise SystemExit(main())
