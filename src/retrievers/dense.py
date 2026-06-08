"""Dense retriever using TF-IDF + cosine similarity KNN."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.preprocessing.config import PreprocessConfig
from src.preprocessing.pipeline import build_indexable_text, preprocess_query


class DenseRetriever:
    """TF-IDF vectorized cosine KNN retriever."""

    def __init__(
        self,
        corpus_path: Path | str = Path("data/corpus.jsonl"),
        preprocess_config: PreprocessConfig | None = None,
    ) -> None:
        self.preprocess_config = preprocess_config or PreprocessConfig()
        self.doc_ids: list[str] = []
        self.normalized_texts: list[str] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._doc_matrix = None
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
                self.normalized_texts.append(" ".join(tokens))

        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"(?u)\b\w+\b",
            lowercase=False,
        )
        self._doc_matrix = self._vectorizer.fit_transform(self.normalized_texts)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Return ranked (doc_id, cosine_score) pairs."""
        if self._vectorizer is None or self._doc_matrix is None:
            raise RuntimeError("Dense index not built")
        tokens = preprocess_query(query, self.preprocess_config)
        query_text = " ".join(tokens)
        query_vec = self._vectorizer.transform([query_text])
        scores = cosine_similarity(query_vec, self._doc_matrix).flatten()
        ranked_idx = np.argsort(scores)[::-1][:top_k]
        return [(self.doc_ids[i], float(scores[i])) for i in ranked_idx]

    def write_trec_run(
        self,
        queries: dict[str, str],
        output_path: Path | str,
        top_k: int = 10,
        system_name: str = "knn",
    ) -> None:
        """Write TREC-format run file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for qid, query_text in queries.items():
                results = self.search(query_text, top_k=top_k)
                for rank, (doc_id, score) in enumerate(results, 1):
                    f.write(
                        f"{qid} Q0 {doc_id} {rank} {score:.6f} {system_name}\n"
                    )
