"""BM25 sparse retriever over title+abstract."""

from __future__ import annotations

import json
from pathlib import Path

from rank_bm25 import BM25Okapi

from src.preprocessing.config import PreprocessConfig
from src.preprocessing.pipeline import build_indexable_text, preprocess_query

# Okapi BM25 parameters (documented for reproducibility)
K1 = 1.5
B = 0.75


class BM25Retriever:
    """BM25 retriever using preprocessed title+abstract tokens."""

    def __init__(
        self,
        corpus_path: Path | str = Path("data/corpus.jsonl"),
        preprocess_config: PreprocessConfig | None = None,
        k1: float = K1,
        b: float = B,
    ) -> None:
        self.preprocess_config = preprocess_config or PreprocessConfig()
        self.k1 = k1
        self.b = b
        self.doc_ids: list[str] = []
        self.tokenized_corpus: list[list[str]] = []
        self._bm25: BM25Okapi | None = None
        self._load_corpus(Path(corpus_path))

    def _load_corpus(self, path: Path) -> None:
        with open(path, encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                tokens = build_indexable_text(
                    record["title"],
                    record["abstract"],
                    self.preprocess_config,
                )
                self.doc_ids.append(record["id"])
                self.tokenized_corpus.append(tokens)
        self._bm25 = BM25Okapi(self.tokenized_corpus, k1=self.k1, b=self.b)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Return ranked (doc_id, score) pairs."""
        if self._bm25 is None:
            raise RuntimeError("BM25 index not built")
        tokens = preprocess_query(query, self.preprocess_config)
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(
            zip(self.doc_ids, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked[:top_k]

    def write_trec_run(
        self,
        queries: dict[str, str],
        output_path: Path | str,
        top_k: int = 10,
        system_name: str = "bm25",
    ) -> None:
        """Write TREC-format run file: qid Q0 doc_id rank score system."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for qid, query_text in queries.items():
                results = self.search(query_text, top_k=top_k)
                for rank, (doc_id, score) in enumerate(results, 1):
                    f.write(
                        f"{qid} Q0 {doc_id} {rank} {score:.6f} {system_name}\n"
                    )
