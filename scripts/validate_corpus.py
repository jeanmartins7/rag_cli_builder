#!/usr/bin/env python3
"""Validate data/corpus.jsonl against corpus-record.schema.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    REPO_ROOT / "specs/001-arxiv-corpus-ingestion/contracts/corpus-record.schema.json"
)
CORPUS_PATH = REPO_ROOT / "data/corpus.jsonl"


def main() -> int:
    if not CORPUS_PATH.exists():
        print(f"ERROR: {CORPUS_PATH} not found", file=sys.stderr)
        return 1

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    lines = CORPUS_PATH.read_text(encoding="utf-8").strip().splitlines()
    ids: set[str] = set()
    dois: set[str] = set()

    for i, line in enumerate(lines, 1):
        record = json.loads(line)
        jsonschema.validate(instance=record, schema=schema)
        if record["id"] in ids:
            print(f"ERROR: duplicate id {record['id']} at line {i}", file=sys.stderr)
            return 1
        ids.add(record["id"])

    print(f"OK: {len(lines)} documents validated against schema")
    if lines:
        sample = json.loads(lines[0])
        print(f"Sample id={sample['id']}, title={sample['title'][:60]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
