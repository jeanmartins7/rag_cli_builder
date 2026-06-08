from pathlib import Path

import pandas as pd
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from preprocessing import tokenize
from baseline_bm25 import build_bm25, search as search_bm25, load_corpus
from knn_retriever import build_knn, search as search_knn

def search_hybrid(query: str, bm25: BM25Okapi, vectorizer: TfidfVectorizer, knn: NearestNeighbors, docs: list[dict], k: int = 10, alpha: float = 0.5) -> list[tuple[int, float, dict]]:
    """
    Realiza busca híbrida usando soma ponderada normalizada.
    alpha controla o peso do KNN (denso). (1 - alpha) controla o peso do BM25 (esparso).
    """
    initial_k = min(100, len(docs))
    
    results_bm25 = search_bm25(query, bm25, docs, k=initial_k)
    results_knn = search_knn(query, vectorizer, knn, docs, k=initial_k)
    
    def normalize_scores(results):
        if not results: return {}
        scores = [r[1] for r in results]
        min_score, max_score = min(scores), max(scores)
        
        normalized = {}
        for idx, score, _ in results:
            norm_score = (score - min_score) / (max_score - min_score) if max_score > min_score else 0.5
            normalized[idx] = norm_score
        return normalized

    norm_bm25 = normalize_scores(results_bm25)
    norm_knn = normalize_scores(results_knn)
    
    combined_scores = {idx: (alpha * norm_knn.get(idx, 0.0)) + ((1.0 - alpha) * norm_bm25.get(idx, 0.0))
                       for idx in set(norm_bm25.keys()) | set(norm_knn.keys())}
        
    sorted_indices = sorted(combined_scores.items(), key=lambda item: item[1], reverse=True)[:k]
    
    return [(idx, score, docs[idx]) for idx, score in sorted_indices]

def generate_run(queries_path: Path, run_path: Path, bm25: BM25Okapi, vectorizer: TfidfVectorizer, knn: NearestNeighbors, docs: list[dict], k: int = 100, alpha: float = 0.5) -> None:
    if not queries_path.exists():
        print(f"Arquivo de queries {queries_path} não encontrado.")
        return
        
    queries = pd.read_csv(queries_path, sep="\t", names=["qid", "text"])
    run_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(run_path, "w", encoding="utf-8") as f:
        for _, q in queries.iterrows():
            n_results = min(k, len(docs))
            for rank, (idx, score, d) in enumerate(search_hybrid(q["text"], bm25, vectorizer, knn, docs, k=n_results, alpha=alpha), 1):
                f.write(f"{q['qid']} Q0 {d['arxiv_id']} {rank} {score:.6f} hybrid\n")
    print(f"Run salva em: {run_path}")

def run_hybrid():
    """
    Executa o pipeline completo do recuperador híbrido.
    """
    print("\n--- Executando Pipeline Híbrido ---")
    corpus_path = Path("../data/corpus.jsonl")
    queries_path = Path("../data/queries.tsv")
    run_path = Path("../../data/runs/hybrid.trec")
    
    if not corpus_path.exists():
         print(f"Corpus não encontrado em {corpus_path}. Execute a coleta primeiro.")
         return
         
    docs = load_corpus(corpus_path)
    print(f"Documentos carregados: {len(docs)}")
    
    print("Construindo índice BM25...")
    bm25 = build_bm25(docs)
    
    print("Construindo índice KNN...")
    vectorizer, knn, _ = build_knn(docs)
    
    generate_run(queries_path, run_path, bm25, vectorizer, knn, docs)
    print("--- Pipeline Híbrido Concluído ---")

if __name__ == "__main__":
    run_hybrid()
