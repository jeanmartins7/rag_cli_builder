"""Collection configuration dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

VALID_CATEGORIES = frozenset({"cs.CL", "cs.LG", "cs.AI"})


@dataclass(frozen=True)
class CollectionConfig:
    """Immutable configuration for ArXiv corpus collection."""

    theme: str
    keywords: list[str]
    categories: list[str]
    year_from: int
    year_to: int
    target_count: int
    page_size: int = 50
    raw_path: Path = field(default_factory=lambda: Path("data/arxiv_raw.jsonl"))
    corpus_path: Path = field(default_factory=lambda: Path("data/corpus.jsonl"))
    checkpoint_path: Path = field(
        default_factory=lambda: Path("data/.collection_checkpoint.json")
    )

    def validate(self) -> None:
        """Validate configuration; raise ValueError on invalid settings."""
        if not self.theme.strip():
            raise ValueError("theme must not be empty")
        if not self.keywords:
            raise ValueError("keywords must contain at least one term")
        if not self.categories:
            raise ValueError("categories must contain at least one category")
        invalid = set(self.categories) - VALID_CATEGORIES
        if invalid:
            raise ValueError(f"invalid categories: {invalid}")
        if self.year_from > self.year_to:
            raise ValueError("year_from must be <= year_to")
        if not 1000 <= self.target_count <= 5000:
            raise ValueError("target_count must be between 1000 and 5000")
        if not 25 <= self.page_size <= 100:
            raise ValueError("page_size must be between 25 and 100")
