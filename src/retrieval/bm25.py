from pathlib import Path

import pandas as pd
from rank_bm25 import BM25Okapi

from preprocessing.tokenizer import tokenize
from common.utils import load_corpus
from common.config import CORPUS_PATH, QUERIES_PATH, RUNS_DIR

def build_bm25(docs: list[dict], k1: float = 1.5, b: float = 0.75) -> BM25Okapi:
    texts = [(d["title"] + ". " + d["abstract"]) for d in docs]
    tokenized_corpus = [tokenize(t) for t in texts]
    return BM25Okapi(tokenized_corpus, k1=k1, b=b)

def search(query: str, bm25: BM25Okapi, docs: list[dict], k: int = 10) -> list[tuple[int, float, dict]]:
    q_tokens = tokenize(query)
    scores = bm25.get_scores(q_tokens)
    top_idx = scores.argsort()[::-1][:k]
    return [(int(i), float(scores[i]), docs[i]) for i in top_idx]

def generate_run(queries_path: Path, run_path: Path, bm25: BM25Okapi, docs: list[dict], k: int = 100) -> None:
    if not queries_path.exists():
        print(f"Arquivo de queries {queries_path} não encontrado.")
        return
        
    queries = pd.read_csv(queries_path, sep="\t", names=["qid", "text"])
    run_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(run_path, "w", encoding="utf-8") as f:
        for _, q in queries.iterrows():
            for rank, (idx, score, d) in enumerate(search(q["text"], bm25, docs, k=k), 1):
                f.write(f"{q['qid']} Q0 {d['arxiv_id']} {rank} {score:.6f} bm25\n")
    print(f"Run salva em: {run_path}")

def run_bm25():
    """
    Executa o pipeline completo do BM25.
    """
    print("\n--- Executando Pipeline BM25 ---")
    
    docs = load_corpus(CORPUS_PATH)
    if not docs:
         print(f"Corpus não encontrado em {CORPUS_PATH}. Execute a coleta primeiro.")
         return
         
    print(f"Documentos carregados: {len(docs)}")
    
    bm25 = build_bm25(docs)
    print("Índice BM25 construído.")
    
    generate_run(QUERIES_PATH, RUNS_DIR / "bm25.trec", bm25, docs)
    print("--- Pipeline BM25 Concluído ---")

if __name__ == "__main__":
    run_bm25()
