#!/usr/bin/env python3
"""Demo CLI: query text in → ranked articles out."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.preprocessing.config import PreprocessConfig
from src.retrievers.bm25 import BM25Retriever
from src.retrievers.dense import DenseRetriever

CORPUS_PATH = REPO_ROOT / "data/corpus.jsonl"


def _load_titles() -> dict[str, str]:
    titles: dict[str, str] = {}
    with open(CORPUS_PATH, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            titles[rec["id"]] = rec["title"]
    return titles


def main() -> int:
    parser = argparse.ArgumentParser(description="Search corpus with BM25 or dense KNN")
    parser.add_argument("query", help="Search query text")
    parser.add_argument(
        "--method", choices=["bm25", "dense"], default="bm25", help="Retriever"
    )
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    if not CORPUS_PATH.exists():
        print(f"ERROR: corpus not found at {CORPUS_PATH}", file=sys.stderr)
        print("Run: python scripts/collect_corpus.py", file=sys.stderr)
        return 1

    pp_cfg = PreprocessConfig(use_stemming=False)
    if args.method == "bm25":
        retriever = BM25Retriever(CORPUS_PATH, preprocess_config=pp_cfg)
    else:
        retriever = DenseRetriever(CORPUS_PATH, preprocess_config=pp_cfg)

    titles = _load_titles()
    results = retriever.search(args.query, top_k=args.top_k)

    print(f"Query: {args.query}")
    print(f"Method: {args.method}\n")
    for rank, (doc_id, score) in enumerate(results, 1):
        title = titles.get(doc_id, "?")
        print(f"{rank}. [{doc_id}] {score:.4f} — {title}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
