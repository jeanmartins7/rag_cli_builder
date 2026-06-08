#!/usr/bin/env python3
"""CLI wrapper for ArXiv corpus collection and normalization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.collection.config import CollectionConfig
from src.collection.fetcher import fetch_arxiv_raw
from src.collection.normalizer import normalize_corpus

DEFAULT_KEYWORDS = [
    "structural pruning",
    "LLM compression",
    "attention heads pruning",
    "MLP pruning",
    "parameter efficient fine-tuning",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and normalize ArXiv corpus")
    parser.add_argument("--target", type=int, default=2000, help="Target document count")
    parser.add_argument("--page-size", type=int, default=50)
    args = parser.parse_args()

    config = CollectionConfig(
        theme="Structural pruning and LLM compression during fine-tuning",
        keywords=DEFAULT_KEYWORDS,
        categories=["cs.CL", "cs.LG", "cs.AI"],
        year_from=2023,
        year_to=2026,
        target_count=args.target,
        page_size=args.page_size,
    )
    config.validate()

    print("Fetching from ArXiv API (may take hours; re-run to resume)...")
    n_raw = fetch_arxiv_raw(config)
    print(f"Raw unique ids: {n_raw}")

    n_corpus = normalize_corpus(config)
    print(f"Corpus documents: {n_corpus}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
