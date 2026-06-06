# -*- coding: utf-8 -*-
"""
Ferramenta CLI `rag-setup` para Scaffolding de Projetos de RAG Científico (Tema-Agnóstico).
Autor: Jean Marcel Peres Martins (FACOM/UFMS)
"""

import argparse
import os
import stat
import sys
from pathlib import Path

# ==============================================================================
# TEMPLATES DE CÓDIGO DO PIPELINE GERADO (COM SPACEHOLDERS DE ESCOPO)
# ==============================================================================

MANAGE_TEMPLATE = """# -*- coding: utf-8 -*-
\"\"\"
Orquestrador do Pipeline de RAG (Busca e Recuperação Temática)
Autor: {{AUTHOR}}

Decisões de Implementação do Orquestrador:
- Utiliza argparse com subparsers para isolamento das tarefas (coletar, processar, buscar, avaliar).
- Invoca cada subprocesso utilizando sys.executable (o mesmo Python do ambiente ativo) de forma a garantir isolamento de dependências.
- Executa em pipeline sequencial usando a chamada 'run-all' para teste rápido do sistema completo.
\"\"\"

import argparse
import sys
import subprocess
import os

def main():
    parser = argparse.ArgumentParser(
        description="Orquestrador do pipeline de RAG.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-comando a executar")

    # Coletar
    parser_coletar = subparsers.add_parser("coletar", help="Coleta artigos científicos via API do ArXiv")
    parser_coletar.add_argument("--keywords", nargs="+", default={{DEFAULT_KEYWORDS}},
                                help="Palavras-chave para busca de artigos")
    parser_coletar.add_argument("--categories", nargs="+", default={{DEFAULT_CATEGORIES}},
                                help="Categorias do arXiv")
    parser_coletar.add_argument("--year_from", type=int, default={{DEFAULT_YEAR_FROM}}, help="Ano inicial")
    parser_coletar.add_argument("--year_to", type=int, default={{DEFAULT_YEAR_TO}}, help="Ano final")
    parser_coletar.add_argument("--target_size", type=int, default={{DEFAULT_TARGET_SIZE}}, help="Quantidade de artigos a coletar")

    # Processar
    subparsers.add_parser("processar", help="Pré-processa e divide os artigos em chunks")

    # Buscar
    parser_buscar = subparsers.add_parser("buscar", help="Busca documentos relevantes")
    parser_buscar.add_argument("--modelo", type=str, choices=["bm25", "knn"{{ADDITIONAL_MODELS}}], default="bm25",
                                help="Modelo de recuperação de informação")
    parser_buscar.add_argument("--query", type=str, default="{{DEFAULT_QUERY}}",
                                help="Query de busca/recuperação")
    parser_buscar.add_argument("--top_k", type=int, default=3, help="Número de documentos a recuperar")

    # Avaliar
    subparsers.add_parser("avaliar", help="Avalia o pipeline usando métricas clássicas de IR (Precision@K, Recall@K, MAP, MRR)")

    # Run-all
    subparsers.add_parser("run-all", help="Executa o pipeline completo sequencialmente")

    args = parser.parse_args()

    python_bin = sys.executable

    if args.command == "coletar":
        print(f"[*] Iniciando etapa de Coleta via ArXiv...")
        cmd = [python_bin, "src/utils/coleta.py",
               "--keywords"] + args.keywords + [
               "--categories"] + args.categories + [
               "--year_from", str(args.year_from),
               "--year_to", str(args.year_to),
               "--target_size", str(args.target_size)]
        subprocess.run(cmd, check=True)

    elif args.command == "processar":
        print("[*] Iniciando etapa de Pré-processamento...")
        cmd = [python_bin, "src/utils/preprocess.py"]
        subprocess.run(cmd, check=True)

    elif args.command == "buscar":
        print(f"[*] Executando busca utilizando o modelo '{args.modelo}' para a query: '{args.query}'...")
        if args.modelo == "bm25":
            cmd = [python_bin, "src/models/bm25_retriever.py", "--query", args.query, "--top_k", str(args.top_k)]
        elif args.modelo == "knn":
            cmd = [python_bin, "src/models/knn_retriever.py", "--query", args.query, "--top_k", str(args.top_k)]
        elif args.modelo == "hybrid":
            cmd = [python_bin, "src/models/m5_hybrid.py", "--query", args.query, "--top_k", str(args.top_k)]
        else:
            print(f"Erro: Modelo {args.modelo} não implementado.")
            sys.exit(1)
        subprocess.run(cmd, check=True)

    elif args.command == "avaliar":
        print("[*] Iniciando etapa de Avaliação do pipeline...")
        cmd = [python_bin, "eval/evaluate.py"]
        subprocess.run(cmd, check=True)

    elif args.command == "run-all":
        print("="*80)
        print("INICIANDO EXECUÇÃO COMPLETA DO PIPELINE DE RAG")
        print("="*80)
        
        # 1. Coleta
        print("\\n[Etapa 1/4] Coletando artigos...")
        cmd = [python_bin, "src/utils/coleta.py", "--target_size", str({{DEFAULT_TARGET_SIZE}})]
        subprocess.run(cmd, check=True)
        
        # 2. Processamento
        print("\\n[Etapa 2/4] Pré-processando artigos...")
        cmd = [python_bin, "src/utils/preprocess.py"]
        subprocess.run(cmd, check=True)
        
        # 3. Busca teste (para validar o retriever padrão)
        print("\\n[Etapa 3/4] Executando busca de teste (BM25)...")
        cmd = [python_bin, "src/models/bm25_retriever.py", "--query", "{{TEST_QUERY}}", "--top_k", "2"]
        subprocess.run(cmd, check=True)
        
        # 4. Avaliação
        print("\\n[Etapa 4/4] Executando avaliação de métricas de IR...")
        cmd = [python_bin, "eval/evaluate.py"]
        subprocess.run(cmd, check=True)
        
        print("\\n" + "="*80)
        print("PIPELINE EXECUTADO COM SUCESSO!")
        print("="*80)

if __name__ == "__main__":
    main()
"""

