from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from tools._shared import ROOT, err

EXPORT_DIR = ROOT / "exports"


def save_digest(content: str = "", filename: str = "digest", confirmed: bool = False) -> dict[str, Any]:
    if not confirmed:
        return {
            "tool": "save_digest",
            "status": "needs_confirmation",
            "message": "Only write the file after the user explicitly confirms.",
            "preview": content[:200],
        }
    try:
        if not content.strip():
            raise ValueError("content is empty; nothing to save")
        stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", filename).strip("-") or "digest"
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = EXPORT_DIR / f"{stem}_{stamp}.md"
        path.write_text(content, encoding="utf-8")
        return {
            "tool": "save_digest",
            "status": "saved",
            "path": str(path.relative_to(ROOT)),
            "chars_written": len(content),
        }
    except Exception as exc:
        return err("save_digest", exc)
