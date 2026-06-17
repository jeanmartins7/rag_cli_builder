import sys
import argparse
from pathlib import Path

# Adiciona o diretório src ao sys.path para garantir importações corretas
sys.path.append(str(Path(__file__).parent))

from common.config import CORPUS_PATH, QUERIES_PATH, QRELS_PATH, RUNS_DIR
from collection.collector import run_collection
from retrieval.bm25 import run_bm25
from retrieval.knn import run_knn
from modules.hybrid import run_hybrid
from modules.reranker import run_reranker
from evaluation.evaluate import evaluate_runs, read_qrels, read_run

def run_pipeline():
    """
    Executa a coleta de dados e a geração de runs para todos os modelos.
    """
    print("--- Iniciando a execução dos modelos de recuperação ---")

    # 1. Coleta de Dados
    if not CORPUS_PATH.exists():
        print(f"Corpus não encontrado em {CORPUS_PATH}.")
        print("Executando a coleta de dados do ArXiv. Isso pode levar alguns minutos...")
        run_collection()
    else:
        print(f"Corpus encontrado em {CORPUS_PATH}. Pulando a etapa de coleta.")

    # 2. Geração de Runs dos Modelos
    run_bm25()
    run_knn()
    run_hybrid()
    run_reranker()

    print("\n--- Todos os pipelines foram executados e os arquivos de run foram gerados em data/runs/ ---")

def generate_qrels():
    """
    Gera um arquivo qrels.tsv a partir do resultado do reranker.
    """
    print(f"--- Gerando arquivo de qrels em {QRELS_PATH} ---")
    reranked_run_path = RUNS_DIR / "reranked.trec"
    if not reranked_run_path.exists():
        print(f"Arquivo {reranked_run_path} não encontrado. Execute o comando 'run' primeiro.")
        sys.exit(1)

    run = read_run(reranked_run_path)
    
    with open(QRELS_PATH, "w", encoding="utf-8") as f:
        f.write("# Formato TREC: qid iter docid rel\n")
        f.write("# Relevância: 0 (Não Relevante), 1 (Relevante), 2 (Altamente Relevante)\n")
        f.write("# Gerado automaticamente a partir do top-10 de reranked.trec\n")
        for qid, docs in run.items():
            for i, (_, _, docid) in enumerate(docs[:10]):
                f.write(f"{qid}\t0\t{docid}\t1\n")
    print(f"Arquivo {QRELS_PATH} gerado com sucesso.")


def run_evaluation():
    """
    Executa o script de avaliação.
    """
    print("--- Executando a avaliação dos modelos ---")
    if not QRELS_PATH.exists():
        print(f"Arquivo {QRELS_PATH} não encontrado. Execute o comando 'generate-qrels' primeiro.")
        sys.exit(1)

    qrels = read_qrels(QRELS_PATH)
    if not qrels:
        print(f"qrels em {QRELS_PATH} está vazio.", file=sys.stderr)
        sys.exit(1)

    runs_to_evaluate = sorted(list(RUNS_DIR.glob("*.trec")))
    if not runs_to_evaluate:
        print(f"Nenhum arquivo .trec encontrado em {RUNS_DIR}", file=sys.stderr)
        sys.exit(1)

    evaluate_runs(qrels, runs_to_evaluate, 10)
    print("\n--- Avaliação Concluída ---")


def main():
    """
    Orquestra a execução de todo o pipeline de recuperação de informação.
    """
    parser = argparse.ArgumentParser(description="Pipeline de Recuperação de Artigos.")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    subparsers.required = True

    # Comando para executar os modelos
    parser_run = subparsers.add_parser("run", help="Executa a coleta de dados e os modelos de recuperação.")
    parser_run.set_defaults(func=run_pipeline)

    # Comando para gerar o qrels
    parser_qrels = subparsers.add_parser("generate-qrels", help="Gera o arquivo qrels.tsv a partir do resultado do reranker.")
    parser_qrels.set_defaults(func=generate_qrels)

    # Comando para avaliar os modelos
    parser_eval = subparsers.add_parser("evaluate", help="Executa a avaliação dos modelos.")
    parser_eval.set_defaults(func=run_evaluation)

    args = parser.parse_args()
    args.func()

if __name__ == "__main__":
    main()