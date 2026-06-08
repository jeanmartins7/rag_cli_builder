import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from preprocessing import tokenize

def load_corpus(path: Path) -> list[dict]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs

def build_knn(docs: list[dict]) -> tuple[TfidfVectorizer, NearestNeighbors, np.ndarray]:
    texts = [(d["title"] + ". " + d["abstract"]) for d in docs]
    
    # Dummy tokenize to pass text directly or use our custom tokenizer
    # We pass the custom tokenizer directly to TfidfVectorizer
    vectorizer = TfidfVectorizer(tokenizer=tokenize, lowercase=False)
    
    X = vectorizer.fit_transform(texts)
    
    # Fit KNN
    knn = NearestNeighbors(n_neighbors=100, metric='cosine')
    knn.fit(X)
    
    return vectorizer, knn, X

def search(query: str, vectorizer: TfidfVectorizer, knn: NearestNeighbors, docs: list[dict], k: int = 10) -> list[tuple[int, float, dict]]:
    q_vec = vectorizer.transform([query])
    
    # nearest neighbors
    distances, indices = knn.kneighbors(q_vec, n_neighbors=k)
    
    # metric is cosine distance, so score can be 1 - distance (cosine similarity)
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
            # Pegamos mais de k no knn, pois queremos salvar o top k. Se k > n_neighbors ajustamos lá na busca.
            # Aqui vamos forçar que o baseline traga no máximo len(docs) ou k, o que for menor.
            n_results = min(k, len(docs))
            for rank, (idx, score, d) in enumerate(search(q["text"], vectorizer, knn, docs, k=n_results), 1):
                f.write(f"{q['qid']} Q0 {d['arxiv_id']} {rank} {score:.6f} knn\n")
    print(f"Run salva em: {run_path}")

def run_knn():
    """
    Executa o pipeline completo do KNN.
    """
    print("\n--- Executando Pipeline KNN ---")
    corpus_path = Path("../data/corpus.jsonl")
    queries_path = Path("../data/queries.tsv")
    run_path = Path("../../data/runs/knn.trec")
    
    if not corpus_path.exists():
         print(f"Corpus não encontrado em {corpus_path}. Execute a coleta primeiro.")
         return
         
    docs = load_corpus(corpus_path)
    print(f"Documentos carregados: {len(docs)}")
    
    vectorizer, knn, X = build_knn(docs)
    print(f"Índice KNN/TF-IDF construído. Vocabulário: {X.shape[1]} termos.")
    
    generate_run(queries_path, run_path, vectorizer, knn, docs)
    print("--- Pipeline KNN Concluído ---")

if __name__ == "__main__":
    run_knn()
