from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from preprocessing.tokenizer import tokenize
from common.utils import load_corpus
from common.config import CORPUS_PATH, QUERIES_PATH, RUNS_DIR

def build_knn(docs: list[dict]) -> tuple[TfidfVectorizer, NearestNeighbors, np.ndarray]:
    texts = [(d["title"] + ". " + d["abstract"]) for d in docs]
    
    vectorizer = TfidfVectorizer(tokenizer=tokenize, lowercase=False)
    
    X = vectorizer.fit_transform(texts)
    
    knn = NearestNeighbors(n_neighbors=100, metric='cosine')
    knn.fit(X)
    
    return vectorizer, knn, X

def search(query: str, vectorizer: TfidfVectorizer, knn: NearestNeighbors, docs: list[dict], k: int = 10) -> list[tuple[int, float, dict]]:
    q_vec = vectorizer.transform([query])
    
    distances, indices = knn.kneighbors(q_vec, n_neighbors=k)
    
    results = []
    for i, dist in zip(indices[0], distances[0]):
        score = 1.0 - dist
        results.append((int(i), float(score), docs[i]))
        
    return results

def generate_run(queries_path: Path, run_path: Path, vectorizer: TfidfVectorizer, knn: NearestNeighbors, docs: list[dict], k: int = 100) -> None:
    if not queries_path.exists():
        print(f"Arquivo de queries {queries_path} não encontrado.")
        return
        
    queries = pd.read_csv(queries_path, sep="\t", names=["qid", "text"])
    run_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(run_path, "w", encoding="utf-8") as f:
        for _, q in queries.iterrows():
            n_results = min(k, len(docs))
            for rank, (idx, score, d) in enumerate(search(q["text"], vectorizer, knn, docs, k=n_results), 1):
                f.write(f"{q['qid']} Q0 {d['arxiv_id']} {rank} {score:.6f} knn\n")
    print(f"Run salva em: {run_path}")

def run_knn():
    """
    Executa o pipeline completo do KNN.
    """
    print("\n--- Executando Pipeline KNN ---")
    
    docs = load_corpus(CORPUS_PATH)
    if not docs:
        print(f"Corpus não encontrado em {CORPUS_PATH}. Execute a coleta primeiro.")
        return
         
    print(f"Documentos carregados: {len(docs)}")
    
    vectorizer, knn, X = build_knn(docs)
    print(f"Índice KNN/TF-IDF construído. Vocabulário: {X.shape[1]} termos.")
    
    generate_run(QUERIES_PATH, RUNS_DIR / "knn.trec", vectorizer, knn, docs)
    print("--- Pipeline KNN Concluído ---")

if __name__ == "__main__":
    run_knn()