COLETA_TEMPLATE = """# -*- coding: utf-8 -*-
\"\"\"
Módulo de Coleta e Normalização de Artigos Científicos via API do ArXiv com Fallback Offline.
Autor: {{AUTHOR}}

Decisões de Implementação do Coletor:
- Utiliza a biblioteca 'arxiv' com paginação controlada e rate-limiting (delay_seconds=1).
- Implementa falha rápida (num_retries=1, max_outer_attempts=1) para evitar travamento em caso de erro 429 da API do ArXiv.
- Incorpora fallback local gerado dinamicamente com base nas palavras-chave do escopo do projeto.
- Deduplica artigos com base no 'arxiv_id' mais recente (campo 'updated') usando Pandas.
- Filtra abstracts e títulos inválidos ou curtos antes de salvar em 'corpus.jsonl'.
\"\"\"

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import arxiv
import pandas as pd
from tqdm import tqdm

FALLBACK_PAPERS = {{FALLBACK_PAPERS}}

def build_query(keywords, categories):
    \"\"\"Monta a string de query no formato esperado pela API do ArXiv.\"\"\"
    kw_part = " OR ".join([f'all:\"{k}\"' for k in keywords]) if keywords else ""
    cat_part = " OR ".join([f"cat:{c}" for c in categories]) if categories else ""
    parts = [p for p in [f"({kw_part})" if kw_part else "",
                          f"({cat_part})" if cat_part else ""] if p]
    return " AND ".join(parts) if parts else "all:*"

def already_collected_ids(path: Path) -> set:
    \"\"\"Lê o arquivo .jsonl (se existir) e retorna os IDs já salvos.\"\"\"
    if not path.exists():
        return set()
    ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                ids.add(json.loads(line)["arxiv_id"])
            except Exception:
                continue
    return ids

def collect_arxiv(query, target_size, page_size, year_from, year_to,
                  out_path: Path, max_outer_attempts: int = 1,
                  initial_backoff_seconds: int = 1):
    \"\"\"Coleta artigos do ArXiv, salvando incrementalmente em JSONL.\"\"\"
    client = arxiv.Client(page_size=page_size, delay_seconds=1, num_retries=1)
    seen = already_collected_ids(out_path)
    print(f"[*] IDs já coletados anteriormente: {len(seen)}")

    offset = 0
    outer_attempt = 0

    while len(seen) < target_size and outer_attempt < max_outer_attempts:
        try:
            search = arxiv.Search(
                query=query,
                max_results=target_size * 2,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )

            print(f"[*] Iniciando/retomando busca com offset={offset} (alvo={target_size}, acumulado={len(seen)})...")
            
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(out_path, "a", encoding="utf-8") as f:
                results_generator = client.results(search, offset=offset)
                pbar = tqdm(initial=len(seen), total=target_size, desc="coletando")
                
                for result in results_generator:
                    offset += 1
                    year = result.published.year if result.published else None
                    if year_from is not None and (year is None or year < year_from):
                        continue
                    if year_to is not None and (year is None or year > year_to):
                        continue

                    arxiv_id = result.get_short_id().split("v")[0]
                    if arxiv_id in seen:
                        continue

                    record = {
                        "arxiv_id": arxiv_id,
                        "title": (result.title or "").strip(),
                        "abstract": (result.summary or "").strip().replace("\\n", " "),
                        "authors": [a.name for a in result.authors],
                        "categories": list(result.categories or []),
                        "primary_category": result.primary_category,
                        "published": result.published.isoformat() if result.published else None,
                        "updated": result.updated.isoformat() if result.updated else None,
                        "doi": result.doi,
                        "pdf_url": result.pdf_url,
                        "entry_id": result.entry_id,
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\\n")
                    f.flush()
                    seen.add(arxiv_id)
                    pbar.update(1)
                    pbar.set_postfix(offset=offset)

                    if len(seen) >= target_size:
                        break
                pbar.close()
            break
        except Exception as e:
            outer_attempt += 1
            print(f"\\n[Aviso] Tentativa {outer_attempt}/{max_outer_attempts} falhou de forma rápida: {type(e).__name__}: {e}")

    print(f"[*] Coleta finalizada. Total bruto acumulado em {out_path}: {len(seen)} artigos.")
    return len(seen)

def write_fallback_data(out_path: Path):
    \"\"\"Escreve os artigos de fallback no arquivo jsonl.\"\"\"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen = already_collected_ids(out_path)
    with open(out_path, "a", encoding="utf-8") as f:
        for paper in FALLBACK_PAPERS:
            if paper["arxiv_id"] not in seen:
                f.write(json.dumps(paper, ensure_ascii=False) + "\\n")
                seen.add(paper["arxiv_id"])

def clean_and_deduplicate(raw_path: Path, corpus_path: Path):
    \"\"\"Lê o arquivo jsonl bruto, deduplica por ID e filtra campos vazios.\"\"\"
    if not raw_path.exists():
        print(f"[-] Erro: Arquivo bruto {raw_path} não existe.")
        return 0

    print(f"[*] Limpando e normalizando corpus...")
    raw_records = []
    with open(raw_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                raw_records.append(json.loads(line))
            except Exception:
                continue

    if not raw_records:
        print("[-] Nenhum registro bruto encontrado.")
        return 0

    df = pd.DataFrame(raw_records)
    df["updated_dt"] = pd.to_datetime(df["updated"], errors="coerce")
    df = df.sort_values("updated_dt").drop_duplicates("arxiv_id", keep="last")

    df = df[df["title"].str.len() > 0]
    df = df[df["abstract"].str.len() > 50]

    cols = ["arxiv_id", "title", "abstract", "authors", "categories",
            "primary_category", "published", "doi", "pdf_url"]
    
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(corpus_path, "w", encoding="utf-8") as f:
        for _, row in df[cols].iterrows():
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\\n")

    print(f"[*] Corpus limpo e normalizado salvo em: {corpus_path} ({len(df)} documentos).")
    return len(df)

def main():
    parser = argparse.ArgumentParser(description="Coletor ArXiv do Pipeline RAG.")
    parser.add_argument("--keywords", nargs="+", default={{KEYWORDS}},
                        help="Palavras-chave a buscar.")
    parser.add_argument("--categories", nargs="+", default={{CATEGORIES}},
                        help="Categorias do arXiv a filtrar.")
    parser.add_argument("--year_from", type=int, default={{YEAR_FROM}}, help="Ano inicial.")
    parser.add_argument("--year_to", type=int, default={{YEAR_TO}}, help="Ano final.")
    parser.add_argument("--target_size", type=int, default={{TARGET_SIZE}}, help="Quantidade alvo de artigos.")
    parser.add_argument("--page_size", type=int, default={{PAGE_SIZE}}, help="Tamanho da página da API.")
    parser.add_argument("--raw_path", type=str, default="data/raw/arxiv_raw.jsonl", help="Caminho do arquivo bruto.")
    parser.add_argument("--corpus_path", type=str, default="data/processed/corpus.jsonl", help="Caminho do corpus limpo.")

    args = parser.parse_args()

    raw_path = Path(args.raw_path)
    corpus_path = Path(args.corpus_path)
    query = build_query(args.keywords, args.categories)
    print(f"[*] Query montada: {query}")

    try:
        collected = collect_arxiv(
            query=query,
            target_size=args.target_size,
            page_size=args.page_size,
            year_from=args.year_from,
            year_to=args.year_to,
            out_path=raw_path
        )
    except Exception as e:
        print(f"\\n[Aviso] Falha na chamada da API do ArXiv: {e}")
        collected = 0

    if collected < 2:
        print("\\n[Aviso] Coleta online insuficiente (provável bloqueio de API ou falta de conectividade).")
        print("[Aviso] Populando dados locais offline/mock de backup de doutorado...")
        write_fallback_data(raw_path)

    clean_and_deduplicate(raw_path, corpus_path)

if __name__ == "__main__":
    main()
"""

