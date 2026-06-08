import sys
from pathlib import Path

# Adiciona o diretório src ao sys.path para garantir importações corretas
sys.path.append(str(Path(__file__).parent))

from common.config import CORPUS_PATH, QUERIES_PATH, QRELS_PATH
from collection.collector import run_collection
from retrieval.bm25 import run_bm25
from retrieval.knn import run_knn
from modules.hybrid import run_hybrid
from modules.reranker import run_reranker

def main():
    """
    Orquestra a execução de todo o pipeline de recuperação de informação.
    """
    print("--- Iniciando Pipeline de Recuperação de Artigos ---")

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

    # 3. Instruções Finais
    print("\n--- Todos os pipelines foram executados e os arquivos de run foram gerados em data/runs/ ---")
    print("\nPróximos Passos:")
    print(f"1. Anote a relevância dos documentos para cada query no arquivo `{QRELS_PATH.name}`.")
    print(f"   - Para cada query em `{QUERIES_PATH.name}`, julgue os documentos retornados nos arquivos de run.")
    print("   - Use o formato: qid <TAB> 0 <TAB> doc_id <TAB> relevância (0, 1 ou 2).")
    print(f"   - Um exemplo de `qrels.tsv` pode ser encontrado em `{QRELS_PATH}` (com placeholders).")
    print("\n2. Execute o script de avaliação para calcular as métricas:")
    print("   python src/evaluation/evaluate.py")
    print("\n--- Pipeline Concluído ---")


if __name__ == "__main__":
    main()
