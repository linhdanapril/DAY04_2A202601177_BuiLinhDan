from __future__ import annotations

from typing import Any

from tools._shared import domain, err


def request_item_selection(
    items: list[dict[str, Any]] | None = None,
    question: str = "",
    allow_multiple: bool = True,
) -> dict[str, Any]:
    try:
        items = items or []
        if not items:
            raise ValueError("items is empty; nothing to select from")

        options: list[str] = []
        for index, item in enumerate(items, start=1):
            title = (item.get("title") or item.get("summary") or "").strip().replace("\n", " ")
            source = (item.get("source") or domain(item.get("url", "")) or "?").strip()
            options.append(f"{index}. {title[:100]} — {source}")

        hint = "Trả lời bằng số, cách nhau bởi dấu phẩy (ví dụ: 1,3)." if allow_multiple \
            else "Trả lời bằng đúng một số."
        prompt = (question.strip() or "Bạn muốn giữ lại những mục nào?")

        return {
            "tool": "request_item_selection",
            "question": f"{prompt}\n\n" + "\n".join(options) + f"\n\n{hint}",
            "options": options,
            "item_count": len(items),
            "allow_multiple": allow_multiple,
            "awaiting_user": True,
            "error": None,
        }
    except Exception as exc:
        return err("request_item_selection", exc)