PREPROCESS_TEMPLATE = """# -*- coding: utf-8 -*-
\"\"\"
Módulo de Pré-processamento e Divisão em Chunks de Artigos do Corpus.
Autor: {{AUTHOR}}

Decisões de Implementação do Pré-processador:
- Lê o arquivo 'corpus.jsonl' linha a linha (reduzindo pegada de memória).
- Divide o resumo do artigo utilizando expressões regulares para isolamento de sentenças.
- Limpa o texto das sentenças (lowercase e remoção de espaços em excesso).
- Preserva metadados essenciais (autores, ID, ano de publicação) em cada chunk para garantir citação correta e cálculo de métricas.
\"\"\"

import json
import os
import re

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\\s+', ' ', text)
    return text.strip()

def main():
    input_path = os.path.join("data/processed", "corpus.jsonl")
    output_path = os.path.join("data/processed", "chunks.json")
    
    if not os.path.exists(input_path):
        print(f"[Preprocess] Erro: Arquivo {input_path} não encontrado. Execute a etapa de coleta primeiro.")
        return
        
    chunks = []
    print(f"[Preprocess] Carregando corpus de {input_path}...")
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            paper = json.loads(line)
            text = paper["abstract"]
            arxiv_id = paper["arxiv_id"]
            title = paper["title"]
            authors = paper["authors"]
            published = paper.get("published", "")
            
            # Dividir em sentenças usando expressões regulares
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\\s+', text) if len(s.strip()) > 10]
            
            for i, sentence in enumerate(sentences):
                cleaned = clean_text(sentence)
                chunks.append({
                    "chunk_id": f"{arxiv_id}_c{i:03d}",
                    "paper_id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "published": published,
                    "text": sentence,
                    "text_cleaned": cleaned,
                    "categories": paper.get("categories", [])
                })
                
    os.makedirs("data/processed", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=4, ensure_ascii=False)
        
    print(f"[Preprocess] Sucesso! Gerados {len(chunks)} chunks e salvos em: {output_path}")

if __name__ == "__main__":
    main()
"""

