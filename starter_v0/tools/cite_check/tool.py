from __future__ import annotations

from typing import Any

from tools._shared import domain, err

TIER3_DOMAINS = {
    "x.com", "twitter.com", "reddit.com", "facebook.com",
    "t.me", "threads.net", "quora.com",
}
TIER1_HINTS = ("arxiv.org", "openai.com", "anthropic.com", "deepmind.google", ".gov", ".edu")
WEAK_LABELS = ("unverified", "early signal", "chưa xác minh", "tín hiệu sớm", "chưa kiểm chứng")


def _tier(url: str) -> int:
    host = domain(url)
    if not host:
        return 3
    if host in TIER3_DOMAINS:
        return 3
    if any(hint in host or host.endswith(hint) for hint in TIER1_HINTS):
        return 1
    return 2


def check_citations(items: list[dict[str, Any]] | None = None, strict: bool = False) -> dict[str, Any]:
    try:
        items = items or []
        if not items:
            raise ValueError("items is empty; nothing to check")
        violations: list[dict[str, Any]] = []
        tiers: dict[int, int] = {1: 0, 2: 0, 3: 0}

        for index, item in enumerate(items):
            url = (item.get("url") or "").strip()
            source = (item.get("source") or "").strip() or domain(url)
            summary = (item.get("summary") or "").lower()
            tier = _tier(url)
            tiers[tier] += 1
            problems: list[str] = []

            if not url:
                problems.append("missing_url")
            if not source:
                problems.append("missing_source")
            if tier == 3 and not any(label in summary for label in WEAK_LABELS):
                problems.append("tier3_not_labeled_unverified")
            if strict and tier == 3:
                problems.append("tier3_rejected_in_strict_mode")

            if problems:
                violations.append({
                    "index": index,
                    "title": (item.get("title") or "")[:80],
                    "tier": tier,
                    "problems": problems,
                })

        return {
            "tool": "check_citations",
            "policy": "source-citation-policy",
            "checked": len(items),
            "tier_counts": tiers,
            "violation_count": len(violations),
            "violations": violations,
            "verdict": "pass" if not violations else "needs_review",
            "error": None,
        }
    except Exception as exc:
        return err("check_citations", exc)
