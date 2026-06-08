"""ArXiv API fetcher with retry, backoff, and incremental save."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import arxiv
from tqdm import tqdm

from src.collection.config import CollectionConfig
from src.collection.query_builder import build_arxiv_query


def _query_hash(config: CollectionConfig) -> str:
    payload = json.dumps(
        {
            "keywords": config.keywords,
            "categories": config.categories,
            "year_from": config.year_from,
            "year_to": config.year_to,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _load_checkpoint(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_checkpoint(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_seen_ids(raw_path: Path) -> set[str]:
    if not raw_path.exists():
        return set()
    seen: set[str] = set()
    with open(raw_path, encoding="utf-8") as f:
        for line in f:
            try:
                seen.add(json.loads(line)["arxiv_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return seen


def fetch_arxiv_raw(config: CollectionConfig) -> int:
    """
    Incremental ArXiv collection with retry/backoff.

    Appends to config.raw_path and updates config.checkpoint_path.
    Returns total unique ids collected.
    """
    config.validate()
    config.raw_path.parent.mkdir(parents=True, exist_ok=True)

    query = build_arxiv_query(config.keywords, config.categories)
    qhash = _query_hash(config)
    checkpoint = _load_checkpoint(config.checkpoint_path)

    if checkpoint and checkpoint.get("query_hash") != qhash:
        raise ValueError(
            "Collection parameters changed since last run. "
            "Delete checkpoint/raw file or confirm overwrite."
        )

    seen = _load_seen_ids(config.raw_path)
    offset = checkpoint.get("offset", 0) if checkpoint.get("query_hash") == qhash else 0
    client = arxiv.Client(
        page_size=config.page_size, delay_seconds=5, num_retries=8
    )

    max_outer_attempts = 6
    initial_backoff = 60
    outer_attempt = 0

    while len(seen) < config.target_count and outer_attempt < max_outer_attempts:
        try:
            search = arxiv.Search(
                query=query,
                max_results=config.target_count * 3,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )

            with open(config.raw_path, "a", encoding="utf-8") as f:
                pbar = tqdm(
                    initial=len(seen),
                    total=config.target_count,
                    desc="collecting",
                )
                for result in client.results(search, offset=offset):
                    offset += 1
                    year = result.published.year if result.published else None
                    if year is not None and year < config.year_from:
                        continue
                    if year is not None and year > config.year_to:
                        continue

                    arxiv_id = result.get_short_id().split("v")[0]
                    if arxiv_id in seen:
                        continue

                    record = {
                        "arxiv_id": arxiv_id,
                        "title": (result.title or "").strip(),
                        "abstract": (result.summary or "")
                        .strip()
                        .replace("\n", " "),
                        "authors": [a.name for a in result.authors],
                        "categories": list(result.categories or []),
                        "published": (
                            result.published.isoformat() if result.published else None
                        ),
                        "updated": (
                            result.updated.isoformat() if result.updated else None
                        ),
                        "doi": result.doi,
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()
                    seen.add(arxiv_id)
                    pbar.update(1)
                    pbar.set_postfix(offset=offset)

                    _save_checkpoint(
                        config.checkpoint_path,
                        {
                            "offset": offset,
                            "seen_ids": sorted(seen),
                            "query_hash": qhash,
                        },
                    )

                    if len(seen) >= config.target_count:
                        break
                pbar.close()
            break

        except Exception as e:
            outer_attempt += 1
            wait = min(initial_backoff * (2 ** (outer_attempt - 1)), 600)
            print(
                f"\n[warning] collection interrupted (attempt {outer_attempt}/"
                f"{max_outer_attempts}): {type(e).__name__}: {e}"
            )
            print(f"[warning] waiting {wait}s before resuming from offset={offset}...")
            for _ in tqdm(range(wait), desc="backoff", leave=False):
                time.sleep(1)

    _save_checkpoint(
        config.checkpoint_path,
        {"offset": offset, "seen_ids": sorted(seen), "query_hash": qhash},
    )
    return len(seen)