BM25_TEMPLATE = """# -*- coding: utf-8 -*-
\"\"\"
Retriever Léxico usando BM25 para Artigos Científicos.
Autor: {{AUTHOR}}

Decisões de Implementação do BM25:
- Utiliza 'rank_bm25' (Okapi BM25) para construir pontuações lexicais.
- Realiza a tokenização básica do corpus dividindo por espaços e aplicando lowercase.
- Serializa a instância em 'runs/bm25_index.pkl' para uso posterior.
\"\"\"

import argparse
import json
import os
import pickle
import sys
from rank_bm25 import BM25Okapi

def tokenize(text):
    return text.lower().split()

class BM25Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.corpus = [tokenize(c["text_cleaned"]) for c in chunks]
        self.model = BM25Okapi(self.corpus)

    def search(self, query, top_k=3):
        tokenized_query = tokenize(query)
        scores = self.model.get_scores(tokenized_query)
        
        ranked_results = sorted(
            zip(self.chunks, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        results = []
        for chunk, score in ranked_results[:top_k]:
            results.append({
                "chunk": chunk,
                "score": float(score)
            })
        return results

def main():
    parser = argparse.ArgumentParser(description="Retriever BM25.")
    parser.add_argument("--query", type=str, required=True, help="Query de busca.")
    parser.add_argument("--top_k", type=int, default=3, help="Quantidade de documentos a recuperar.")
    args = parser.parse_args()

    chunks_path = os.path.join("data/processed", "chunks.json")
    if not os.path.exists(chunks_path):
        print(f"[BM25] Erro: Arquivo {chunks_path} não encontrado. Execute a etapa de preprocessamento primeiro.")
        sys.exit(1)
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    retriever = BM25Retriever(chunks)
    
    os.makedirs("runs", exist_ok=True)
    index_path = os.path.join("runs", "bm25_index.pkl")
    with open(index_path, "wb") as f:
        pickle.dump(retriever, f)
        
    print(f"[BM25] Modelo indexado e salvo em: {index_path}")
    
    results = retriever.search(args.query, top_k=args.top_k)
    
    print(f"\\n[Resultados da Busca BM25] Query: '{args.query}'")
    print("-" * 80)
    for idx, res in enumerate(results):
        chunk = res["chunk"]
        authors_str = ", ".join(chunk['authors'][:3]) if isinstance(chunk['authors'], list) else chunk['authors']
        print(f"Rank {idx+1} | Score: {res['score']:.4f}")
        print(f"Artigo: {chunk['title']} ({authors_str}, {chunk['published'][:4]})")
        print(f"Conteúdo: {chunk['text']}")
        print("-" * 80)

if __name__ == "__main__":
    main()
"""

KNN_TEMPLATE = """# -*- coding: utf-8 -*-
\"\"\"
Retriever Baseado em Vetores usando KNN e TF-IDF da scikit-learn.
Autor: {{AUTHOR}}

Decisões de Implementação do KNN:
- Utiliza a biblioteca scikit-learn ('TfidfVectorizer') para construir os vetores e 'NearestNeighbors' para o cálculo geométrico.
- A métrica de distância configurada é o cosseno ('cosine').
- Executa de maneira totalmente offline e rápida, servindo como baseline para busca vetorial densa.
\"\"\"

import argparse
import json
import os
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

class KNNRetriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.texts = [c["text_cleaned"] for c in chunks]
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.texts)
        self.knn = NearestNeighbors(n_neighbors=5, metric="cosine")
        self.knn.fit(self.tfidf_matrix)

    def search(self, query, top_k=3):
        if not self.chunks:
            return []
        query_vector = self.vectorizer.transform([query.lower()])
        distances, indices = self.knn.kneighbors(query_vector, n_neighbors=min(top_k, len(self.chunks)))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            similarity = 1.0 - float(dist)
            results.append({
                "chunk": self.chunks[idx],
                "score": similarity
            })
        return results

def main():
    parser = argparse.ArgumentParser(description="Retriever KNN base de vetores.")
    parser.add_argument("--query", type=str, required=True, help="Query de busca.")
    parser.add_argument("--top_k", type=int, default=3, help="Top K.")
    args = parser.parse_args()

    chunks_path = os.path.join("data/processed", "chunks.json")
    if not os.path.exists(chunks_path):
        print(f"[KNN] Erro: Arquivo {chunks_path} não encontrado. Execute preprocess.py primeiro.")
        sys.exit(1)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    retriever = KNNRetriever(chunks)
    results = retriever.search(args.query, top_k=args.top_k)

    print(f"\\n[Resultados da Busca KNN Vector Space] Query: '{args.query}'")
    print("-" * 80)
    for idx, res in enumerate(results):
        chunk = res["chunk"]
        authors_str = ", ".join(chunk['authors'][:3]) if isinstance(chunk['authors'], list) else chunk['authors']
        print(f"Rank {idx+1} | Similaridade Cosseno: {res['score']:.4f}")
        print(f"Artigo: {chunk['title']} ({authors_str}, {chunk['published'][:4]})")
        print(f"Conteúdo: {chunk['text']}")
        print("-" * 80)

if __name__ == "__main__":
    main()
"""

