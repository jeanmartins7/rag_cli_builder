from pathlib import Path

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preprocessing.tokenizer import tokenize
from retrieval.bm25 import build_bm25, search as search_bm25
from common.utils import load_corpus
from common.config import CORPUS_PATH, QUERIES_PATH, RUNS_DIR

def extract_features(query: str, doc: dict, bm25_score: float, vectorizer: TfidfVectorizer) -> list[float]:
    """Extrai features para o par (consulta, documento)."""
    q_vec = vectorizer.transform([query])
    doc_text = doc["title"] + ". " + doc["abstract"]
    d_vec = vectorizer.transform([doc_text])
    
    cos_sim = cosine_similarity(q_vec, d_vec)[0][0]
    
    title_len = len(doc["title"].split())
    abstract_len = len(doc["abstract"].split())
    
    return [bm25_score, cos_sim, title_len, abstract_len]

def train_reranker(docs: list[dict], vectorizer: TfidfVectorizer) -> LogisticRegression:
    """Treina um modelo simples de regressão logística usando dados sintéticos."""
    print("Treinando modelo de re-ranking (dados sintéticos)...")
    X, y = [], []
    
    np.random.seed(42)
    sample_indices = np.random.choice(len(docs), min(100, len(docs)), replace=False)
    
    for idx in sample_indices:
        doc = docs[idx]
        query = doc["title"]
        features = extract_features(query, doc, 10.0, vectorizer)
        X.append(features)
        y.append(1)
        
        neg_idx = np.random.choice([i for i in range(len(docs)) if i != idx])
        neg_doc = docs[neg_idx]
        neg_features = extract_features(query, neg_doc, 1.0, vectorizer)
        X.append(neg_features)
        y.append(0)
        
    clf = LogisticRegression(random_state=42)
    clf.fit(X, y)
    print("Treinamento concluído.")
    return clf

def search_reranked(query: str, bm25: BM25Okapi, vectorizer: TfidfVectorizer, clf: LogisticRegression, docs: list[dict], initial_k: int = 100, final_k: int = 10) -> list[tuple[int, float, dict]]:
    """Realiza busca BM25 e re-ranqueia o top-k usando o classificador."""
    initial_results = search_bm25(query, bm25, docs, k=initial_k)
    
    if not initial_results:
        return []
        
    X_rerank = [extract_features(query, doc, bm25_score, vectorizer) for _, bm25_score, doc in initial_results]
    probs = clf.predict_proba(X_rerank)[:, 1]
    
    reranked_results = [(idx, float(probs[i]), doc) for i, (idx, bm25_score, doc) in enumerate(initial_results)]
    reranked_results.sort(key=lambda x: x[1], reverse=True)
    
    return reranked_results[:final_k]

def generate_run(queries_path: Path, run_path: Path, bm25: BM25Okapi, vectorizer: TfidfVectorizer, clf: LogisticRegression, docs: list[dict], k: int = 100) -> None:
    if not queries_path.exists():
        print(f"Arquivo de queries {queries_path} não encontrado.")
        return
        
    queries = pd.read_csv(queries_path, sep="\t", names=["qid", "text"])
    run_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(run_path, "w", encoding="utf-8") as f:
        for _, q in queries.iterrows():
            n_results = min(k, len(docs))
            for rank, (idx, score, d) in enumerate(search_reranked(q["text"], bm25, vectorizer, clf, docs, initial_k=max(100, k), final_k=n_results), 1):
                f.write(f"{q['qid']} Q0 {d['arxiv_id']} {rank} {score:.6f} reranked\n")
    print(f"Run salva em: {run_path}")

def run_reranker():
    """Executa o pipeline completo do re-ranqueador."""
    print("\n--- Executando Pipeline Re-ranqueador ---")
    
    docs = load_corpus(CORPUS_PATH)
    if not docs:
         print(f"Corpus não encontrado em {CORPUS_PATH}. Execute a coleta primeiro.")
         return
         
    print(f"Documentos carregados: {len(docs)}")
    
    print("Construindo índice BM25...")
    bm25 = build_bm25(docs)
    
    print("Construindo Vectorizer (TF-IDF)...")
    texts = [(d["title"] + ". " + d["abstract"]) for d in docs]
    vectorizer = TfidfVectorizer(tokenizer=tokenize, lowercase=False)
    vectorizer.fit(texts)
    
    clf = train_reranker(docs, vectorizer)
    
    generate_run(QUERIES_PATH, RUNS_DIR / "reranked.trec", bm25, vectorizer, clf, docs)
    print("--- Pipeline Re-ranqueador Concluído ---")

if __name__ == "__main__":
    run_reranker()
