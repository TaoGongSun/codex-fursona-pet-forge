from __future__ import annotations

from typing import Any


class SimpleYAMLError(ValueError):
    pass


def load(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    value, _index = _parse_mapping(lines, 0, 0)
    return value


def _parse_mapping(lines: list[str], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        current_indent = _indent(line)
        if current_indent < indent:
            break
        if current_indent > indent:
            raise SimpleYAMLError(f"unexpected indent: {line}")

        key, raw_value = _split_key_value(line.strip())
        if raw_value == "|":
            block, index = _parse_block_scalar(lines, index + 1, indent + 2)
            result[key] = block
        elif raw_value:
            result[key] = _parse_scalar(raw_value)
            index += 1
        else:
            result[key], index = _parse_child(lines, index + 1, indent + 2)
    return result, index


def _parse_child(lines: list[str], index: int, indent: int) -> tuple[Any, int]:
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines) or _indent(lines[index]) < indent:
        return {}, index
    if lines[index].lstrip().startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        current_indent = _indent(line)
        if current_indent < indent:
            break
        if current_indent != indent or not line.lstrip().startswith("- "):
            raise SimpleYAMLError(f"invalid list item: {line}")
        result.append(_parse_scalar(line.strip()[2:].strip()))
        index += 1
    return result, index


def _parse_block_scalar(lines: list[str], index: int, indent: int) -> tuple[str, int]:
    block: list[str] = []
    while index < len(lines):
        line = lines[index]
        if line.strip() and _indent(line) < indent:
            break
        block.append(line[indent:] if len(line) >= indent else "")
        index += 1
    return "\n".join(block).rstrip() + "\n", index


def _split_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        raise SimpleYAMLError(f"missing ':' in line: {line}")
    key, value = line.split(":", 1)
    key = key.strip()
    if not key:
        raise SimpleYAMLError("empty key")
    return key, value.strip()


def _parse_scalar(value: str) -> Any:
    if value.startswith("[") and not value.endswith("]"):
        raise SimpleYAMLError(f"unsupported or malformed scalar: {value}")
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    try:
        return int(value)
    except ValueError:
        return value.strip('"').strip("'")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))