EVAL_TEMPLATE = """# -*- coding: utf-8 -*-
\"\"\"
Script de Avaliação Dinâmica do Pipeline de RAG usando silver labels léxicas.
Autor: {{AUTHOR}}

Decisões de Implementação da Avaliação:
- Calcula dinamicamente a relevância (silver labels) no corpus coletado: um documento é considerado relevante para a consulta se contiver todas as palavras da consulta.
- Computa estatísticas de avaliação de RI de nível de pós-graduação: Precision@K, Recall@K, MAP e MRR.
- Salva o relatório detalhado em 'runs/evaluation_report.json'.
\"\"\"

import json
import os
import sys

# Definimos as consultas de teste (Query Set) baseadas no domínio de pesquisa do projeto
TEST_QUERIES = {{TEST_QUERIES}}

def main():
    chunks_path = os.path.join("data/processed", "chunks.json")
    if not os.path.exists(chunks_path):
        print("[Eval] Erro: Chunks processados não encontrados. Execute o pipeline primeiro.")
        sys.exit(1)
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    if not chunks:
        print("[Eval] Erro: Nenhum chunk disponível para avaliação.")
        sys.exit(1)

    sys.path.append(os.getcwd())
    try:
        from src.models.bm25_retriever import BM25Retriever
        retriever = BM25Retriever(chunks)
    except ImportError as e:
        print(f"[Eval] Erro ao importar BM25Retriever: {e}")
        sys.exit(1)

    print("[Eval] Executando avaliação dinâmica de Recuperação de Informação...")
    
    top_k = 3
    results = {}
    
    reciprocal_ranks = []
    average_precisions = []
    precisions_at_k = []
    recalls_at_k = []

    for query in TEST_QUERIES:
        query_words = query.lower().split()
        relevant_ids = set()
        for c in chunks:
            text_to_check = (c["title"] + " " + c["text_cleaned"]).lower()
            if all(w in text_to_check for w in query_words):
                relevant_ids.add(c["paper_id"])

        if not relevant_ids:
            continue

        retrieved = retriever.search(query, top_k=top_k)
        retrieved_ids = [res["chunk"]["paper_id"] for res in retrieved]
        
        unique_retrieved = []
        for r_id in retrieved_ids:
            if r_id not in unique_retrieved:
                unique_retrieved.append(r_id)
                
        hits = [r_id for r_id in unique_retrieved if r_id in relevant_ids]
        precision = len(hits) / top_k
        recall = len(hits) / len(relevant_ids)
        
        precisions_at_k.append(precision)
        recalls_at_k.append(recall)
        
        rr = 0.0
        for rank, r_id in enumerate(unique_retrieved):
            if r_id in relevant_ids:
                rr = 1.0 / (rank + 1)
                break
        reciprocal_ranks.append(rr)
        
        ap = 0.0
        num_hits = 0
        for rank, r_id in enumerate(unique_retrieved):
            if r_id in relevant_ids:
                num_hits += 1
                ap += num_hits / (rank + 1)
        ap /= len(relevant_ids)
        average_precisions.append(ap)
        
        results[query] = {
            "retrieved_ids": unique_retrieved,
            "relevant_ids": list(relevant_ids),
            "Precision@K": precision,
            "Recall@K": recall,
            "AP": ap,
            "RR": rr
        }

    if not average_precisions:
        print("[Eval] Aviso: Nenhuma consulta encontrou documentos relevantes. Aumente o target_size da coleta.")
        mAP, mRR, mean_precision, mean_recall = 0.0, 0.0, 0.0, 0.0
    else:
        mAP = sum(average_precisions) / len(average_precisions)
        mRR = sum(reciprocal_ranks) / len(reciprocal_ranks)
        mean_precision = sum(precisions_at_k) / len(precisions_at_k)
        mean_recall = sum(recalls_at_k) / len(recalls_at_k)

    print("\\n" + "="*50)
    print("RELATÓRIO DE AVALIAÇÃO DE RECUPERAÇÃO DE INFORMAÇÃO (DYN)")
    print("="*50)
    print(f"Média Precision@{top_k}: {mean_precision:.4f}")
    print(f"Média Recall@{top_k}:    {mean_recall:.4f}")
    print(f"MAP (Mean Average Precision): {mAP:.4f}")
    print(f"MRR (Mean Reciprocal Rank):    {mRR:.4f}")
    print("="*50)
    
    os.makedirs("runs", exist_ok=True)
    report_path = os.path.join("runs", "evaluation_report.json")
    report = {
        "metrics": {
            "mean_precision_at_k": mean_precision,
            "mean_recall_at_k": mean_recall,
            "mAP": mAP,
            "mRR": mRR
        },
        "queries": results
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
        
    print(f"[Eval] Relatório de avaliação salvo em: {report_path}")

if __name__ == "__main__":
    main()
"""

RERANKER_TEMPLATE = """# -*- coding: utf-8 -*-
\"\"\"
Módulo M1 - Reranker Semântico usando SentenceTransformers CrossEncoder (Simulado/Stub).
Autor: {{AUTHOR}}
\"\"\"

import argparse
import json
import os
import sys

class CrossEncoderReranker:
    def __init__(self):
        print("[Reranker] Inicializando Reranker Cross-Encoder...")

    def rerank(self, query, candidates):
        scored_candidates = []
        query_words = set(query.lower().split())
        
        for item in candidates:
            chunk = item if "chunk" not in item else item["chunk"]
            text_words = set(chunk["text_cleaned"].split())
            
            intersection = query_words.intersection(text_words)
            jaccard = len(intersection) / len(query_words.union(text_words)) if len(query_words.union(text_words)) > 0 else 0
            
            keyword_bonus = 0.0
            if any(w in query.lower() for w in ["pruning", "compression", "quantization", "fraud", "anomaly"]):
                keyword_bonus += 0.2
            
            final_score = float(jaccard + keyword_bonus)
            scored_candidates.append({
                "chunk": chunk,
                "score": final_score
            })
            
        return sorted(scored_candidates, key=lambda x: x["score"], reverse=True)

def main():
    parser = argparse.ArgumentParser(description="Reranker M1.")
    parser.add_argument("--query", type=str, required=True, help="Query de busca.")
    args = parser.parse_args()

    print(f"[Reranker] Executando Re-ranker M1 para a query: '{args.query}'")
    chunks_path = os.path.join("data/processed", "chunks.json")
    if not os.path.exists(chunks_path):
        print("[Reranker] Erro: Execute coleta.py e preprocess.py primeiro.")
        sys.exit(1)
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    candidates = [{"chunk": c} for c in chunks[:5]]
    
    reranker = CrossEncoderReranker()
    reranked = reranker.rerank(args.query, candidates)
    
    print("\\n[Resultados do Re-Ranking M1]")
    print("-" * 80)
    for idx, item in enumerate(reranked):
        chunk = item["chunk"]
        print(f"Rerank {idx+1} | Score Semântico: {item['score']:.4f}")
        print(f"Artigo: {chunk['title']}")
        print(f"Texto: {chunk['text']}")
        print("-" * 80)

if __name__ == "__main__":
    main()
"""

