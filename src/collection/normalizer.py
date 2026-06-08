"""Raw ArXiv records → normalized corpus.jsonl."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from src.collection.config import CollectionConfig

ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}$")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _parse_date(published: str | None) -> str | None:
    if not published:
        return None
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def _to_corpus_record(raw: dict) -> dict | None:
    arxiv_id = raw.get("arxiv_id", "")
    if not ARXIV_ID_RE.match(arxiv_id):
        return None

    title = (raw.get("title") or "").strip()
    abstract = (raw.get("abstract") or "").strip()
    authors = raw.get("authors") or []
    categories = raw.get("categories") or []
    date = _parse_date(raw.get("published"))

    if not title:
        return None
    if len(abstract) < 50:
        return None
    if not authors:
        return None
    if not categories:
        return None
    if not date:
        return None

    return {
        "id": arxiv_id,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "categories": categories,
        "date": date,
    }


def normalize_corpus(config: CollectionConfig) -> int:
    """
    Read raw_path, deduplicate by id/doi, validate schema, write corpus_path.

    Returns number of documents in final corpus.
    """
    config.validate()
    raw_records = _load_jsonl(config.raw_path)

    by_id: dict[str, tuple[str, dict]] = {}
    by_doi: dict[str, str] = {}

    for raw in raw_records:
        updated = raw.get("updated") or ""
        arxiv_id = raw.get("arxiv_id", "")

        if arxiv_id in by_id:
            if updated > by_id[arxiv_id][0]:
                by_id[arxiv_id] = (updated, raw)
        else:
            by_id[arxiv_id] = (updated, raw)

    corpus_records: list[dict] = []
    seen_dois: set[str] = set()

    for _, raw in sorted(by_id.values(), key=lambda x: x[0]):
        record = _to_corpus_record(raw)
        if record is None:
            continue

        doi = raw.get("doi")
        if doi:
            if doi in seen_dois:
                continue
            seen_dois.add(doi)

        corpus_records.append(record)

    config.corpus_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config.corpus_path, "w", encoding="utf-8") as f:
        for record in corpus_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return len(corpus_records)
