"""ArXiv query string builder."""

from __future__ import annotations


def build_arxiv_query(keywords: list[str], categories: list[str]) -> str:
    """Build ArXiv query: (all:"kw1" OR ...) AND (cat:cs.CL OR ...)."""
    kw_part = " OR ".join(f'all:"{k}"' for k in keywords) if keywords else ""
    cat_part = " OR ".join(f"cat:{c}" for c in categories) if categories else ""

    parts = [
        p
        for p in [
            f"({kw_part})" if kw_part else "",
            f"({cat_part})" if cat_part else "",
        ]
        if p
    ]
    return " AND ".join(parts) if parts else "all:*"
