"""Lightweight markdown frontmatter parser and section extractor.

No external dependencies — uses only stdlib.
Supports Obsidian-friendly YAML-lite frontmatter.
"""
from __future__ import annotations
import re
from typing import Any


# ── Frontmatter ──────────────────────────────────────────────────────────────

def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    # Inline list: [a, b, c]
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [v.strip() for v in inner.split(",") if v.strip()]
    # Bare comma-separated list (only when ≥2 items)
    if "," in raw and not raw.startswith('"'):
        parts = [v.strip() for v in raw.split(",") if v.strip()]
        if len(parts) >= 2:
            return parts
    # Booleans
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    return raw


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML-lite frontmatter. Returns (metadata_dict, body_text)."""
    if not content.startswith("---"):
        return {}, content

    end = content.find("\n---", 3)
    if end == -1:
        return {}, content

    fm_block = content[3:end].strip()
    body = content[end + 4:].lstrip("\n")

    meta: dict[str, Any] = {}
    for line in fm_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = _parse_value(value)

    return meta, body


def build_frontmatter(meta: dict) -> str:
    """Serialize a metadata dict to a frontmatter block."""
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(str(i) for i in v)}]")
        elif v is None:
            lines.append(f"{k}: ")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# ── Section extraction ────────────────────────────────────────────────────────

def extract_section(body: str, section: str) -> str:
    """Return the trimmed content of a '## Section' heading block."""
    pattern = re.compile(
        rf"^##\s+{re.escape(section)}\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(body)
    if not match:
        return ""
    start = match.end()
    next_h2 = re.search(r"^##\s+", body[start:], re.MULTILINE)
    end = start + next_h2.start() if next_h2 else len(body)
    return body[start:end].strip()