HYBRID_TEMPLATE = """# -*- coding: utf-8 -*-
\"\"\"
Módulo M5 - Retriever Híbrido combinando busca Lexical (BM25) e busca Semântica via Reciprocal Rank Fusion (RRF).
Autor: {{AUTHOR}}
\"\"\"

import argparse
import json
import os
import sys

sys.path.append(os.getcwd())
try:
    from src.models.bm25_retriever import BM25Retriever
    from src.models.knn_retriever import KNNRetriever
except ImportError as e:
    print(f"[Hybrid] Erro de importação: {e}")
    sys.exit(1)

class HybridRetriever:
    def __init__(self, chunks):
        self.bm25 = BM25Retriever(chunks)
        self.knn = KNNRetriever(chunks)
        
    def search(self, query, top_k=3, k_rrf=60):
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        knn_results = self.knn.search(query, top_k=top_k * 2)
        
        rrf_scores = {}
        
        for rank, res in enumerate(bm25_results):
            chunk_id = res["chunk"]["chunk_id"]
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {"chunk": res["chunk"], "score": 0.0}
            rrf_scores[chunk_id]["score"] += 1.0 / (k_rrf + rank + 1)
            
        for rank, res in enumerate(knn_results):
            chunk_id = res["chunk"]["chunk_id"]
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {"chunk": res["chunk"], "score": 0.0}
            rrf_scores[chunk_id]["score"] += 1.0 / (k_rrf + rank + 1)
            
        sorted_results = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results[:top_k]

def main():
    parser = argparse.ArgumentParser(description="Retriever Híbrido M5 (BM25 + Dense KNN com RRF).")
    parser.add_argument("--query", type=str, required=True, help="Query de busca.")
    parser.add_argument("--top_k", type=int, default=3, help="Top K.")
    args = parser.parse_args()

    chunks_path = os.path.join("data/processed", "chunks.json")
    if not os.path.exists(chunks_path):
        print("[Hybrid] Erro: Execute a etapa de preprocessamento primeiro.")
        sys.exit(1)
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    hybrid_retriever = HybridRetriever(chunks)
    results = hybrid_retriever.search(args.query, top_k=args.top_k)
    
    print(f"\\n[Resultados da Busca Híbrida M5] Query: '{args.query}'")
    print("=" * 80)
    for idx, res in enumerate(results):
        chunk = res["chunk"]
        authors_str = ", ".join(chunk['authors'][:3]) if isinstance(chunk['authors'], list) else chunk['authors']
        print(f"Rank {idx+1} | Score RRF: {res['score']:.6f}")
        print(f"Artigo: {chunk['title']} ({authors_str}, {chunk['published'][:4]})")
        print(f"Trecho: {chunk['text']}")
        print("=" * 80)

if __name__ == "__main__":
    main()
"""

README_TEMPLATE = """# Pipeline de Recuperação de Informação (RAG) - Busca Temática

Este projeto foi gerado automaticamente pela ferramenta de scaffolding `rag-setup`. Ele fornece uma infraestrutura funcional para coleta via API do ArXiv, pré-processamento, indexação, recuperação e avaliação estatística.

**Autor:** {{AUTHOR}}

---

## Estrutura de Diretórios Gerada

```
├── data/
│   ├── raw/             # Artigos brutos coletados em formato JSONL (arxiv_raw.jsonl)
│   └── processed/       # Corpus limpo (corpus.jsonl) e chunks para RAG (chunks.json)
├── notebooks/           # Notebooks Jupyter para análise exploratória
├── src/
│   ├── models/          # Mecanismos de busca (BM25, KNN, Reranker, Híbrido)
│   └── utils/           # Módulos de Coleta (ArXiv) e Pré-processamento (Chunking)
├── runs/                # Índices e relatórios de avaliação
├── eval/                # Avaliação de métricas clássicas de IR (Precision@K, Recall@K, MAP, MRR)
├── manage.py            # Orquestrador da CLI do pipeline
└── README.md
```

## Como Usar

Instale as dependências:
```bash
pip install arxiv rank_bm25 scikit-learn sentence-transformers pandas numpy tqdm
```

Execute o pipeline completo (Coleta, Processamento, Busca Teste e Avaliação):
```bash
python manage.py run-all
```

Ou execute comandos isolados:
```bash
# Coleta customizada
python manage.py coletar --keywords "attention pruning" "layer dropping" --target_size 20

# Pré-processamento
python manage.py processar

# Recuperação de documentos
python manage.py buscar --modelo bm25 --query "structural compression of LLMs" --top_k 3

# Avaliação
python manage.py avaliar
```
"""

