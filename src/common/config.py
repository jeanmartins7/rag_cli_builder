from pathlib import Path

# Caminho base do projeto (raiz do repositório)
# Considerando que este arquivo está em src/common/config.py
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Diretório de dados principal
DATA_DIR = PROJECT_ROOT / "data"

# Caminhos específicos dos arquivos
RAW_PATH = DATA_DIR / "arxiv_raw.jsonl"
CORPUS_PATH = DATA_DIR / "corpus.jsonl"
QUERIES_PATH = DATA_DIR / "queries.tsv"
QRELS_PATH = DATA_DIR / "qrels.tsv"

# Diretório para os arquivos de run gerados pelos modelos
RUNS_DIR = DATA_DIR / "runs"
