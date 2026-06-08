#!/usr/bin/env python3
"""
Generate a minimal schema-valid dev corpus for pipeline smoke tests.

Replace with real data via: python scripts/collect_corpus.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = REPO_ROOT / "data/corpus.jsonl"

SAMPLES = [
    {
        "id": "2401.15024",
        "title": "Structured Pruning of Large Language Models via Importance Scores",
        "abstract": (
            "We study structural pruning of transformer-based large language models "
            "during fine-tuning, removing attention heads and MLP neurons with minimal "
            "accuracy loss on downstream tasks."
        ),
        "authors": ["Alice Researcher", "Bob Scientist"],
        "categories": ["cs.CL", "cs.LG"],
        "date": "2024-01-26",
    },
    {
        "id": "2305.12345",
        "title": "LLM Compression via Layer-wise Magnitude Pruning",
        "abstract": (
            "This paper proposes an efficient compression pipeline for open-source LLMs "
            "using magnitude-based pruning of MLP layers and knowledge distillation "
            "during parameter-efficient fine-tuning."
        ),
        "authors": ["Carol Author"],
        "categories": ["cs.LG", "cs.AI"],
        "date": "2023-05-18",
    },
    {
        "id": "2403.06789",
        "title": "Attention Head Pruning for Efficient Inference",
        "abstract": (
            "We analyze which attention heads contribute least to model performance and "
            "prune them structurally, achieving significant speedup with competitive "
            "perplexity on language modeling benchmarks."
        ),
        "authors": ["Dan Engineer", "Eve ML"],
        "categories": ["cs.CL"],
        "date": "2024-03-12",
    },
    {
        "id": "2501.01010",
        "title": "Parameter Efficient Fine-Tuning with Dynamic Sparsity",
        "abstract": (
            "We combine LoRA-style adapters with dynamic structural sparsity patterns "
            "learned during fine-tuning of compressed transformer models for NLP tasks."
        ),
        "authors": ["Frank PhD"],
        "categories": ["cs.AI", "cs.LG"],
        "date": "2025-01-08",
    },
    {
        "id": "2311.22222",
        "title": "Survey of Structural Compression Methods for LLMs",
        "abstract": (
            "A comprehensive survey of structural pruning, quantization, and distillation "
            "techniques applied to large language models in the 2023-2026 period with "
            "benchmark comparisons across open-source model families."
        ),
        "authors": ["Grace Reviewer", "Henry Analyst"],
        "categories": ["cs.CL", "cs.AI"],
        "date": "2023-11-20",
    },
]


def main() -> None:
    CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_PATH, "w", encoding="utf-8") as f:
        for record in SAMPLES:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote {len(SAMPLES)} dev records to {CORPUS_PATH}")


if __name__ == "__main__":
    main()