# ==============================================================================
# LOGICA DE SUPORTE A ESCOPO AGNOSTICO
# ==============================================================================

def load_scope_file(filepath):
    """Lê um arquivo de escopo Python e extrai as variáveis globais de configuração."""
    scope = {}
    if not filepath or not os.path.exists(filepath):
        return scope
    try:
        from pathlib import Path
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        local_vars = {}
        # Executar no namespace com Path disponível
        exec(code, {"Path": Path}, local_vars)
        for var in ["KEYWORDS", "CATEGORIES", "YEAR_FROM", "YEAR_TO", "TARGET_SIZE", "PAGE_SIZE"]:
            if var in local_vars:
                scope[var] = local_vars[var]
    except Exception as e:
        print(f"[Aviso] Falha ao ler o arquivo de escopo '{filepath}': {e}")
    return scope

def generate_fallback_papers(keywords, categories, year_from, year_to):
    """Gera uma lista de mock papers dinâmica com base nas keywords e categorias fornecidas."""
    papers = []
    start_year = year_from if year_from is not None else 2018
    end_year = year_to if year_to is not None else 2026
    if start_year > end_year:
        start_year, end_year = end_year, start_year

    for i in range(5):
        idx1 = i % len(keywords)
        idx2 = (i + 1) % len(keywords)
        kw1 = keywords[idx1]
        kw2 = keywords[idx2]
        kw_combo = f"{kw1} and {kw2}" if kw1 != kw2 else kw1
        
        year = start_year + (i % (end_year - start_year + 1)) if end_year >= start_year else start_year
        
        papers.append({
            "arxiv_id": f"mock_paper_{i+1:03d}",
            "title": f"A Novel Approach to {kw_combo.title()} in Academic Contexts",
            "abstract": f"This research presents a comprehensive analysis of {kw_combo}. We develop innovative methods and framework concepts specifically designed to address challenges in modern literature. Our empirical validation across categories like {', '.join(categories)} shows significant improvements and contributions.",
            "authors": [f"Author A. Surname_{i+1}", f"Author B. Surname_{i+1}"],
            "categories": categories,
            "primary_category": categories[0] if categories else "cs.CL",
            "published": f"{year}-05-19T18:00:00Z",
            "doi": None,
            "pdf_url": f"https://arxiv.org/pdf/mock_paper_{i+1}.pdf",
            "updated": f"{year}-05-19T18:00:00Z"
        })
    return papers

# ==============================================================================
# LOGICA PRINCIPAL DO SCAFFOLDING
# ==============================================================================

def create_project_structure(project_name):
    """Cria a estrutura de diretórios do projeto."""
    dirs = [
        "data/raw",
        "data/processed",
        "notebooks",
        "src/models",
        "src/utils",
        "runs",
        "eval",
    ]
    for d in dirs:
        os.makedirs(os.path.join(project_name, d), exist_ok=True)

def write_file(project_name, relative_path, content, author, make_executable=False):
    """Grava um arquivo injetando metadados."""
    full_path = os.path.join(project_name, relative_path)
    processed_content = content.replace("{{AUTHOR}}", author)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(processed_content)
        
    if make_executable:
        st = os.stat(full_path)
        os.chmod(full_path, st.st_mode | stat.S_IEXEC)

