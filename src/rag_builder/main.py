import os
import argparse
from pathlib import Path


def setup_cli():
    parser = argparse.ArgumentParser(
        description="🚀 Construtor do Pipeline RAG - Trabalho de IA"
    )

    parser.add_argument(
        "nome_projeto",
        nargs="?",
        default="trabalho_rag",
        help="Nome da pasta raiz do projeto (padrão: trabalho_rag)"
    )

    parser.add_argument(
        "--autor",
        type=str,
        default="Aluno de Doutorado",
        help="Nome do autor para preencher o README.md"
    )

    parser.add_argument(
        "--modulos",
        action="store_true",
        help="Gera os arquivos-base para os módulos de aprofundamento (M1 a M5)"
    )

    return parser.parse_args()


def criar_estrutura(args):
    """Cria a estrutura física de arquivos e diretórios."""
    base_dir = Path(args.nome_projeto)

    diretorios = [
        "data/raw",
        "data/processed",
        "notebooks",
        "src/models",
        "src/utils",
        "runs",
        "eval"
    ]

    arquivos = {
        "README.md": f"# Pipeline RAG\n\n**Autor:** {args.autor}\n\nDescreva aqui como reproduzir seu projeto.\n",
        "requirements.txt": "rank_bm25\nscikit-learn\nsentence-transformers\npandas\nnumpy\njupyter\n",
        "LINKS.txt": "Link do Vídeo: \nLink do Repositório (se aplicável): \n",
        "CHECKLIST.md": "- [ ] Coleta concluída\n- [ ] BM25 avaliado\n- [ ] KNN avaliado\n- [ ] Módulos extras finalizados\n- [ ] Vídeo gravado\n",
        "eval/queries.tsv": "",
        "eval/qrels.tsv": "",
        "src/models/bm25_retriever.py": "# Implementação do Baseline BM25\n",
        "src/models/knn_retriever.py": "# Implementação da busca por similaridade (TF-IDF ou Densa)\n",
    }

    if args.modulos:
        arquivos.update({
            "src/models/m1_reranker.py": "# M1: Re-ranqueamento por classificação supervisionada\n",
            "src/models/m2_clustering.py": "# M2: Agrupamento dos resultados\n",
            "src/models/m3_expansion.py": "# M3: Expansão de consulta via regras de associação\n",
            "src/models/m4_optimization.py": "# M4: Otimização de hiperparâmetros\n",
            "src/models/m5_hybrid.py": "# M5: Ranking híbrido sparse+dense\n",
        })

    print(f"\n🚀 Iniciando a criação do projeto em: ./{args.nome_projeto}/\n")

    for dir_path in diretorios:
        caminho_completo = base_dir / dir_path
        caminho_completo.mkdir(parents=True, exist_ok=True)
        print(f"📁 Criado: {dir_path}/")

    # Criando arquivos
    for file_path, conteudo in arquivos.items():
        caminho_completo = base_dir / file_path
        with open(caminho_completo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        print(f"📄 Criado: {file_path}")

    print("\n✅ Setup finalizado com sucesso!")


if __name__ == "__main__":
    argumentos = setup_cli()
    criar_estrutura(argumentos)