def main():
    parser = argparse.ArgumentParser(description="CLI para scaffolding de projetos RAG agnósticos com ArXiv.")
    parser.add_argument("project_name", help="Nome da pasta do projeto a ser criado.")
    parser.add_argument("--autor", default="Jean Marcel Peres Martins (FACOM/UFMS)", help="Nome do autor a injetar nos templates.")
    parser.add_argument("--modulos", action="store_true", help="Adiciona suporte para submódulos extras (m1_reranker e m5_hybrid).")
    parser.add_argument("--escopo", help="Caminho para o arquivo python de definição de escopo (ex: escopo.py).")
    
    # Argumentos diretos para definição de escopo via CLI
    parser.add_argument("--keywords", nargs="+", help="Palavras-chave a buscar.")
    parser.add_argument("--categories", nargs="+", help="Categorias do arXiv.")
    parser.add_argument("--year_from", type=int, help="Ano inicial.")
    parser.add_argument("--year_to", type=int, help="Ano final.")
    parser.add_argument("--target_size", type=int, help="Quantidade alvo de artigos.")
    parser.add_argument("--page_size", type=int, help="Tamanho da página da API.")
    
    args = parser.parse_args()
    
    project_name = args.project_name
    author = args.autor
    extra = args.modulos
    
    # 1. Definir os valores padrão (LLM Pruning como tema padrão)
    scope = {
        "KEYWORDS": ["structural pruning", "structural compression", "llm pruning"],
        "CATEGORIES": ["cs.CL", "cs.LG", "cs.AI"],
        "YEAR_FROM": 2018,
        "YEAR_TO": 2026,
        "TARGET_SIZE": 15,
        "PAGE_SIZE": 15
    }

    # 2. Carregar do arquivo de escopo se ele existir
    escopo_file = args.escopo if args.escopo else "escopo.py"
    if os.path.exists(escopo_file):
        print(f"[*] Carregando escopo do arquivo '{escopo_file}'...")
        file_scope = load_scope_file(escopo_file)
        scope.update(file_scope)
    else:
        if args.escopo:
            print(f"[Erro] Arquivo de escopo '{args.escopo}' não foi encontrado.")
            sys.exit(1)

    # 3. Aplicar overrides dos argumentos CLI diretos se fornecidos
    if args.keywords is not None:
        scope["KEYWORDS"] = args.keywords
    if args.categories is not None:
        scope["CATEGORIES"] = args.categories
    if args.year_from is not None:
        scope["YEAR_FROM"] = args.year_from
    if args.year_to is not None:
        scope["YEAR_TO"] = args.year_to
    if args.target_size is not None:
        scope["TARGET_SIZE"] = args.target_size
    if args.page_size is not None:
        scope["PAGE_SIZE"] = args.page_size

    print(f"[*] Escopo do RAG resolvido com sucesso:")
    print(f" - Palavras-chave: {scope['KEYWORDS']}")
    print(f" - Categorias:    {scope['CATEGORIES']}")
    print(f" - Anos:          {scope['YEAR_FROM']} -> {scope['YEAR_TO']}")
    print(f" - Meta Coleta:   {scope['TARGET_SIZE']} artigos (página de tamanho {scope['PAGE_SIZE']})")

    # 4. Criar diretórios do projeto
    create_project_structure(project_name)

    # 5. Escrever manage.py customizado com defaults injetados
    additional_models = ', "hybrid"' if extra else ""
    default_query = " OR ".join(scope["KEYWORDS"])
    test_query = scope["KEYWORDS"][0] if scope["KEYWORDS"] else "test query"
    
    manage_py_processed = MANAGE_TEMPLATE.replace("{{AUTHOR}}", author)
    manage_py_processed = manage_py_processed.replace("{{ADDITIONAL_MODELS}}", additional_models)
    manage_py_processed = manage_py_processed.replace("{{DEFAULT_KEYWORDS}}", repr(scope["KEYWORDS"]))
    manage_py_processed = manage_py_processed.replace("{{DEFAULT_CATEGORIES}}", repr(scope["CATEGORIES"]))
    manage_py_processed = manage_py_processed.replace("{{DEFAULT_YEAR_FROM}}", repr(scope["YEAR_FROM"]))
    manage_py_processed = manage_py_processed.replace("{{DEFAULT_YEAR_TO}}", repr(scope["YEAR_TO"]))
    manage_py_processed = manage_py_processed.replace("{{DEFAULT_TARGET_SIZE}}", repr(scope["TARGET_SIZE"]))
    manage_py_processed = manage_py_processed.replace("{{DEFAULT_QUERY}}", default_query)
    manage_py_processed = manage_py_processed.replace("{{TEST_QUERY}}", test_query)
    write_file(project_name, "manage.py", manage_py_processed, author, make_executable=True)

    # 6. Gerar dados de backup/fallback locais baseados nas keywords do usuário
    fallback_papers = generate_fallback_papers(scope["KEYWORDS"], scope["CATEGORIES"], scope["YEAR_FROM"], scope["YEAR_TO"])

    # 7. Escrever coleta.py customizado
    coleta_processed = COLETA_TEMPLATE.replace("{{AUTHOR}}", author)
    coleta_processed = coleta_processed.replace("{{KEYWORDS}}", repr(scope["KEYWORDS"]))
    coleta_processed = coleta_processed.replace("{{CATEGORIES}}", repr(scope["CATEGORIES"]))
    coleta_processed = coleta_processed.replace("{{YEAR_FROM}}", repr(scope["YEAR_FROM"]))
    coleta_processed = coleta_processed.replace("{{YEAR_TO}}", repr(scope["YEAR_TO"]))
    coleta_processed = coleta_processed.replace("{{TARGET_SIZE}}", repr(scope["TARGET_SIZE"]))
    coleta_processed = coleta_processed.replace("{{PAGE_SIZE}}", repr(scope["PAGE_SIZE"]))
    coleta_processed = coleta_processed.replace("{{FALLBACK_PAPERS}}", repr(fallback_papers))
    write_file(project_name, "src/utils/coleta.py", coleta_processed, author)

    # 8. Escrever preprocess.py
    write_file(project_name, "src/utils/preprocess.py", PREPROCESS_TEMPLATE, author)

    # 9. Escrever retrievers e avaliação dinâmica
    write_file(project_name, "src/models/bm25_retriever.py", BM25_TEMPLATE, author)
    write_file(project_name, "src/models/knn_retriever.py", KNN_TEMPLATE, author)
    
    eval_processed = EVAL_TEMPLATE.replace("{{AUTHOR}}", author)
    eval_processed = eval_processed.replace("{{TEST_QUERIES}}", repr(scope["KEYWORDS"]))
    write_file(project_name, "eval/evaluate.py", eval_processed, author)

    # 10. Escrever stubs extras caso solicitado
    if extra:
        write_file(project_name, "src/models/m1_reranker.py", RERANKER_TEMPLATE, author)
        write_file(project_name, "src/models/m5_hybrid.py", HYBRID_TEMPLATE, author)
        print("[*] Módulos extras (m1_reranker, m5_hybrid) configurados com sucesso!")

    # 11. Escrever README.md
    write_file(project_name, "README.md", README_TEMPLATE, author)

    print("="*60)
    print(f"SUCESSO: O projeto '{project_name}' foi estruturado e configurado!")
    print(f"Para executar o pipeline completo com dados do ArXiv, acesse e rode:")
    print(f"  cd {project_name}")
    print(f"  python manage.py run-all")
    print("="*60)

if __name__ == "__main__":
    main()
